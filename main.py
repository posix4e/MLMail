import os
import argparse
import logging
from datetime import datetime, timedelta
from EmailFetcher import EmailFetcher
from EmailProcessor import load_emails
from RAGChain import create_text_embedding, create_rag_chain
from VerifyAnswer import verify_answer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_emails(email_directory):
    emails = load_emails(email_directory, limit=5)
    print(f"Number of emails loaded for processing: {len(emails)}")

    retriever = create_text_embedding(emails)
    rag_chain = create_rag_chain(retriever)

    query = "From whom these emails came from?"
    results = rag_chain({"input": query})

    text_answer = results["answer"]

    print(f"Query: {query}")
    print("\nInitial Answer:")
    print(text_answer)
    print("\nSource Emails:")
    for doc in results["source_documents"]:
        print(f"  Subject: {doc.metadata['subject']}")
        print(f"  From: {doc.metadata['from']}")
        print(f"  Date: {doc.metadata['date']}")
        print(f"  Content: {doc.page_content[:100]}...")
        print()

    verification_result = verify_answer(text_answer, query)
    print("\nVerification Result:", verification_result)

    if verification_result == "No":
        print("\nVerification failed. Please refine the question or check the email contents manually.")
    else:
        print("\nVerification succeeded. The answer is considered correct and complete.")

def main():
    parser = argparse.ArgumentParser(description="Fetch and process emails from an IMAP server.")
    parser.add_argument("--imap_url", default='imap.gmail.com', help="IMAP server URL")
    parser.add_argument("--max_emails", type=int, default=50, help="Maximum number of emails to fetch")
    parser.add_argument("--output_directory", default='my_emails', help="Directory to save emails")
    args = parser.parse_args()

    user = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')

    if not user or not password:
        logger.error("Missing EMAIL or PASSWORD environment variables.")
        exit(1)

    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    # Check if the email directory already contains emails
    existing_emails = [f for f in os.listdir(args.output_directory) if f.endswith('.txt')]
    if existing_emails:
        logger.info(f"Found {len(existing_emails)} existing emails in {args.output_directory}. Skipping download.")
    else:
        logger.info("No existing emails found. Proceeding to download emails.")
        fetcher = EmailFetcher(args.imap_url, user, password, args.output_directory)

        try:
            fetcher.connect()
            fetcher.select_mailbox()

            date_since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            search_criteria = ['SINCE', date_since]
            email_uids = fetcher.search_emails(search_criteria)

            logger.info(f"Found {len(email_uids)} emails from yesterday.")
            email_uids = email_uids[-args.max_emails:]

            successful_fetches = 0
            for uid in email_uids:
                try:
                    email_message = fetcher.fetch_email(uid)
                    if email_message:
                        fetcher.save_email(email_message, args.output_directory)
                        successful_fetches += 1
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error processing email with UID {uid}: {e}")

            logger.info(f"Successfully downloaded and saved {successful_fetches} out of {len(email_uids)} emails in the '{args.output_directory}' directory.")

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        finally:
            fetcher.disconnect()

    # Process the emails (whether they were just downloaded or already existed)
    process_emails(args.output_directory)

if __name__ == "__main__":
    main()
