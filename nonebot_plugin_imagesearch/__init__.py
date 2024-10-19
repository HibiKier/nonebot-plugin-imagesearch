from nonebot import logger, require

require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")
require("nonebot_plugin_uninfo")

from nonebot.adapters import Bot
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot_plugin_alconna import (
    Alconna,
    Args,
    Image,
    Match,
    Reference,
    UniMessage,
    on_alconna,
)
from nonebot_plugin_uninfo import Uninfo

from .saucenao import Config, custom_forward_msg, get_saucenao_image

__plugin_meta__ = PluginMetadata(
    name="识图",
    description="以图搜图，看破本源",
    usage="""
    识别图片 [二次元图片]
    指令：
        识图 [图片]
    """.strip(),
    type="application",
    config=Config,
    homepage="https://github.com/HibiKier/nonebot-plugin-imagesearch",
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna",
    ),
    extra={"author": "HibiKier", "version": "0.1"},
)


_matcher = on_alconna(
    Alconna("识图", Args["mode?", str]["image?", Image]), block=True, priority=5
)


async def get_image_info(mod: str, url: str) -> str | list[str | Image] | None:
    if mod == "saucenao":
        return await get_saucenao_image(url)


@_matcher.handle()
async def _(mode: Match[str], image: Match[Image]):
    if mode.available:
        _matcher.set_path_arg("mode", mode.result)
    else:
        _matcher.set_path_arg("mode", "saucenao")
    if image.available:
        _matcher.set_path_arg("image", image.result)


@_matcher.got_path("image", prompt="图来！")
async def _(
    bot: Bot,
    session: Uninfo,
    mode: str,
    image: Image,
):
    if not image.url:
        await UniMessage("图片url为空...").finish()
    await UniMessage("开始处理图片...").send()
    info_list = await get_image_info(mode, image.url)
    if isinstance(info_list, str):
        await UniMessage(info_list).finish(at_sender=True)
    if not info_list:
        await UniMessage("未查询到...").finish()
    if session.basic["scope"].lower().startswith("qq") and session.group:
        forward = custom_forward_msg(
            info_list, bot.self_id, next(iter(bot.config.nickname))
        )
        await UniMessage(Reference(nodes=forward)).send()
    else:
        for info in info_list[1:]:
            await UniMessage(info).send()
    logger.info(f" 识图: {image.url}")
