import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Account credentials
username = os.getenv("EMAIL_USERNAME")
password = os.getenv("EMAIL_PASSWORD")

# Create an IMAP4 class with SSL
imap = imaplib.IMAP4_SSL("imap.gmail.com")

# Authenticate
imap.login(username, password)

# Select the mailbox you want to use
imap.select("INBOX")

# Search for specific emails by criteria
status, messages = imap.search(None, "ALL")

# Convert messages to a list of email IDs
email_ids = messages[0].split()


# Function to clean the email content
def clean_email_body(body):
    soup = BeautifulSoup(body, "html.parser")
    for style in soup(["style"]):
        style.decompose()
    return soup.get_text()


# Create a file to save the emails
with open("emails.txt", "w", encoding="utf-8") as f:
    # Iterate through the first 10 emails
    for email_id in email_ids[:10]:
        # Fetch the email message by ID
        status, msg_data = imap.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse a bytes email into a message object
                msg = email.message_from_bytes(response_part[1])
                # Decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # If it's a bytes, decode to str
                    subject = subject.decode(encoding if encoding else "utf-8")
                f.write(f"Subject: {subject}\n")
                # Email sender
                from_ = msg.get("From")
                f.write(f"From: {from_}\n")
                # If the email message is multipart
                if msg.is_multipart():
                    # Iterate over email parts
                    for part in msg.walk():
                        # Extract content type of email
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            # Get the email body
                            body = part.get_payload(decode=True).decode()
                            clean_body = clean_email_body(body)
                            f.write(f"Body: {clean_body}\n")
                        except:
                            pass
                else:
                    # Extract content type of email
                    content_type = msg.get_content_type()
                    # Get the email body
                    body = msg.get_payload(decode=True).decode()
                    clean_body = clean_email_body(body)
                    f.write(f"Body: {clean_body}\n")
                f.write("\n" + "=" * 50 + "\n\n")

# Close the connection and logout
imap.close()
imap.logout()
