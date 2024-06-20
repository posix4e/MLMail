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
print("Loaded credentials for:", username)  # Print to confirm credential loading

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


# Function to clean the email content
def clean_email_body(body):
    soup = BeautifulSoup(body, "html.parser")
    for style in soup(["style"]):
        style.decompose()
    cleaned_text = soup.get_text()
    print("Cleaned email body.")
    return cleaned_text


# Create a file to save the emails
with open("emails.txt", "w", encoding="utf-8") as f:
    # Iterate through the first 10 emails
    for email_id in email_ids[:10]:
        print(f"Processing email ID: {email_id}")
        # Fetch the email message by ID
        status, msg_data = imap.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse a bytes email into a message object
                msg = email.message_from_bytes(response_part[1])
                # Decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # If it's a bytes type, decode to str
                    subject = subject.decode(encoding if encoding else "utf-8")
                f.write(f"Subject: {subject}\n")
                print(f"Subject: {subject}")
                # Email sender
                from_ = msg.get("From")
                f.write(f"From: {from_}\n")
                print(f"From: {from_}")
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
                        except Exception as e:
                            print("Failed to process part:", e)
                else:
                    # Extract content type of email
                    content_type = msg.get_content_type()
                    # Get the email body
                    body = msg.get_payload(decode=True).decode()
                    clean_body = clean_email_body(body)
                    f.write(f"Body: {clean_body}\n")
                f.write("\n" + "=" * 50 + "\n\n")
        print("Email processed and saved.")

# Close the connection and logout
imap.close()
imap.logout()
print("IMAP connection closed and logged out.")
