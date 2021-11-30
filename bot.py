import datetime
import os
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler
import telegram
from telegram import Update
import logging
import sqlite3
import pandas as pd
import csv
import urllib.request


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


def start_command(update: Update, context: CallbackContext):
    text = """
Welcome to Jun's Iron Church telegram bot!

In order to begin: 
1. Create a google excel sheet with your workout program in the format of this following document: 
https://docs.google.com/spreadsheets/d/19wwdOS01lprzKgXXtZZ_bVM7bGJc9STpaaPnUQiEtFw/edit#gid=0.
3. Save and change permission for anyone with the link to be able to view.
2. Send a message to this telegram bot in this following format:
your_google_sheets_url (your_sheet_name)
e.g. https://docs.google.com/spreadsheets/d/19wwdOS01lprzKgXXtZZ_bVM7bGJc9STpaaPnUQiEtFw/edit#gid=0 (Sheet1)
3. Type /workout to receive the exercises you are to be doing today!
4. Lastly, begin praying at the Iron Church!
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("Lame...")


def workout_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user['id']
    text = f"```{get_workout_by_date(str(datetime.date.today().strftime('%d/%m/%Y')), user_id)}```"
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)


def handle_message(update: Update, context: CallbackContext):
    user_input = update.message.text
    sheets_url = url_converter(user_input)
    user_id = update.message.from_user['id']
    store_url(sheets_url, user_id)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"I have received your Google Sheets! This is your user_id: {user_id}")


# Google Sheets url to csv file
# https://stackoverflow.com/questions/33713084/download-link-for-google-spreadsheets-csv-export-with-multiple-sheets
# https://docs.google.com/spreadsheets/d/{key}/gviz/tq?tqx=out:csv&sheet={sheet_name}


def error(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")
    try:
        # if str(context.error) == 'list index out of range' and update.message.text.split("/")[6] is True:
        #     context.bot.send_message(chat_id=update.effective_chat.id, text="Please input a sheet name.")
        if str(context.error) == 'list index out of range' and 'https://' in update.message.text:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Please input a valid URL and sheet name.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Type /start to get started.")
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="I do not understand.")


def main():
    updater = Updater(token=API_KEY, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("workout", workout_command))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    dp.add_error_handler(error)
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=API_KEY)
    updater.bot.setWebhook('https://pure-chamber-09599.herokuapp.com/' + API_KEY)
    updater.idle()


# Run the bot until you press Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.


# storing of data into database using sqlite
# not sure if check_same_thread=False will cause any problems
# https://www.youtube.com/watch?v=pd-0G0MigUA&t=1566s&ab_channel=CoreySchafer


conn = sqlite3.connect('main.db', check_same_thread=False)
c = conn.cursor()


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
def store_url(sheets_url, user_id):
    with conn:
        c.execute(f"""CREATE TABLE IF NOT EXISTS url (
                    user_id,
                    sheets_url
                    )""")
        c.execute(f"INSERT OR REPLACE INTO url VALUES (:user_id, :sheets_url)",
                  {'user_id': user_id, 'sheets_url': sheets_url})


# dataframe needs to be converted to string in order to be printed as a message. Everytime /workout is called,
# sheets will be re-passed into the database so as to get latest updates
def get_workout_by_date(date, user_id):
    c.execute(f"SELECT sheets_url FROM url WHERE (:user_id)", {'user_id': user_id})
    for url_line in c.fetchall():
        url_unread = urllib.request.urlopen(url_line[0])
        url_read = [l.decode('utf-8') for l in url_unread.readlines()]
        df_csv = pd.DataFrame(data=csv.reader(url_read), index=None,
                              columns=['ID', 'Date', 'Day', 'Week', 'Exercise', 'Sets', 'Intensity', 'Reps', 'Load',
                                       'Tempo', 'Rest'])
        with conn:
            c.execute(f"""CREATE TABLE IF NOT EXISTS '{user_id}' (
                        ID,
                        Date,
                        Day,
                        Week,
                        Exercise,
                        Sets,
                        Reps,
                        Intensity,
                        Load,
                        Tempo,
                        Rest
                        )""")
            df_csv.to_sql(f'{user_id}', conn, if_exists='replace', index=False)
    c.execute(f"SELECT Exercise, Sets, Reps, Load, Tempo, Rest FROM '{user_id}' WHERE date=:date", {'date': date})
    df_from_db = pd.DataFrame(data=c.fetchall(), index=None,
                              columns=['Exercise', 'Sets', 'Reps', 'Load', 'Tempo', 'Rest'])
    return df_from_db.to_string(index=False)


# url = 'http://winterolympicsmedals.com/medals.csv'
# response = urllib.request.urlopen(url)
# lines = [l.decode('utf-8') for l in response.readlines()]
# cr = pd.DataFrame(data=csv.reader(lines), index=None)
# print(cr)

# inputing excel sheet into sqlite database
# https://towardsdatascience.com/turn-your-excel-workbook-into-a-sqlite-database-bc6d4fd206aa

# google sheets download link for csv file
# cmphttps://stackoverflow.com/questions/33713084/download-link-for-google-spreadsheets-csv-export-with-multiple-sheets

# reading csv_file from urllib
# https://stackoverflow.com/questions/16283799/how-to-read-a-csv-file-from-a-url-with-python/62614979#62614979


if __name__ == '__main__':
    main()
