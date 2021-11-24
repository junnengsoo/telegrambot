import datetime
import readfile as rf

import constants as keys
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
from telegram import Update
import responses as R


# https://stackoverflow.com/questions/62445753/how-to-send-pdf-file-back-to-user-using-python-telegram-bot - sending file back to user
# https://stackoverflow.com/questions/31096358/how-do-i-download-a-file-or-photo-that-was-sent-to-my-telegram-bot - downloading file sent to bot


print("Bot Started...")


def start_command(update: Update, context: CallbackContext):
    update.message.reply_text("Type something to get started!")


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("Lame...")


def workout_command(update: Update, context: CallbackContext):
    text = f"```{rf.get_workout_by_date(str(datetime.date.today()) + ' 00:00:00')}```"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)
    # context.bot.send_message(chat_id=update.effective_chat.id, text='test')


def handle_message(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def downloader(update: Update, context: CallbackContext):
    with open(f"{update.message.from_user['id']}.xlsx", 'wb') as f:
        context.bot.get_file(update.message.document).download(out=f)


def error(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")


def main():
    updater = Updater(token=keys.API_KEY, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("workout", workout_command))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    dp.add_handler(MessageHandler(Filters.document, downloader))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
