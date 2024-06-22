# Email Embedding and Retrieval System

This project provides a tool for processing large text files (specifically emails), generating embeddings for each text chunk, and storing these embeddings in a PostgreSQL database. It also includes functionality to handle user queries by retrieving the most relevant text chunks based on their embeddings and generating responses using OpenAI's GPT models.

## Features

- **Text Chunking**: Splits large text files into manageable chunks.
- **Embedding Generation**: Generates embeddings for each text chunk using OpenAI's embedding models.
- **Database Storage**: Stores text chunks and their embeddings in a PostgreSQL database.
- **Query Retrieval**: Retrieves text chunks relevant to a user query based on cosine similarity of embeddings.
- **Chat Response Generation**: Utilizes OpenAI's chat completion models to generate responses from retrieved text data.
- **Automatic Email Processing**: Automatically fetches and processes emails every 30 minutes.
- **Interactive Chat Interface**: Provides a web interface for real-time interaction with the system.

## Prerequisites

Before you can run this project, you'll need to have the following installed:

- Python 3.8 or higher
- PostgreSQL
- OpenAI API access
- Python packages: `psycopg2`, `dotenv`, `openai`, `flask`, `apscheduler`

## Setup

### Environment Variables

Create a `.env` file in the root directory of your project with the following environment variables:

```plaintext
EMAIL_USERNAME=your_email
EMAIL_PASSWORD=your_email_pass
OPENAI_API_KEY=your_openai_api_key
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=your_database_port
OPENAI_EMBEDDINGS_MODEL=your_preferred_openai_embedding_model
OPENAI_CHAT_MODEL=your_preferred_openai_chat_model
```

### Database Setup

Ensure your PostgreSQL database is set up with the necessary extensions and schemas:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    text_chunk TEXT,
    embedding vector(3072)
);

-- Create a table for tracking which emails have been processed
CREATE TABLE IF NOT EXISTS email_tracking (
    owner_email VARCHAR(255) PRIMARY KEY,
    message_ids TEXT[]  -- Array of message IDs processed by the owner
);
```

### Install Dependencies

Install the necessary Python packages by running:

```bash
pip install -r requirements.txt
```

## Usage

Run the Flask application with the command below to start the server and enable both scheduled tasks and real-time chat functionality:

```bash
python app.py
```

This command runs the Flask server which manages fetching emails, processing embeddings, and handling user queries via a web interface.

## Project Structure

Below is an overview of the main components of the project:

- `app.py`: The Flask application server managing all components.
- `chat.py`: Handles user queries, retrieves relevant chunks from the database, and generates responses using OpenAI's chat model.
- `embedd.py`: Responsible for processing text files, generating embeddings, and storing them in the PostgreSQL database.
- `get_emails.py`: Script to fetch and preprocess email data.
- `requirements.txt`: Lists all the Python dependencies required for the project, which can be installed via `pip`.
- `templates/`: Folder containing HTML templates for the Flask app.

## Web Interface

Access the web interface by navigating to `http://localhost:5000` in your web browser after starting the Flask server. This interface allows you to interact with the chat system in real-time.
