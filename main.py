# -*- coding: utf-8 -*-


import config
from lib import itchat
from lib.itchat.content import *
from util import get_group_name, logger

relay_type = config.relay_type


def get_relay():
    """
    根据配置获取分发器
    :return:
    """
    if relay_type == "wechat":
        from relay import WechatRelay
        return WechatRelay(itchat)
    elif relay_type == "tg":
        from relay import TgRelay
        from tg_bot import bot
        return TgRelay(bot)
    else:
        raise NotImplementedError("Relay not available for type %s" % relay_type)


relay = get_relay()


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_forward(msg):
    """
    Forward text messages received by account A to account B.

    If the received message is from account B,
    then distribute the message to the contacts of account A according to the rules.
    :param msg:
    :return:
    """
    if config.relay_type == 'wechat':
        account_b = relay.get_account_b_user()
        if not account_b:
            return
        if msg.user.remarkName == account_b.remarkName:
            relay.dispatch(msg)
            return

    relay.forward(msg, is_group=False, is_media=False)


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING], isGroupChat=True)
def group_text_forward(msg):
    """
    将账户A收到的消息转发给账户B
    :param msg:
    :return:
    """
    group_name = get_group_name(msg)
    if not (group_name in config.group_white_list or '*' in config.group_white_list):
        logger.info(f"群聊 \"{group_name}\" 不在白名单中, 群消息不转发")
        return

    relay.forward(msg, is_group=True, is_media=False)


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def media_forward(msg):
    """
    将账户A收到的媒体文件转发给账户B

    如果消息是账户B发来的，则将文件存储并返回文件路径给账户B
    :param msg:
    :return:
    """
    relay.forward(msg, is_group=False, is_media=True)


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
def group_media_forward(msg):
    """
    将账户A收到的媒体文件转发给账户B

    如果消息是账户B发来的，则将文件存储并返回文件路径给账户B
    :param msg:
    :return:
    """
    group_name = get_group_name(msg)
    if not (group_name in config.group_white_list or '*' in config.group_white_list):
        logger.info(f"群聊 \"{group_name}\" 不在白名单中, 群消息不转发")
        return

    relay.forward(msg, is_group=True, is_media=True)


@itchat.msg_register(FRIENDS)
def add_friend(msg):
    """
    Automatically approve friend requests.
    :param msg:
    :return:
    """
    msg.user.verify()
    msg.user.send('Nice to meet you!')


logger.info(f'群聊白名单: {config.group_white_list}')
if relay_type == "wechat":
    # 调试时使用
    # itchat.auto_login(enableCmdQR=2, hotReload=True)
    logger.info(f'账号B: {config.account_b_remark_name}')
    itchat.auto_login(enableCmdQR=2)
    itchat.run(True)
else:
    from tg_bot import bot
    bot.infinity_polling()