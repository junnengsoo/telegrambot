import constants as keys
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
from telegram import Update, Bot
import responses as R


print("Bot Started...")


def start_command(update: Update, context: CallbackContext):
    update.message.reply_text("Type something to get started!")


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("Lame...")


def handle_message(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def error(update, context):
    print(f"Update {update} caused error {context.error}")


def main():
    updater = Updater(token=keys.API_KEY, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
