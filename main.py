import datetime
import logging

import config
from lib import itchat
from lib.itchat.content import *

logger = logging.getLogger('wechat-bridge')

forward_msg_format = '''From: {sender}

Message: {message}

Send Time: {send_time}

Group: {group}

From ID: {from_id}
'''

last_file_name = ''


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_forward(msg):
    """
    Forward text messages received by account A to account B.

    If the received message is from account B, then distribute the message to the contacts of account A according to the rules.
    :param msg:
    :return:
    """
    account_b = get_account_b_user()
    if not account_b:
        return
    if msg.user.remarkName == account_b.remarkName:
        distribute_text(msg)
        return
    if msg.type != 'Text':
        itchat.send_raw_msg(msg.msgType, msg.oriContent if '' != msg.oriContent else msg.content, toUserName=account_b.userName)
        itchat.send(forward_msg_format.format(sender=msg.user.remarkName,
                                              message=msg.type,
                                              group='None',
                                              from_id=msg.user.userName,
                                              send_time=get_now()),
                    toUserName=account_b.userName)
    else:
        itchat.send(forward_msg_format.format(sender=msg.user.remarkName,
                                              message=msg.text,
                                              group='None',
                                              from_id=msg.user.userName,
                                              send_time=get_now()),
                    toUserName=account_b.userName)


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING], isGroupChat=True)
def group_text_forward(msg):
    """
    Forward group text messages received by account A to account B.
    :param msg:
    :return:
    """
    account_b = get_account_b_user()
    if not account_b:
        return
    if msg.user.remarkName == account_b.remarkName:
        return

    if msg.type != 'Text':
        itchat.send_raw_msg(msg.msgType, msg.oriContent if '' != msg.oriContent else msg.content, toUserName=account_b.userName)
        itchat.send(forward_msg_format.format(sender=msg.actualNickName,
                                              message=msg.type,
                                              group=get_group_name(msg),
                                              from_id=msg.user.userName,
                                              send_time=get_now()),
                    toUserName=account_b.userName)
    else:
        itchat.send(forward_msg_format.format(sender=msg.actualNickName,
                                              message=msg.text,
                                              group=get_group_name(msg),
                                              from_id=msg.user.userName,
                                              send_time=get_now()),
                    toUserName=account_b.userName)


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def media_forward(msg):
    """
    Forward files, including images, received by account A to account B.
    If the received message is from account B, then record the file paths for future use.
    :param msg:
    :return:
    """
    download_path = 'download/' + msg.fileName
    msg.download(download_path)
    account_b = get_account_b_user()
    if msg.user.remarkName == account_b.remarkName:
        distribute_media(msg)
        return
    itchat.send('@%s@%s' % ('img' if msg.type == 'Picture' else 'fil', download_path), account_b.userName)
    itchat.send(forward_msg_format.format(sender=msg.user.remarkName,
                                          message=msg.type,
                                          group='None',
                                          from_id=msg.user.userName,
                                          send_time=get_now()),
                toUserName=account_b.userName)


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
def group_media_forward(msg):
    """
    Forward files, including images, received by account A to account B.
    If the received message is from account B, then save the file path for future use.
    :param msg:
    :return:
    """
    download_path = 'download/' + msg.fileName
    msg.download(download_path)
    account_b = get_account_b_user()
    if msg.user.remarkName == account_b.remarkName:
        return
    itchat.send('@%s@%s' % ('img' if msg.type == 'Picture' else 'fil', download_path), account_b.userName)
    itchat.send(forward_msg_format.format(sender=msg.actualNickName,
                                          message=msg.type,
                                          group=get_group_name(msg),
                                          from_id=msg.user.userName,
                                          send_time=get_now()),
                toUserName=account_b.userName)


def distribute_text(msg):
    """
    todo
    消息以 '/' 开头指的是要执行的命令
        1. /search xxx (根据关键词搜索好友或者群聊), 返回内容有 remarkName, nickName, actualNickName, userName 等

    消息包含引用, 则需要解析引用中的内容来分发消息
        1. 引用中是图片, 则消息内容应该是 From ID, 将 last_file_name 指定的文件发送给 From ID 表示的用户
        2. 引用中没有图片, 提取引用中的 From ID, 将消息发送给 From ID 表示的用户
    :param msg:
    :return:
    """


def distribute_media(msg):
    """
    save the file path for future use
    :param msg:
    :return:
    """
    download_path = 'download/' + msg.fileName
    msg.download(download_path)
    global last_file_name
    last_file_name = download_path


def get_group_name(msg):
    group = msg.user.nickName
    if not group:
        group = ','.join(member.nickName for member in msg.user.memberList[:3]) + '...'
    return group


@itchat.msg_register(FRIENDS)
def add_friend(msg):
    """
    Automatically approve friend requests.
    :param msg:
    :return:
    """
    msg.user.verify()
    msg.user.send('Nice to meet you!')


def get_account_b_user():
    account_b_remark_name = config.account_b_remark_name
    friends = itchat.search_friends(remarkName=account_b_remark_name)
    if not friends:
        logger.error(f'{account_b_remark_name} not found in friends list')
        return None
    return friends[0]


def get_now():
    current_utc_time = datetime.datetime.utcnow()
    eastern_offset = datetime.timedelta(hours=8)
    return current_utc_time + eastern_offset


itchat.auto_login(enableCmdQR=2, hotReload=True)
itchat.run(True)
