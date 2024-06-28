import os
import re
from langchain_core.documents import Document

def load_emails(directory, limit=None):
    emails = []
    for filename in sorted(os.listdir(directory), reverse=True):  # Sort to get latest emails first
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                content = file.read()
                subject = re.search(r"Subject: (.*)\n", content)
                sender = re.search(r"From: (.*)\n", content)
                date = re.search(r"Date: (.*)\n", content)
                body = content.split("Body:\n", 1)[1] if "Body:\n" in content else content

                emails.append(Document(
                    page_content=body,
                    metadata={
                        "subject": subject.group(1) if subject else "No subject",
                        "from": sender.group(1) if sender else "No sender",
                        "date": date.group(1) if date else "No date",
                        "filename": filename
                    }
                ))
                
                if limit and len(emails) >= limit:
                    break
    return emails
