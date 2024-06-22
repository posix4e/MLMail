from flask import Flask, request, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import os
from embedd import process_and_store_embeddings
from get_emails import fetch_and_process_emails
from chat import answer_query_in_chat

app = Flask(__name__)

# Load database configuration from environment variables
db_config = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

# File path where emails are saved
file_path = "emails.txt"


def fetch_and_embed():
    """Fetch emails and then start embedding process after fetching is complete."""
    fetch_thread = threading.Thread(target=fetch_and_process_emails)
    fetch_thread.start()
    fetch_thread.join()  # Wait for the fetching process to complete
    process_and_store_embeddings(file_path, db_config)  # Start embedding after fetching


# Set up scheduler to fetch emails and then process embeddings every 30 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_and_embed, trigger="interval", minutes=30)
scheduler.start()

# Fetch and process emails immediately and periodically on server start without blocking
threading.Thread(target=fetch_and_embed).start()


@app.route("/")
def index():
    """Serve the chat interface."""
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat queries from the HTML interface."""
    user_query = request.form["query"]
    response = answer_query_in_chat(user_query, db_config)
    return jsonify(response)


@app.route("/fetch_emails", methods=["POST"])
def fetch_emails():
    """Endpoint to manually trigger email fetching and processing."""
    fetch_thread = threading.Thread(target=fetch_and_process_emails)
    fetch_thread.start()
    fetch_thread.join()  # Ensure fetching finishes before sending response
    return jsonify({"status": "Emails fetched and processing started"})


@app.route("/process_embeddings", methods=["POST"])
def process_embeddings():
    """Endpoint to manually trigger processing and storing embeddings."""
    embed_thread = threading.Thread(
        target=lambda: process_and_store_embeddings(file_path, db_config)
    )
    embed_thread.start()
    return jsonify({"status": "Embedding process started"})


if __name__ == "__main__":
    app.run(debug=True)
