import os
import time
import re
import socket
import email
import logging
from datetime import datetime, timedelta
from email.header import decode_header
from imapclient import IMAPClient
from imapclient.imapclient import SEEN
from backoff import on_exception, expo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailFetcher:
    def __init__(self, imap_url, user, password, output_directory):
        self.imap_url = imap_url
        self.user = user
        self.password = password
        self.output_directory = output_directory
        self.client = None

    @on_exception(expo, (socket.error, IMAPClient.Error), max_tries=5)
    def connect(self):
        try:
            self.client = IMAPClient(self.imap_url, use_uid=True, ssl=True)
            self.client.login(self.user, self.password)
            logger.info("Successfully connected to the IMAP server.")
        except Exception as e:
            logger.error(f"IMAP connection or login failed: {e}")
            raise

    def disconnect(self):
        if self.client:
            try:
                self.client.logout()
                logger.info("Successfully disconnected from the IMAP server.")
            except Exception as e:
                logger.error(f"Failed to logout from the server: {e}")

    def select_mailbox(self, mailbox='INBOX'):
        try:
            self.client.select_folder(mailbox)
            logger.info(f"Selected mailbox: {mailbox}")
        except Exception as e:
            logger.error(f"Failed to select mailbox {mailbox}: {e}")
            raise

    def search_emails(self, criteria):
        try:
            return self.client.search(criteria)
        except Exception as e:
            logger.error(f"Email search failed: {e}")
            raise

    @on_exception(expo, (socket.error, IMAPClient.Error), max_tries=3)
    def fetch_email(self, uid):
        try:
            header_data = self.client.fetch([uid], ['BODY[HEADER]'])
            if uid not in header_data:
                logger.warning(f"No header data returned for email with UID {uid}")
                return None

            email_message = email.message_from_bytes(header_data[uid][b'BODY[HEADER]'])

            body_data = self.client.fetch([uid], ['BODY[TEXT]'])
            if uid in body_data:
                email_message.set_payload(body_data[uid][b'BODY[TEXT]'])
            else:
                logger.warning(f"No body data returned for email with UID {uid}")

            self.client.add_flags([uid], [SEEN])

            return email_message
        except Exception as e:
            logger.error(f"Failed to fetch email with UID {uid}: {e}")
            return None

    @staticmethod
    def decode_email_subject(subject):
        decoded_subject, encoding = decode_header(subject)[0]
        if isinstance(decoded_subject, bytes):
            return decoded_subject.decode(encoding or 'utf-8', errors='ignore')
        return decoded_subject

    def save_email(self, email_message, output_directory):
        if email_message is None:
            return

        subject = self.decode_email_subject(email_message['subject']) if email_message['subject'] else 'No subject'
        sender = email_message['from'] if email_message['from'] else 'No sender'
        date = email_message['date'] if email_message['date'] else 'No date'

        safe_subject = re.sub(r'[^\w\-_\. ]', '_', subject)
        filename = f"{output_directory}/{safe_subject}_{int(time.time())}.txt"

        with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(f"Subject: {subject}\n")
            f.write(f"From: {sender}\n")
            f.write(f"Date: {date}\n")
            f.write("Body:\n")

            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == 'text/plain':
                        try:
                            decoded_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            f.write(decoded_content)
                            f.write("\n")
                        except Exception as decode_error:
                            logger.error(f"Failed to decode email content: {decode_error}")
            else:
                try:
                    decoded_content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                    f.write(decoded_content)
                except Exception as decode_error:
                    logger.error(f"Failed to decode email content: {decode_error}")

        logger.info(f"Saved email '{subject}' from '{sender}' to '{filename}'")
