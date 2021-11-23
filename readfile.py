import sqlite3
import pandas as pd
from telegram import Update
import os


# storing of data into database using sqlite
# not sure if check_same_thread=False will cause any problems
# https://www.youtube.com/watch?v=pd-0G0MigUA&t=1566s&ab_channel=CoreySchafer
conn = sqlite3.connect(':memory:', check_same_thread=False)
c = conn.cursor()


# reading excel sheet that is passed into the program using pandas
# https://www.youtube.com/watch?v=vmEHCJofslg&t=453s&ab_channel=KeithGalli
if Update.message.document is True:
    user_id = Update.message.from_user['id']
    df_xlsx = pd.read_excel(f'{user_id}', header=0)
    print(df_xlsx)
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
        df_xlsx.to_sql(f'{user_id}', conn, if_exists='append', index=False)

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
