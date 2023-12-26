import re
from abc import ABC, abstractmethod

import config
from lib.itchat.storage import User
from util import is_img, get_group_name, get_sender, get_now, cache_media, logger

friend_format = '''RemarkName: {remark_name}
NickName: {nick_name}
Type: {type}
Username: {username}
'''

# 账号A 转发到 账号B 的消息格式
forward_msg_format = '''{sender}: {message}
------------------------------
Group: {group}
------------------------------
SendTime: {send_time}
------------------------------
Username: {username}
'''


class RelayInterface(ABC):
    @abstractmethod
    def dispatch(self, msg):
        """
        将消息分发到账号A的好友/群聊
        :param msg:
        :return:
        """
        pass

    @abstractmethod
    def forward(self, msg, is_group, is_media):
        """
        将账号A收到的消息转发到账号B或者TG Bot
        :param is_media: 是否是媒体文件
        :param is_group: 是否是群消息
        :param msg: itchat 消息对象
        :return:
        """
        pass


class WechatRelay(RelayInterface):
    # 搜索的格式
    search_param_pattern = r'/search (.*)'
    # ping
    ping_pattern = r'/ping'
    # 引用的格式
    quote_pattern = r'「.*：([\s\S]*)」\n- - - - - - - - - - - - - - -\n([\s\S]*)'
    # 用户名的格式
    username_pattern = r'.*Username: (.*)'
    # 文件下载路径的格式
    file_path_pattern = r'download/.*\..*'

    def __init__(self, bot):
        self.bot = bot

    def dispatch(self, msg):
        """
            消息以 '/' 开头指的是要执行的命令
                1. /search xxx (根据关键词搜索好友或者群聊), 返回内容有 remarkName, nickName, actualNickName, userName 等

            消息包含引用, 则需要解析引用中的内容来分发消息
                1. 消息内容匹配文件路径格式, 提取引用中的 Username, 将消息内容匹配的文件发送给 Username 表示的用户
                2. 消息内容不是文件路径格式, 提取引用中的 Username, 将消息发送给 Username 表示的用户
            :param msg:
            :return:
            """
        account_b = self.get_account_b_user()
        text = msg.text
        if re.match(WechatRelay.search_param_pattern, text):
            keyword = re.findall(WechatRelay.search_param_pattern, text)[0]
            if keyword:
                friends = self.bot.search_friends(name=keyword)
                chatrooms = self.bot.search_chatrooms(name=keyword)
                result = friends + chatrooms
                if not result:
                    self.bot.send('friends or chat rooms not found', toUserName=account_b.userName)
                else:
                    for friend in result:
                        self.bot.send(friend_format.format(remark_name=friend.remarkName,
                                                           nick_name=friend.nickName,
                                                           username=friend.userName,
                                                           type='User' if type(friend) is User else 'Group'),
                                      toUserName=account_b.userName)

        elif re.match(WechatRelay.ping_pattern, text):
            # 检查服务是否在运行
            self.bot.send('/pong', toUserName=account_b.userName)

        elif re.match(WechatRelay.quote_pattern, text):
            findall = re.findall(WechatRelay.quote_pattern, text)[0]
            quote_msg = findall[0]
            main_msg = findall[1]
            username = re.findall(WechatRelay.username_pattern, quote_msg)[0]
            if not username:
                logger.warning("消息中没有解析出 Username")
                return
            if re.match(WechatRelay.file_path_pattern, main_msg):
                # 消息是文件路径, 将对应的文件发送给 Username 表示的用户
                self.bot.send('@%s@%s' % ('img' if is_img(main_msg) else 'fil', main_msg), username)
            else:
                # 消息没有文件路径, 提取引用中的 Username, 将消息发送给 Username 表示的用户
                self.bot.send(main_msg, username)

        else:
            logger.warning("消息不符合格式, 不进行分发")

    def forward(self, msg, is_group, is_media):
        account_b = self.get_account_b_user()
        if is_group:
            group_name = get_group_name(msg)
            if is_media:
                download_path = 'download/' + msg.fileName
                msg.download(download_path)
                if msg.user.remarkName == account_b.remarkName:
                    return
                self.bot.send('@%s@%s' % ('img' if msg.type == 'Picture' else 'fil', download_path), account_b.userName)
                self.bot.send(forward_msg_format.format(sender=msg.actualNickName,
                                                        message=msg.type,
                                                        group=group_name,
                                                        username=msg.user.userName,
                                                        send_time=get_now()),
                              toUserName=account_b.userName)
            else:
                if not account_b:
                    return
                if msg.user.remarkName == account_b.remarkName:
                    return

                if msg.type != 'Text':
                    self.bot.send_raw_msg(msg.msgType,
                                          msg.oriContent if '' != msg.oriContent else msg.content,
                                          toUserName=account_b.userName)
                    self.bot.send(forward_msg_format.format(sender=msg.actualNickName,
                                                            message=msg.type,
                                                            group=group_name,
                                                            username=msg.user.userName,
                                                            send_time=get_now()),
                                  toUserName=account_b.userName)
                else:
                    self.bot.send(forward_msg_format.format(sender=msg.actualNickName,
                                                            message=msg.text,
                                                            group=group_name,
                                                            username=msg.user.userName,
                                                            send_time=get_now()),
                                  toUserName=account_b.userName)
        else:
            if is_media:
                download_path = 'download/' + msg.fileName
                msg.download(download_path)
                if msg.user.remarkName == account_b.remarkName:
                    path = cache_media(msg)
                    self.bot.send(path, toUserName=account_b.userName)
                    return
                self.bot.send('@%s@%s' % ('img' if msg.type == 'Picture' else 'fil', download_path), account_b.userName)
                self.bot.send(forward_msg_format.format(sender=get_sender(msg),
                                                        message=msg.type,
                                                        group='None',
                                                        username=msg.user.userName,
                                                        send_time=get_now()),
                              toUserName=account_b.userName)
            else:
                if msg.type != 'Text':
                    self.bot.send_raw_msg(msg.msgType,
                                          msg.oriContent if '' != msg.oriContent else msg.content,
                                          toUserName=account_b.userName)
                    self.bot.send(forward_msg_format.format(sender=get_sender(msg),
                                                            message=msg.type,
                                                            group='None',
                                                            username=msg.user.userName,
                                                            send_time=get_now()),
                                  toUserName=account_b.userName)
                else:
                    self.bot.send(forward_msg_format.format(sender=get_sender(msg),
                                                            message=msg.text,
                                                            group='None',
                                                            username=msg.user.userName,
                                                            send_time=get_now()),
                                  toUserName=account_b.userName)

    def get_account_b_user(self):
        account_b_remark_name = config.account_b_remark_name
        friends = self.bot.search_friends(remarkName=account_b_remark_name)
        if not friends:
            logger.error(f'{account_b_remark_name} not found in friends list')
            return None
        return friends[0]


class TgRelay(RelayInterface):
    def __init__(self, bot):
        self.bot = bot

    def dispatch(self, **kwargs):
        # todo 完善分发的逻辑
        print("Dispatcher dispatching")

    def forward(self, msg):
        # todo 转发
        pass
