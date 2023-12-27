import datetime
import os
import logging


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

friend_format = '''RemarkName: {remark_name}
NickName: {nick_name}
Type: {type}
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


def get_now():
    current_utc_time = datetime.datetime.utcnow()
    eastern_offset = datetime.timedelta(hours=8)
    return current_utc_time + eastern_offset


def cache_media(msg):
    """
    save the file path for future use
    :param msg:
    :return:
    """
    download_path = 'download/' + msg.fileName
    msg.download(download_path)
    return download_path