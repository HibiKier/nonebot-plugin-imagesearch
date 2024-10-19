import random

import aiofiles
import httpx
import nonebot_plugin_localstore as store
from nonebot import get_plugin_config
from nonebot.log import logger
from nonebot_plugin_alconna import CustomNode, Image, UniMessage
from pydantic import BaseModel

TEMP_PATH = store.get_plugin_cache_dir()


API_URL_SAUCENAO = "https://saucenao.com/search.php"


class Config(BaseModel):
    isearch_proxy: str | None = None
    """系统代理"""
    isearch_max_find_image_count: int = 3
    """搜索动漫返回的最大数量"""
    isearch_api_key: str
    """Saucenao的API_KEY，通过 https://saucenao.com/user.php?page=search-api 注册获取"""


config = get_plugin_config(Config)


async def get_saucenao_image(url: str) -> str | list[str | Image]:
    """获取图片源

    参数:
        url: 图片url

    返回:
        str | list[Image | Text]: 识图数据
    """
    params = {
        "output_type": 2,
        "api_key": config.isearch_api_key,
        "testmode": 1,
        "numres": 6,
        "db": 999,
        "url": url,
    }
    proxy = None
    if config.isearch_proxy:
        proxy = {"http://": config.isearch_proxy, "https://": config.isearch_proxy}
    async with httpx.AsyncClient(proxies=proxy) as client:  # type: ignore
        res = await client.post(API_URL_SAUCENAO, params=params)
        res.raise_for_status()
        data = res.json()
    if data["header"]["status"] != 0:
        return f"Saucenao识图失败..status：{data['header']['status']}"
    data = data["results"]
    data = (
        data
        if len(data) < config.isearch_max_find_image_count
        else data[: config.isearch_max_find_image_count]
    )
    index = random.randint(0, 10000)
    file = TEMP_PATH / f"saucenao_search_{index}.jpg"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        res.raise_for_status()
        async with aiofiles.open(file, "wb") as f:
            await f.write(res.content)
    msg_list: list[Image | str] = [
        Image(path=TEMP_PATH / f"saucenao_search_{index}.jpg")
    ]
    for info in data:
        try:
            similarity = info["header"]["similarity"]
            tmp = f"相似度：{similarity}%\n"
            for x in info["data"].keys():
                if x != "ext_urls":
                    tmp += f"{x}：{info['data'][x]}\n"
            try:
                if "source" not in info["data"].keys():
                    tmp += f'source：{info["data"]["ext_urls"][0]}\n'
            except KeyError:
                tmp += f'source：{info["header"]["thumbnail"]}\n'
            msg_list.append(tmp[:-1])
        except Exception as e:
            logger.warning(
                f"识图获取图片信息发生错误 {type(e)}:{e}",
            )
    return msg_list


def custom_forward_msg(
    msg_list: list[str | Image],
    uin: str,
    name: str,
) -> list[CustomNode]:
    """生成自定义合并消息

    参数:
        msg_list: 消息列表
        uin: 发送者 QQ
        name: 自定义名称

    返回:
        list[dict]: 转发消息
    """
    mes_list = []
    for _message in msg_list:
        mes_list.append(CustomNode(uid=uin, name=name, content=UniMessage(_message)))
    return mes_list
