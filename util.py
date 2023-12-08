import os

img_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']


def is_img(file_name):
    # global img_extensions
    return os.path.splitext(file_name)[1].lower() in img_extensions


def is_audio(file_name):
    return os.path.splitext(file_name)[1].lower() in audio_extensions


def is_video(file_name):
    return os.path.splitext(file_name)[1].lower() in video_extensions