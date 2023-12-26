#!/usr/bin/python
import io
import pickle
from datetime import datetime

import telebot
from telebot.types import InputFile
from lib import itchat
from util import is_img, is_audio, is_video

API_TOKEN = ''
bot = telebot.TeleBot(API_TOKEN)

chat_id_file = 'chat_id.pkl'
chat_id = 0
start_time = datetime.now()

# TODO 实现消息分发的基本功能
# TODO 微信 logout 提醒

forward_msg_format = '''{sender}: {message}
------------------------------
Group: {group}
------------------------------
SendTime: {send_time}
------------------------------
Username: {username}
'''


@bot.message_handler(commands=['info'])
def echo_info(message):
    # 计算时间差
    time_delta = datetime.now() - start_time
    # 将时间差转换为天、小时和分钟
    days = time_delta.days
    hours, remainder = divmod(time_delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    bot.send_message(chat_id=message.chat.id,
                     text=f"""\
*itchat运行状态*: 已登录
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
    bot.send_message(chat_id=chat_id, text=f'Chat ID 获取成功: `{chat_id}`', parse_mode='MarkdownV2')


@bot.message_handler(commands=['login'])
def wechat_login(message):
    itchat.auto_login(enableCmdQR=2, qrCallback=qr_callback)


def qr_callback(uuid, status, qrcode):
    bot.send_photo(chat_id=get_chat_id(),
                   photo=InputFile(io.BytesIO(qrcode)),
                   caption=f'请使用微信的账号A扫描二维码进行登录\nQR UUID: {uuid}')


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.send_message(chat_id=get_chat_id(), text=forward_msg_format.format(sender=message.from_user.username,
                                                                           message=message.text,
                                                                           group='None',
                                                                           send_time=message.date,
                                                                           username=message.from_user.id))


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


# bot.infinity_polling()
