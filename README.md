# wechat-bridge

> python 3.10, 3.11

微信双开绕路版, wechat-bridge 可以做以下几件事

1. 微信消息转发: `账号A`接收到的消息转发给`账号B`
2. 通过`账号B`操作`账号A`回复消息: `账号B`发送给`账号A`的消息, 经过解析会发送给`账号A`的好友/群聊
3. 搜索好友/群聊: `账号B`通过向`账号A`发送特定格式的消息, 可以搜索`账号A`的好友/群聊

# 准备

完善项目根目录中 `config.py` 中的配置

## 配置说明

```python
# 转发类型 tg 还是 wechat, 如果是 tg 则需要配置 tg_bot_api_key 和 proxy, 如果是 wechat 则需要配置 account_b_remark_name
relay_type = 'tg'

# tg bot api key, 如何获取请及配置自行 Google
tg_bot_api_key = ''
# tg bot 的代理 配置示例: proxy = {'https': 'http://127.0.0.1:7890'}
proxy = None

# 账号B的备注名, 账号A向账号B转发消息时是通过这个备注名来确定账号B的
# 如果有多个相同的备注名, 则会取列表中的第一个
# 所以配置时请确保账号A中账号B的备注名的唯一, 否则可能会发送给其他人
account_b_remark_name = 'MattMin'

# 需要转发消息的群白名单, 群名称包含以下关键字即可, 不支持模糊匹配
# 如果全部都转发, 可配置成: ['*']
# 如果都不转发, 可配置成: []
group_white_list = ['测试', '测试1']
```

## 使用 Python 直接启动

1. 安装依赖: `pip3 install -r requirements.txt`
2. 启动项目: `nohup python3 main.py > nohup.log & tail -f nohup.log`

## 使用 Docker

1. 构建 Docker 镜像: `docker build -t wechat-bridge:1.0 .`
2. 启动项目: `docker run -d --name wechat-bridge wechat-bridge:1.0`
3. 查看日志: `docker logs -f wechat-bridge`

# 使用

## relay 使用 wechat

### 登录
项目启动时控制台会输出二维码, 通过扫码登录

### 搜索好友/群聊

使用`账号B`向`账号A`发送消息, 消息格式为 `/search xxx` xxx 即为要搜索好友的用户名/备注名, 或群聊名称, 搜索结果`账号A`
会发送给`账号B`, 多个结果会有多条消息

## 向搜索结果中的某个好友/群聊发消息

想发送给谁就引用(长按消息, 选择引用)对应的搜索结果, 输入的消息内容会发送给对应`账号A`的好友/群聊

### 回复消息

引用你要回复的消息再回复, 就会将消息发送给对应`账号A`的好友/群聊

### 发送图片

1. 使用账号B发送一张图片给`账号A`, 会返回一个图片路径
2. 引用要回复的消息或者搜索结果, 消息内容填上一步返回的路径, 即可将图片发送到对应`账号A`的好友/群聊

## relay 使用 tg

### tg bot command 配置

```
info - 运行信息
search - 搜索好友或群组
login - 登录
logout - 退出登录
```

### 登录
输入 `/login` 命令, tg bot 会返回登录二维码, 也可以扫描控制台输出的二维码登录

### 退出登录
输入 `/logout` 可以退出登录, 退出登录后程序不会结束运行, 输入 `/login` 可以重新登录
退出登录后 tg bot 

### 搜索好友/群聊

与使用 wechat 相同

## 向搜索结果中的某个好友/群聊发消息

与使用 wechat 相同

### 回复消息

与使用 wechat 相同

### 发送图片

发送图片时回复相应的消息即图片就回发送到对应`账号A`的好友/群聊

## TODO

- [x] 转发群消息的群白名单
- [x] 日志(nohup日志)
- [x] 接入 TG BOT
- [x] 微信意外退出后通过 TG 通知
- [x] 完善 Readme, 使用说明
- [x] 分享的消息简化(提取 xml 中有意义的字段传输)