from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source, At
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, UnionMatch, ParamMatch, ResultValue, ElementMatch
from graia.ariadne.model import Member, Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger

from starbot.utils import config
from starbot.utils.network import request
from starbot.utils.utils import get_credential

logger.info(f"加载上舰查询模块")
prefix = config.get("COMMAND_PREFIX")
_up = config.get("ONBOARD_FOR_UP")
credential = get_credential()

channel = Channel.current()


async def query_onboard_list(user_id):
    """
    异步查询指定用户是否在指定主播的守护者列表中。

    参数:
    - user_id: 要查询的用户ID。

    返回值:
    - 返回 True 表示用户在守护者列表中，返回 False 表示用户不在守护者列表中。
    """
    query_count = 1  # 初始化查询页数
    # 请求获取主播信息
    up_info = await request("GET", f"https://api.live.bilibili.com/live_user/v1/Master/info?uid={_up}",
                            credential=credential)
    # 构造请求守护者列表的URL
    url = f"https://api.live.bilibili.com/xlive/app-room/v2/guardTab/topListNew?roomid={up_info['room_id']}&page={query_count}&ruid={_up}&page_size=30&typ=0"
    # 请求守护者列表
    top_list = await request("GET", url, credential=credential)
    # 计算总页数
    title = top_list["info"]["num"]
    pages = title / 30 + 2

    # 循环查询每页守护者列表
    while query_count <= pages:
        if query_count == 1:
            # 在第一页（包括前3名守护者和后续列表）中查找用户
            for user in top_list["top3"] + top_list["list"]:
                if user_id == user["uinfo"]["uid"]:
                    return True
            query_count += 1
        else:
            # 请求后续页的守护者列表
            url = f"https://api.live.bilibili.com/xlive/app-room/v2/guardTab/topListNew?roomid={up_info['room_id']}&page={query_count}&ruid={_up}&page_size=30&typ=0"
            top_list = await request("GET", url, credential=credential)
            # 在后续页的列表中查找用户
            for user in top_list["list"]:
                if user_id == user["uinfo"]["uid"]:
                    return True
            query_count += 1

    # 如果所有页都没有找到用户，则返回 False
    return False


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(
            ElementMatch(At, optional=True),
            FullMatch(prefix),
            UnionMatch("上舰", "onboard", "舰长"),
            "uid" @ ParamMatch()
        )],
    )
)
async def onboard(app: Ariadne, source: Source, sender: Group, member: Member, uid: MessageChain = ResultValue()):
    logger.info(f"群[{sender.id}] 触发命令 : 上舰查询，需要查询的uid为 {uid} ,查询者 {member.id}")

    # 向B站API请求指定UID的用户信息
    user_info = await request("GET", f"https://api.live.bilibili.com/live_user/v1/Master/info?uid={uid}",
                              credential=credential)
    if user_info["info"]["uname"] == "":
        logger.info("查询失败，该用户可能不存在")
        await app.send_message(sender, MessageChain("查询失败，该用户可能不存在"), quote=source)
        return

    # 请求指定UID的用户徽章信息
    medalwall = await request("GET", f"https://api.live.bilibili.com/xlive/web-ucenter/user/MedalWall?target_id={uid}",
                              credential=credential)

    # 遍历徽章信息，查找与指定用户相关的徽章
    for medal in medalwall["list"]:
        if medal["medal_info"]["target_id"] == _up:
            logger.info(f'UID:{uid} 用户名：{user_info["info"]["uname"]}的徽章等级为{medal["medal_info"]["level"]}')
            await app.send_message(sender, MessageChain(
                f'UID:{uid} 用户名：{user_info["info"]["uname"]}的 {medal["medal_info"]["medal_name"]} 徽章 等级为 {medal["medal_info"]["level"]}'),
                                   quote=source)
            return

    # 若未找到徽章，记录日志并查询该用户是否处于大航海状态
    logger.info(f'没有查询到 {uid} 的徽章')
    onboard_list = await query_onboard_list(user_info["info"]["uid"])

    # 根据查询结果，发送相应的反馈信息
    if onboard_list:
        await app.send_message(sender, MessageChain(
            f'虽然没有查询到 UID:{uid} 用户名：{user_info["info"]["uname"]} 的徽章, 但该用户目前正处于大航海中'),
                               quote=source)
    else:
        await app.send_message(sender, MessageChain(
            f'没有查询到 UID:{uid} 用户名：{user_info["info"]["uname"]} 的徽章, 同时也没有查询到该用户处于大航海中'),
                               quote=source)
