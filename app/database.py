import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()


def connect_db():
    """Establish a connection to the database."""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def update_email_tracking(owner_email, new_message_ids):
    """Update the database with new unique message IDs, avoiding duplicates."""
    with connect_db() as conn:
        with conn.cursor() as cur:
            # Check if there is an existing record for the owner_email
            cur.execute(
                "SELECT message_ids FROM email_tracking WHERE owner_email = %s",
                (owner_email,),
            )
            result = cur.fetchone()

            if result:
                # Fetch the existing message_ids and prepare to update
                existing_ids = result[0]
                # Filter new_message_ids to include only those not in existing_ids
                unique_new_ids = [
                    msg_id for msg_id in new_message_ids if msg_id not in existing_ids
                ]

                if unique_new_ids:
                    # Update the record with new unique IDs only
                    cur.execute(
                        """
                        UPDATE email_tracking
                        SET message_ids = array_cat(message_ids, %s)
                        WHERE owner_email = %s;
                        """,
                        (unique_new_ids, owner_email),
                    )
            else:
                # Insert a new record if none exists
                cur.execute(
                    """
                    INSERT INTO email_tracking (owner_email, message_ids)
                    VALUES (%s, %s);
                    """,
                    (owner_email, new_message_ids),
                )
            conn.commit()


def message_id_exists(owner_email, message_id):
    """Check if a specific message ID already exists for a given owner."""
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT message_ids FROM email_tracking WHERE owner_email = %s;
                """,
                (owner_email,),
            )
            result = cur.fetchone()
            if result:
                # Check if the message_id is in the retrieved list of message IDs
                return message_id in result[0]
            return False
