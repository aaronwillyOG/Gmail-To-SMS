import imaplib
import email
from email.header import decode_header
from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv()


# -------------------- CONFIGURATION --------------------
EMAIL_USER = os.environ['EMAIL_USER']       # Your Gmail (e.g., you@gmail.com)
EMAIL_PASS = os.environ['EMAIL_PASS']       # App Password (not your Gmail password)
IMAP_SERVER = "imap.gmail.com"

TWILIO_SID = os.environ['TWILIO_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_FROM = os.environ['TWILIO_FROM']
TWILIO_TO = os.environ['TWILIO_TO']

# -------------------- CONNECT TO GMAIL --------------------
def connect_to_mailbox():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    return mail

# -------------------- FETCH UNREAD EMAILS --------------------
def fetch_unread_emails(mail, max_count=3):
    status, messages = mail.search(None, '(UNSEEN)')
    email_ids = messages[0].split()[-max_count:]
    emails = []
    for eid in email_ids:
        _, msg_data = mail.fetch(eid, "(RFC822)")
        raw_msg = email.message_from_bytes(msg_data[0][1])

        subject, _ = decode_header(raw_msg["Subject"])[0]
        from_ = raw_msg.get("From")
        snippet = ""

        if raw_msg.is_multipart():
            for part in raw_msg.walk():
                if part.get_content_type() == "text/plain":
                    snippet = part.get_payload(decode=True).decode(errors="ignore")[:160]
                    break
        else:
            snippet = raw_msg.get_payload(decode=True).decode(errors="ignore")[:160]

        emails.append({
            "from": from_,
            "subject": subject if isinstance(subject, str) else subject.decode(),
            "snippet": snippet.strip()
        })
    return emails

# -------------------- SEND SMS --------------------
def send_sms(message):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=TWILIO_FROM,
        to=TWILIO_TO
    )

# -------------------- MAIN --------------------
if __name__ == "__main__":
    try:
        mail = connect_to_mailbox()
        unread_emails = fetch_unread_emails(mail)
        for email_data in unread_emails:
            sms_text = f"Email from {email_data['from']} - {email_data['subject']}\n{email_data['snippet']}"
            send_sms(sms_text)
            print("SMS sent:", sms_text)
    except Exception as e:
        print("Error:", e)
