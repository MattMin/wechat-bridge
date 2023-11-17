# wechat-bridge
> python 3.10, 3.11

wechat-bridge 可以做以下几件事

1. 微信消息转发: `账号A`接收到的消息转发给`账号B`
2. 通过`账号B`操作`账号A`回复消息: `账号B`发送给`账号A`的消息, 经过解析会发送给`账号A`的好友/群聊
3. 搜索好友/群聊: `账号B`通过向`账号A`发送特定格式的消息, 可以搜索`账号A`的好友/群聊

## 准备
1. 完善项目根目录中 `config.py` 中的配置
2. 安装依赖: `pip3 install -r requirements.txt`
3. 启动项目: `nohup python3 main.py > nohup.log & tail -f nohup.log`
4. 使用`账号A`扫码登录即可

### 配置说明
```python
# 账号B的备注名, 账号A向账号B转发消息时是通过这个备注名来确定账号B的
# 如果有多个相同的备注名, 则会取列表中的第一个
# 所以配置时请确保账号A中账号B的备注名的唯一, 否则可能会发送给其他人
account_b_remark_name = 'MattMin'


# 需要转发消息的群白名单, 群名称包含以下关键字即可, 不支持模糊匹配
# 如果全部都转发, 可配置成: ['*']
# 如果都不转发, 可配置成: []
group_white_list = ['测试', '测试1']
```

## 使用
### 搜索好友/群聊
使用`账号B`向`账号A`发送消息, 消息格式为 `/search xxx` xxx 即为要搜索好友的用户名/备注名, 或群聊名称, 搜索结果`账号A`会发送给`账号B`, 多个结果会有多条消息

### 向搜索结果中的某个好友/群聊发消息
想发送给谁就引用(长按消息, 选择引用)对应的搜索结果, 输入的消息内容会发送给对应`账号A`的好友/群聊

### 回复消息
引用你要回复的消息再回复, 就会将消息发送给对应`账号A`的好友/群聊

### 发送图片
1. 使用账号B发送一张图片给`账号A`, 会返回一个图片路径
2. 引用要回复的消息或者搜索结果, 消息内容填上一步返回的路径, 即可将图片发送到对应`账号A`的好友/群聊


## TODO
- [x] 转发群消息的群白名单
- [x] 日志(nohup日志)
- [ ] 接入 TG BOT
