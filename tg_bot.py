#!/usr/bin/python
import io
import os
import pickle
import re
from datetime import datetime

import telebot
from telebot import apihelper
from telebot.types import InputFile

import config
from lib import itchat
from lib.itchat.storage import User
from util import is_img, is_audio, is_video, logger, search_param_pattern, friend_format, username_pattern, \
    img_extensions

API_TOKEN = ''
bot = telebot.TeleBot(API_TOKEN)
apihelper.proxy = config.proxy

chat_id_file = 'chat_id.pkl'
chat_id = 0
start_time = datetime.now()

forward_msg_format = '''{sender}: {message}
------------------------------
Group: {group}
------------------------------
SendTime: {send_time}
------------------------------
Username: {username}
'''


@bot.message_handler(commands=['info'])
def info(message):
    # 计算时间差
    time_delta = datetime.now() - start_time
    # 将时间差转换为天、小时和分钟
    days = time_delta.days
    hours, remainder = divmod(time_delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    bot.send_message(chat_id=message.chat.id,
                     text=f"""\
*itchat运行状态*: {get_login_status()}
*运行时间*: {days}天{hours}小时{minutes}分
""",
                     parse_mode='MarkdownV2')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    初始化 chat_id
    :param message:
    :return:
    """
    global chat_id
    chat_id = message.chat.id
    save_chat_id(chat_id)
    bot.send_message(chat_id=chat_id, text=f'Chat ID 获取成功: `{chat_id}`, 使用 `/login` 开始登录',
                     parse_mode='MarkdownV2')


@bot.message_handler(commands=['login'])
def wechat_login(message):
    itchat.auto_login(enableCmdQR=2,
                      loginCallback=login_call_back,
                      exitCallback=exit_call_back,
                      qrCallback=qr_callback)


@bot.message_handler(commands=['logout'])
def wechat_logout(message):
    itchat.logout()
    logger.info('/logout command executed')


@bot.message_handler(commands=['search'])
def search(message):
    try:
        keyword = re.findall(search_param_pattern, message.text)[0]
    except Exception as e:
        logger.warn(f'/search 出现异常: {e}')
        bot.send_message(chat_id=get_chat_id(), text='/search 需要一个参数')
        return

    if keyword:
        friends = itchat.search_friends(name=keyword)
        chatrooms = itchat.search_chatrooms(name=keyword)
        result = friends + chatrooms
        if not result:
            bot.send_message(chat_id=get_chat_id(), text='friends or chat rooms not found')
        else:
            for friend in result:
                bot.send_message(chat_id=get_chat_id(),
                                 text=friend_format.format(remark_name=friend.remarkName,
                                                           nick_name=friend.nickName,
                                                           username=friend.userName,
                                                           type='User' if type(friend) is User else 'Group'))


# Handle all text messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def dispatch_text_message(message):
    reply_message = message.reply_to_message
    username = re.findall(username_pattern, reply_message.text)[0]
    if not username:
        logger.warning("消息中没有解析出 Username")
        bot.send_message(chat_id=get_chat_id(), text='引用的消息中没有解析出 Username')
    else:
        itchat.send(message.text, username)


# Handle all image messages
@bot.message_handler(func=lambda message: True, content_types=['photo'])
def dispatch_photo_message(message):
    reply_message = message.reply_to_message
    username = re.findall(username_pattern, reply_message.text)[0]
    if not username:
        logger.warning("消息中没有解析出 Username")
        bot.send_message(chat_id=get_chat_id(), text='引用的消息中没有解析出 Username')
    else:
        photo_size_list = message.photo
        file = bot.get_file(photo_size_list[len(photo_size_list) - 1].file_id)
        download_file = bot.download_file(file.file_path)
        download_path = f'download/{file.file_id}{os.path.splitext(file.file_path)[1].lower()}'
        with open(download_path, 'wb') as f:
            f.write(download_file)
        logger.info(f'file received, path: {download_path}')
        itchat.send('@%s@%s' % ('img', download_path), username)


# Handle all document messages
@bot.message_handler(func=lambda message: True, content_types=['document'])
def dispatch_document_message(message):
    # 判断是不是图片格式
    reply_message = message.reply_to_message
    username = re.findall(username_pattern, reply_message.text)[0]
    if not username:
        logger.warning("消息中没有解析出 Username")
        bot.send_message(chat_id=get_chat_id(), text='引用的消息中没有解析出 Username')
    else:
        # todo 下载文件到本地
        file = bot.get_file(message.document.file_id)
        download_file = bot.download_file(file.file_path)
        file_extension = os.path.splitext(file.file_path)[1].lower()
        download_path = f'download/{file.file_id}{file_extension}'
        with open(download_path, 'wb') as f:
            f.write(download_file)
        logger.info(f'file received, path: {download_path}')
        itchat.send('@%s@%s' % ('img' if file_extension in img_extensions else 'fil', download_path), username)


def send_file(file_path, caption):
    """
    根据文件类型调用不同的发送方法
    :param file_path: 文件路径
    :param caption: 文件说明
    :return:
    """
    with open(file_path, 'rb') as f:
        file = InputFile(f)
        if is_img(file_path):
            bot.send_photo(chat_id=get_chat_id(), photo=file, caption=caption)
        elif is_audio(file_path):
            bot.send_audio(chat_id=get_chat_id(), audio=file, caption=caption)
        elif is_video(file_path):
            bot.send_video(chat_id=get_chat_id(), video=file, caption=caption)
        else:
            bot.send_document(chat_id=get_chat_id(), document=file, caption=caption)


def save_chat_id(_chat_id):
    """
    将 chat_id 保存到文件中
    :param _chat_id:
    :return:
    """
    with open(chat_id_file, 'wb') as f:
        pickle.dump(_chat_id, f)
    return True


def read_chat_id():
    """
    从文件中读取 chat_id
    :return:
    """
    with open(chat_id_file, 'rb') as file:
        loaded_variable = pickle.load(file)
    global chat_id
    chat_id = loaded_variable
    return loaded_variable


def get_chat_id():
    return chat_id if chat_id != 0 else read_chat_id()


def get_login_status():
    friends = itchat.get_friends()
    if friends:
        return '已登录'
    else:
        return '未登录'


def qr_callback(uuid, status, qrcode, isLoggedIn):
    if '0' == status:
        bot.send_photo(chat_id=get_chat_id(),
                       photo=InputFile(io.BytesIO(qrcode)),
                       caption=f'请使用微信的账号A扫描二维码进行登录\nQR UUID: {uuid}')
    if '201' == status and isLoggedIn is not None:
        bot.send_message(chat_id=get_chat_id(), text='请在手机上确认')


def login_call_back(username=None, nickname=None):
    logger.info('Login successfully as %s' % nickname)
    bot.send_message(chat_id=get_chat_id(), text=f'{nickname} 登录成功')


def exit_call_back(username=None, nickname=None):
    logger.info('Logout successfully %s' % nickname)
    bot.send_message(chat_id=get_chat_id(), text=f'{nickname} 退出登录')
