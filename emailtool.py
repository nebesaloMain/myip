import smtplib
import random
import dotenv
import os

from email.mime.text import MIMEText

# Load env variables
dotenv.load_dotenv()

def send_email(to:str):

    code = "".join([str(random.randint(0,9)) for x in range(6)])

    msg = MIMEText(f'Код для подтверждения электронной почты для аккаунта в системе заявлений СЕГАЛ: {code}')
    msg['Subject'] = "Подтвердите свой Email"
    msg['From'] = os.getenv("EMAIL")
    msg['To'] = to

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(os.getenv("EMAIL"), os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)
    return code
