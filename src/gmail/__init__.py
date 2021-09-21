import email
import imaplib

from utils import config


def get_inbox():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(config.email_address, config.email_password)
    mail.select("inbox")

    _, search_data = mail.search(None, "UNSEEN")
    messages = []
    for num in search_data[0].split():
        email_data = {}
        _, data = mail.fetch(num, "(RFC822)")
        _, b = data[0]
        email_message = email.message_from_bytes(b)
        email_data['title'] = email_message['subject']
        messages.append(email_data)

    return messages
