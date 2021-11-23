import sqlite3
import pandas as pd
from telegram import Update
import os


# storing of data into database using sqlite
# not sure if check_same_thread=False will cause any problems
# https://www.youtube.com/watch?v=pd-0G0MigUA&t=1566s&ab_channel=CoreySchafer
conn = sqlite3.connect('test1.db', check_same_thread=False)
c = conn.cursor()


# reading excel sheet that is passed into the program using pandas
# https://www.youtube.com/watch?v=vmEHCJofslg&t=453s&ab_channel=KeithGalli
def create_table(csv_file):
    if Update.message is True:
        try:
            user_id = Update.message.from_user['id']
            print(csv_file)
            # Updates sql database from xlsx
            with conn:
                c.execute(f"""CREATE TABLE IF NOT EXISTS {user_id} (
                            Exercise,
                            Sets,
                            Reps,
                            Intensity,
                            Load,
                            Tempo,
                            Rest
                            )""")
                csv_file.to_sql(f'{user_id}', conn, if_exists='append', index=False)
        finally:
            pass
    else:
        pass


# dataframe needs to be converted to string in order to be printed as a message
def get_workout_by_date(date):
    user_id = Update.message.from_user['id']
    c.execute(f"SELECT Exercise, Sets, Reps, Load, Tempo, Rest FROM {user_id} WHERE date=:date", {'date': date})
    df = pd.DataFrame(data=c.fetchall(), index=None, columns=['Exercise', 'Sets', 'Reps', 'Load', 'Tempo', 'Rest'])
    return df.to_string(index=False)


# inputing excel sheet into sqlite database
# https://towardsdatascience.com/turn-your-excel-workbook-into-a-sqlite-database-bc6d4fd206aa
