import telebot

bot_token = ''
bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['ping'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")

bot.polling()