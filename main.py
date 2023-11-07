import datetime
import logging
import os
import re

import config
from lib import itchat
from lib.itchat.content import *
from lib.itchat.storage import User

logger = logging.getLogger('wechat-bridge')

img_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

# 账号A 转发到 账号B 的消息格式
forward_msg_format = '''From: {sender}

Message: {message}

SendTime: {send_time}

Group: {group}

Username: {username}
'''

# 好友、群聊搜索的返回格式
friend_format = '''RemarkName: {remark_name}
NickName: {nick_name}
Type: {type}
Username: {username}
'''

# 搜索的格式
search_param_pattern = r'/search (.*)'

# 引用的格式
quote_pattern = r'「.*：([\s\S]*)」\n- - - - - - - - - - - - - - -\n([\s\S]*)'

# 用户名的格式
username_pattern = r'.*Username: (.*)'

# 文件下载路径的格式
file_path_pattern = r'download/\d{6}-\d{6}\..*'


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_forward(msg):
    """
    Forward text messages received by account A to account B.

    If the received message is from account B,
    then distribute the message to the contacts of account A according to the rules.
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
        itchat.send_raw_msg(msg.msgType,
                            msg.oriContent if '' != msg.oriContent else msg.content,
                            toUserName=account_b.userName)
        itchat.send(forward_msg_format.format(sender=get_sender(msg),
                                              message=msg.type,
                                              group='None',
                                              username=msg.user.userName,
                                              send_time=get_now()),
                    toUserName=account_b.userName)
    else:
        itchat.send(forward_msg_format.format(sender=get_sender(msg),
                                              message=msg.text,
                                              group='None',
                                              username=msg.user.userName,
                                              send_time=get_now()),
                    toUserName=account_b.userName)


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING], isGroupChat=True)
def group_text_forward(msg):
    """
    将账户A收到的消息转发给账户B
    :param msg:
    :return:
    """
    account_b = get_account_b_user()
    if not account_b:
        return
    if msg.user.remarkName == account_b.remarkName:
        return

    if msg.type != 'Text':
        itchat.send_raw_msg(msg.msgType,
                            msg.oriContent if '' != msg.oriContent else msg.content,
                            toUserName=account_b.userName)
        itchat.send(forward_msg_format.format(sender=msg.actualNickName,
                                              message=msg.type,
                                              group=get_group_name(msg),
                                              username=msg.user.userName,
                                              send_time=get_now()),
                    toUserName=account_b.userName)
    else:
        itchat.send(forward_msg_format.format(sender=msg.actualNickName,
                                              message=msg.text,
                                              group=get_group_name(msg),
                                              username=msg.user.userName,
                                              send_time=get_now()),
                    toUserName=account_b.userName)


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def media_forward(msg):
    """
    将账户A收到的媒体文件转发给账户B

    如果消息是账户B发来的，则将文件存储并返回文件路径给账户B
    :param msg:
    :return:
    """
    download_path = 'download/' + msg.fileName
    msg.download(download_path)
    account_b = get_account_b_user()
    if msg.user.remarkName == account_b.remarkName:
        path = cache_media(msg)
        itchat.send(path, toUserName=account_b.userName)
        return
    itchat.send('@%s@%s' % ('img' if msg.type == 'Picture' else 'fil', download_path), account_b.userName)
    itchat.send(forward_msg_format.format(sender=get_sender(msg),
                                          message=msg.type,
                                          group='None',
                                          username=msg.user.userName,
                                          send_time=get_now()),
                toUserName=account_b.userName)


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True)
def group_media_forward(msg):
    """
    将账户A收到的媒体文件转发给账户B

    如果消息是账户B发来的，则将文件存储并返回文件路径给账户B
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
                                          username=msg.user.userName,
                                          send_time=get_now()),
                toUserName=account_b.userName)


def distribute_text(msg):
    """
    消息以 '/' 开头指的是要执行的命令
        1. /search xxx (根据关键词搜索好友或者群聊), 返回内容有 remarkName, nickName, actualNickName, userName 等

    消息包含引用, 则需要解析引用中的内容来分发消息
        1. 消息内容匹配文件路径格式, 提取引用中的 Username, 将消息内容匹配的文件发送给 Username 表示的用户
        2. 消息内容不是文件路径格式, 提取引用中的 Username, 将消息发送给 Username 表示的用户
    :param msg:
    :return:
    """
    account_b = get_account_b_user()
    text = msg.text
    if re.match(search_param_pattern, text):
        keyword = re.findall(search_param_pattern, text)[0]
        if keyword:
            friends = itchat.search_friends(name=keyword)
            chatrooms = itchat.search_chatrooms(name=keyword)
            result = friends + chatrooms
            if not result:
                itchat.send('friends or chat rooms not found', toUserName=account_b.userName)
            else:
                for friend in result:
                    itchat.send(friend_format.format(remark_name=friend.remarkName,
                                                     nick_name=friend.nickName,
                                                     username=friend.userName,
                                                     type='User' if type(friend) is User else 'Group'),
                                toUserName=account_b.userName)
        else:
            return
    elif re.match(quote_pattern, text):
        findall = re.findall(quote_pattern, text)[0]
        quote_msg = findall[0]
        main_msg = findall[1]
        username = re.findall(username_pattern, quote_msg)[0]
        if not username:
            logger.warning("消息中没有解析出 Username")
            return
        if re.match(file_path_pattern, main_msg):
            # 消息是文件路径, 将对应的文件发送给 Username 表示的用户
            itchat.send('@%s@%s' % ('img' if is_img(main_msg) else 'fil', main_msg), username)
        else:
            # 消息没有文件路径, 提取引用中的 Username, 将消息发送给 Username 表示的用户
            itchat.send(main_msg, username)
    else:
        logger.warning("消息不符合格式, 不进行分发")


@itchat.msg_register(FRIENDS)
def add_friend(msg):
    """
    Automatically approve friend requests.
    :param msg:
    :return:
    """
    msg.user.verify()
    msg.user.send('Nice to meet you!')


def cache_media(msg):
    """
    save the file path for future use
    :param msg:
    :return:
    """
    download_path = 'download/' + msg.fileName
    msg.download(download_path)
    return download_path


def get_group_name(msg):
    group = msg.user.nickName
    if not group:
        group = ','.join(member.nickName for member in msg.user.memberList[:3]) + '...'
    return group


def is_img(file_name):
    global img_extensions
    return os.path.splitext(file_name)[1].lower() in img_extensions


def get_sender(msg):
    remark_name = msg.user.remarkName
    return remark_name if '' != remark_name else msg.user.nickName


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
