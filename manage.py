from threading import Thread
import os
from sys import platform


def sturtup_client_bot():
    if platform == "linux" or platform == "linux2":
        os.system("python3 ./res/main.py")
    elif platform == "win32":
        os.system("python ./res/main.py")


def sturtup_admin_bot():
    if platform == "linux" or platform == "linux2":
        os.system("python3 ./res/admin_bot.py")
    elif platform == "win32":
        os.system("python ./res/admin_bot.py")


# os.system("pip install -r requirements.txt")

client = Thread(target=sturtup_client_bot)
client.start()

admin = Thread(target=sturtup_admin_bot)
admin.start()
