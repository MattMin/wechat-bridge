#!/usr/bin/python
import pickle
from datetime import datetime

import telebot

API_TOKEN = ''
bot = telebot.TeleBot(API_TOKEN)

chat_id_file = 'chat_id.pkl'
chat_id = 0
start_time = datetime.now()


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


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.send_message(chat_id=get_chat_id(), text='hello')


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


bot.infinity_polling()
