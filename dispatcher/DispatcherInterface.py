import re
from abc import ABC, abstractmethod

import config
from lib.itchat.storage import User
from main import logger
from util import is_img

friend_format = '''RemarkName: {remark_name}
NickName: {nick_name}
Type: {type}
Username: {username}
'''


class DispatcherInterface(ABC):
    @abstractmethod
    def dispatch(self, msg):
        pass


class WechatDispatcher(DispatcherInterface):
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
        if re.match(WechatDispatcher.search_param_pattern, text):
            keyword = re.findall(WechatDispatcher.search_param_pattern, text)[0]
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

        elif re.match(WechatDispatcher.ping_pattern, text):
            # 检查服务是否在运行
            self.bot.send('/pong', toUserName=account_b.userName)

        elif re.match(WechatDispatcher.quote_pattern, text):
            findall = re.findall(WechatDispatcher.quote_pattern, text)[0]
            quote_msg = findall[0]
            main_msg = findall[1]
            username = re.findall(WechatDispatcher.username_pattern, quote_msg)[0]
            if not username:
                logger.warning("消息中没有解析出 Username")
                return
            if re.match(WechatDispatcher.file_path_pattern, main_msg):
                # 消息是文件路径, 将对应的文件发送给 Username 表示的用户
                self.bot.send('@%s@%s' % ('img' if is_img(main_msg) else 'fil', main_msg), username)
            else:
                # 消息没有文件路径, 提取引用中的 Username, 将消息发送给 Username 表示的用户
                self.bot.send(main_msg, username)

        else:
            logger.warning("消息不符合格式, 不进行分发")

    def get_account_b_user(self):
        account_b_remark_name = config.account_b_remark_name
        friends = self.bot.search_friends(remarkName=account_b_remark_name)
        if not friends:
            logger.error(f'{account_b_remark_name} not found in friends list')
            return None
        return friends[0]


class TgDispatcher(DispatcherInterface):
    def __init__(self, bot):
        self.bot = bot

    def dispatch(self, **kwargs):
        # todo 完善分发的逻辑
        print("Dispatcher dispatching")


def get_dispatcher(dispatcher_type, bot):
    """
    根据配置获取分发器
    :param dispatcher_type: wechat or tg
    :param bot: itchat or telebot
    :return:
    """
    if dispatcher_type == "wechat":
        return WechatDispatcher(bot)
    elif dispatcher_type == "tg":
        return TgDispatcher(bot)
    else:
        raise NotImplementedError("Dispatcher not available for type %s" % (dispatcher_type,))
