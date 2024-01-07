import datetime
import logging
import os
import xml.etree.ElementTree as ET

import yaml

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger('wechat-bridge')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

img_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']

# 搜索的格式
search_param_pattern = r'/search (.*)'
username_pattern = r'.*Username: (.*)'

friend_format = '''RemarkName: {remark_name}
NickName: {nick_name}
Type: {type}
Username: {username}
'''

# 账号A 转发到 账号B 的消息格式
forward_msg_format = '''{sender}: {message}
---------------
Group: {group}
---------------
Username: {username}
'''


def is_img(file_name):
    # global img_extensions
    return os.path.splitext(file_name)[1].lower() in img_extensions


def is_audio(file_name):
    return os.path.splitext(file_name)[1].lower() in audio_extensions


def is_video(file_name):
    return os.path.splitext(file_name)[1].lower() in video_extensions


def get_group_name(msg):
    group = msg.user.nickName
    if not group:
        group = ','.join(member.nickName for member in msg.user.memberList[:3]) + '...'
    return group


def get_sender(msg):
    remark_name = msg.user.remarkName
    return remark_name if '' != remark_name else msg.user.nickName


# 递归地将XML数据转换为Python对象
def xml_to_dict(element):
    data = {}
    for child in element:
        if list(child):
            data[child.tag] = xml_to_dict(child)
        else:
            data[child.tag] = child.text
    return data


# 递归地过滤掉没有值的字段
def filter_empty_fields(data):
    filtered_data = {}
    for k, v in data.items():
        if isinstance(v, dict):
            filtered_v = filter_empty_fields(v)
            if filtered_v:
                filtered_data[k] = filtered_v
        elif v and v not in ['0', '0.0', 'null']:
            filtered_data[k] = v
    return filtered_data


def xml_to_yaml(xml_string):
    """
    解析 xml 成 yaml 便于阅读, 如果解析失败返回原文
    :param xml_string:
    :return:
    """
    try:
        # 解析XML数据
        root = ET.fromstring(xml_string)
        # 将XML数据转换为Python对象
        data = xml_to_dict(root)
        filtered_data = filter_empty_fields(data)
        return yaml.dump(filtered_data, allow_unicode=True)
    except Exception as e:
        logger.info(f'xml 解析失败: {e}, {xml_string}')
        return xml_string
