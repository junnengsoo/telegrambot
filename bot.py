import datetime
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
)
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
import sqlite3
import pandas as pd
import csv
import urllib.request
import logging
import os

# https://stackoverflow.com/questions/36872308/locking-telegram-custom-keyboard-buttons-for-multiple-inputs
# inline keyboard testing
# https://towardsdatascience.com/how-to-deploy-a-telegram-bot-using-heroku-for-free-9436f89575d2
# https://stackoverflow.com/questions/62445753/how-to-send-pdf-file-back-to-user-using-python-telegram-bot - sending file back to user
# https://stackoverflow.com/questions/31096358/how-do-i-download-a-file-or-photo-that-was-sent-to-my-telegram-bot - downloading file sent to bot


PORT = int(os.environ.get('PORT', 5000))
API_KEY = "2131896364:AAH6u2F3__TmQ7gIKNZpJA-K1HPajSQmFAA"
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

print("Bot Started...")

# Stages
FIRST, SECOND, THIRD = range(3)

conn = sqlite3.connect(':memory:', check_same_thread=False)
c = conn.cursor()

query_list = []
reply_markup = []
user_id = []


def start_command(update: Update, context: CallbackContext) -> int:
    """Starts the conversation."""
    global user_id
    user_id = update.message.from_user['id']
    update.message.reply_text("""
Welcome to Jun's Iron Church telegram bot!

To use: 
1. Send the google sheets URL and sheet name to this telegram bot in the following format:
your_google_sheets_url (your_sheet_name)
e.g. https://docs.google.com/spreadsheets/d/19wwdOS01lprzKgXXtZZ_bVM7bGJc9STpaaPnUQiEtFw/edit#gid=0 (Sheet1)

Ensure that you do the following:
1) Create a google excel sheet with your workout program in the format of this following document: 
https://docs.google.com/spreadsheets/d/19wwdOS01lprzKgXXtZZ_bVM7bGJc9STpaaPnUQiEtFw/edit#gid=0.
2) Save and change permission for anyone with the link to be able to view.
3) Note that the there should only be one row of column headers at the top of the Google Sheets.
4) Your Google Sheet should also include a column for the 'Date' of the exercise.
    """)

    return FIRST


def edit_url(update: Update, context: CallbackContext) -> int:
    """Updates the Google Sheets URL."""
    username = update.message.from_user['username']
    global user_id
    user_id = update.message.from_user['id']
    text = f"""
Hi {username}! To update your Google Sheets URL, please send your Google Sheets URL and sheet name in the following format:
your_google_sheets_url (your_sheet_name)
e.g. https://docs.google.com/spreadsheets/d/19wwdOS01lprzKgXXtZZ_bVM7bGJc9STpaaPnUQiEtFw/edit#gid=0 (Sheet1)
"""
    update.message.reply_text(text)

    return FIRST


def select(update: Update, context: CallbackContext) -> int:
    if update.message.text:
        user_input = update.message.text
        sheets_url = url_converter(user_input)
        store_url(sheets_url)
        update.message.reply_text('I have received your Google Sheets!')
    colnames = conn.execute(f"SELECT * FROM '{user_id}'").description
    headers_list = list(map(lambda x: x[0], colnames))
    button_list = []
    for each in headers_list:
        button_list.append(InlineKeyboardButton(each, callback_data=each))
    button_list.append(InlineKeyboardButton('Done', callback_data='done'))
    global reply_markup
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    update.message.reply_text('Please choose the headers:', reply_markup=reply_markup)

    return SECOND


def edit_header(update: Update, context: CallbackContext) -> int:
    """Updates the headers to be shown when /workout is used."""
    global user_id
    user_id = update.message.from_user['id']
    colnames = conn.execute(f"SELECT * FROM '{user_id}'").description
    headers_list = list(map(lambda x: x[0], colnames))
    button_list = []
    for each in headers_list:
        button_list.append(InlineKeyboardButton(each, callback_data=each))
    button_list.append(InlineKeyboardButton('Done', callback_data='done'))
    global reply_markup
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    update.message.reply_text('Please choose the headers:', reply_markup=reply_markup)

    return SECOND


def display(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    global query_list
    query_list = query.data.split(" ")
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"{query.data} is added as a column header")
    query.answer()
    query.edit_message_text(text="Select other headers or click Done to end the selection!", reply_markup=reply_markup)

    return THIRD


def display_2(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if 'done' not in query.data:
        if query.data not in query_list:
            query_list.append(query.data)
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"{query.data} is added as a column header")
        else:
            text = f"{query.data} is already added as a column header, choose another header or click Done to end the selection!"
            context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        del update.callback_query.data
        return THIRD
    store_header(query_list)
    query.edit_message_text(text="I have received your input! Type /workout to receive your workout for today!")

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text('Bye! I hope we can talk again some day.')

    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext):
    text = """
1) /start : Begin using the bot
2) /editurl : Send a new Google Sheets URL or Google Sheet to replace the existing data
3) /editheader : Change headers to be shown for /workout
4) /workout : Display the workout for the day
5) /cancel : Cancel changes made
    """
    update.message.reply_text(text)


def received_url(update: Update, context: CallbackContext):
    if update.message.text:
        user_input = update.message.text
        sheets_url = url_converter(user_input)
        store_url(sheets_url)
        update.message.reply_text('I have updated your Google Sheets url!')


def workout_command(update: Update, context: CallbackContext):
    """Sends the workout for today's date."""
    global user_id
    user_id = update.message.from_user['id']
    df_from_db = get_workout_by_date(str(datetime.date.today().strftime('%d/%m/%Y')))
    if df_from_db.empty:
        no_workout = "You do not have any workout today!"
        context.bot.send_message(chat_id=update.effective_chat.id, text=no_workout)
    else:
        text = f"```{df_from_db.to_string(index=False)}```"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)


