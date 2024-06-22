import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from database import connect_db, update_email_tracking, message_id_exists


def fetch_and_process_emails():
    load_dotenv()

    # Account credentials
    username = os.getenv("EMAIL_USERNAME")
    password = os.getenv("EMAIL_PASSWORD")
    print("Loaded credentials for:", username)

    # Create an IMAP4 class with SSL
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    print("Connected to IMAP server.")

    # Authenticate
    imap.login(username, password)
    print("Logged in with username:", username)

    # Select the mailbox you want to use
    imap.select("INBOX")
    print("Mailbox selected: INBOX")

    # Search for specific emails by criteria
    status, messages = imap.search(None, "ALL")
    print(f"Search completed with status: {status}")

    # Convert messages to a list of email IDs
    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} emails.")

    processed_ids = []  # List to track new message IDs that were actually processed

    def clean_email_body(body):
        soup = BeautifulSoup(body, "html.parser")
        for style in soup(["style"]):
            style.decompose()
        cleaned_text = soup.get_text()
        print("Cleaned email body.")
        return cleaned_text

    with open("emails.txt", "w", encoding="utf-8") as f:
        for email_id in email_ids[:20]:
            status, msg_data = imap.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    message_id = msg.get("Message-ID")
                    if message_id and message_id_exists(username, message_id):
                        print(
                            f"Skipping email with Message-ID: {message_id} as it already exists in the database."
                        )
                    elif message_id:
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        email_date = msg.get("Date")
                        formatted_date = (
                            parsedate_to_datetime(email_date).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            if email_date
                            else "Unknown Date"
                        )

                        f.write(f"Date: {formatted_date}\n")
                        f.write(f"Subject: {subject}\n")
                        f.write(f"From: {msg.get('From')}\n")

                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() in [
                                    "text/plain",
                                    "text/html",
                                ]:
                                    body = part.get_payload(decode=True).decode()
                                    clean_body = clean_email_body(body)
                                    f.write(f"Body: {clean_body}\n")
                        else:
                            body = msg.get_payload(decode=True).decode()
                            clean_body = clean_email_body(body)
                            f.write(f"Body: {clean_body}\n")
                        f.write("\n" + "=" * 50 + "\n\n")
                        processed_ids.append(message_id)
                        print(
                            f"Email with Message-ID: {message_id} processed and saved."
                        )

    update_email_tracking(username, processed_ids)
    imap.close()
    imap.logout()
    print("IMAP connection closed and logged out.")
