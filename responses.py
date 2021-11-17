from datetime import datetime


def sample_response(input_text):
    user_message = str(input_text).lower()

    if user_message in ("hello", "hey", "yo"):
        return "Yo!"

    if user_message in ("what is the time?", "time", "time?"):
        now = datetime.now()
        date_time = now.strftime("%d/%m/%y, %H:%M:%S")
        return date_time

    return "I don't understand you."