def message_handler(update: Update, context: CallbackContext):
    """Prompts user when user sends a message."""
    text = "Welcome to the Iron Church Bot! Type /start or /help for more instructions!"
    update.message.reply_text(text)


# Google Sheets url to csv file
# https://stackoverflow.com/questions/33713084/download-link-for-google-spreadsheets-csv-export-with-multiple-sheets
# https://docs.google.com/spreadsheets/d/{key}/gviz/tq?tqx=out:csv&sheet={sheet_name}


def error(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    try:
        if 'list index out of range' in str(context.error):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Please input a valid URL and sheet name.")
        elif 'duplicate column name' in str(context.error):
            text = 'There is a duplicate column name in your Google Sheets'
            context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        elif 'column' in str(context.error):
            text = """Please edit the Google Sheets in the format of the following document:
                   https://docs.google.com/spreadsheets/d/19wwdOS01lprzKgXXtZZ_bVM7bGJc9STpaaPnUQiEtFw/edit#gid=0.
                   """
            context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Type /start to get started.")
    except:
        text = f"Error {context.error}, text daddy Jun Neng to fix it!"
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def main():
    updater = Updater(token=API_KEY, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(CommandHandler("help", help_command))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command),
                      CommandHandler("editurl", edit_url),
                      CommandHandler("editheader", edit_header)],
        states={
            FIRST: [MessageHandler(Filters.text, select)],
            SECOND: [CallbackQueryHandler(display)],
            THIRD: [CallbackQueryHandler(display_2)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("workout", workout_command))
    dp.add_handler(MessageHandler(Filters.text, message_handler))
    dp.add_error_handler(error)
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=API_KEY)
    updater.bot.setWebhook('https://pure-chamber-09599.herokuapp.com/' + API_KEY)
    # updater.start_polling()
    updater.idle()


# Run the bot until you press Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.


# storing of data into database using sqlite
# not sure if check_same_thread=False will cause any problems
# https://www.youtube.com/watch?v=pd-0G0MigUA&t=1566s&ab_channel=CoreySchafer


# converts google sheet url link to google sheets csv download url, requires user_input of the google sheets url link
# and sheet name
# https://stackoverflow.com/questions/33713084/download-link-for-google-spreadsheets-csv-export-with-multiple-sheets
def url_converter(user_input):
    url_and_sheet_name = user_input.split()
    sheets_url = url_and_sheet_name[0]
    key = sheets_url.split("/")[5]
    sheet_name = url_and_sheet_name[1]
    return f"https://docs.google.com/spreadsheets/d/{key}/gviz/tq?tqx=out:csv&sheet={sheet_name}"


# reading excel sheet that is passed into the program using pandas
# https://www.youtube.com/watch?v=vmEHCJofslg&t=453s&ab_channel=KeithGalli
def store_url(sheets_url):
    with conn:
        c.execute(f"""CREATE TABLE IF NOT EXISTS url (
                    user_id,
                    sheets_url
                    )""")
        c.execute(f"INSERT OR REPLACE INTO url (user_id, sheets_url) VALUES (:user_id, :sheets_url)",
                  {'user_id': user_id, 'sheets_url': sheets_url})
    update_SQL()


def store_header(query_list_headers):
    headers_string = ', '.join(query_list_headers)
    with conn:
        c.execute(f"""CREATE TABLE IF NOT EXISTS header (
                        user_id,
                        headers
                        )""")
        c.execute(f"INSERT OR REPLACE INTO header (user_id, headers) VALUES (:user_id, :headers)",
                  {'user_id': user_id, 'headers': headers_string})
    c.execute("SELECT * FROM header")


# dataframe needs to be converted to string in order to be printed as a message. Everytime /workout is called,
# sheets will be re-passed into the database so as to get latest updates
def get_workout_by_date(date):
    update_SQL()
    c.execute(f"SELECT headers from header WHERE user_id=:user_id", {'user_id': user_id})
    sentence = ""
    for header_string in c.fetchall():
        for string in header_string:
            sentence += string
    sentence_list = sentence.split(", ")
    c.execute(f"SELECT {sentence} FROM '{user_id}' WHERE date=:date", {'date': date})
    df_from_db = pd.DataFrame(data=c.fetchall(), index=None, columns=sentence_list)
    return df_from_db


def update_SQL():
    c.execute(f"SELECT sheets_url FROM url WHERE user_id=:user_id", {'user_id': user_id})
    df = []
    for url_line in c.fetchall():
        url_unread = urllib.request.urlopen(url_line[0])
        url_read = [l.decode('utf-8') for l in url_unread.readlines()]
        df_csv = pd.DataFrame(data=csv.reader(url_read), index=None)
        df_csv.columns = df_csv.iloc[0]
        df = df_csv[1:]
        nan_value = float("NaN")
        df.replace("", nan_value, inplace=True)
        df_updated = df.dropna(how="all", axis=1)
        df_updated.fillna(method='ffill', inplace=True)
        df_updated.to_sql(user_id, conn, if_exists='replace', index=False)


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


# inputing excel sheet into sqlite database
# https://towardsdatascience.com/turn-your-excel-workbook-into-a-sqlite-database-bc6d4fd206aa

# google sheets download link for csv file
# cmphttps://stackoverflow.com/questions/33713084/download-link-for-google-spreadsheets-csv-export-with-multiple-sheets

# reading csv_file from urllib
# https://stackoverflow.com/questions/16283799/how-to-read-a-csv-file-from-a-url-with-python/62614979#62614979


if __name__ == '__main__':
    main()

# https://stackoverflow.com/questions/7831371/is-there-a-way-to-get-a-list-of-column-names-in-sqlite/7831685
# mapping column headers of sql table