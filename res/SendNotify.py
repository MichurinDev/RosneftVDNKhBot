from notifiers import get_notifier


def send_notify(token: str, msg: str, chatId: int):
    telegram = get_notifier('telegram')
    telegram.notify(
        token=token,
        chat_id=chatId,
        message=msg)
