import datetime
import logging

import config
from lib import itchat
from lib.itchat.content import *

logger = logging.getLogger('itchat')

forward_msg_format = '''From: {sender}

Message: {message}

Send Time: {send_time}

Group: {group}

Group ID: {group_id}
'''


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
    # if msg.user.remarkName == account_b.remarkName:
    #     # todo distribute the message
    #     return
    itchat.send(forward_msg_format.format(sender=msg.user.remarkName,
                                          message=msg.text,
                                          group='None',
                                          group_id='None',
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
    # if msg.user.remarkName == account_b.remarkName:
    #     # todo
    #     return
    itchat.send('@%s@%s' % (
        'img' if msg.type == 'Picture' else 'fil', download_path),
                account_b.userName)
    itchat.send(forward_msg_format.format(sender=msg.user.remarkName,
                                          message='[图片]',
                                          group='None',
                                          group_id='None',
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
    # if msg.user.remarkName == account_b.remarkName:
    #     # todo distribute the message
    #     return
    itchat.send(forward_msg_format.format(sender=msg.actualNickName,
                                          message=msg.text,
                                          group=msg.user.nickName,
                                          group_id=msg.user.userName,
                                          send_time=get_now()),
                toUserName=account_b.userName)


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
