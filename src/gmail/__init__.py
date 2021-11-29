import email
import imaplib
import os

from dotenv import load_dotenv

load_dotenv()


def get_inbox():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
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
