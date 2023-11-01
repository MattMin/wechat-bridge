import logging

import config
from lib import itchat
from lib.itchat.content import *

logger = logging.getLogger('itchat')


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
        # todo distribute the message
        return
    itchat.send(config.forward_msg_format.format(sender=msg.user.remarkName, message=msg.text, group='None'),
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
        # todo
        return
    itchat.send('@%s@%s' % (
        'img' if msg.type == 'Picture' else 'fil', download_path),
                account_b.userName)


def get_account_b_user():
    account_b_remark_name = config.account_b_remark_name
    friends = itchat.search_friends(remarkName=account_b_remark_name)
    if not friends:
        logger.error(f'{account_b_remark_name} not found in friends list')
        return None
    return friends[0]


itchat.auto_login(enableCmdQR=2, hotReload=True)
itchat.run(True)
