# Email Embedding and Retrieval System

This project provides a tool for processing large text files (specifically emails), generating embeddings for each text chunk, and storing these embeddings in a PostgreSQL database. It also includes functionality to handle user queries by retrieving the most relevant text chunks based on their embeddings and generating responses using OpenAI's GPT models.

## Features

- **Text Chunking**: Splits large text files into manageable chunks.
- **Embedding Generation**: Generates embeddings for each text chunk using OpenAI's embedding models.
- **Database Storage**: Stores text chunks and their embeddings in a PostgreSQL database.
- **Query Retrieval**: Retrieves text chunks relevant to a user query based on cosine similarity of embeddings.
- **Chat Response Generation**: Utilizes OpenAI's chat completion models to generate responses from retrieved text data.

## Prerequisites

Before you can run this project, you'll need to have the following installed:

- Python 3.8 or higher
- PostgreSQL
- OpenAI API access
- Python packages: `psycopg2`, `dotenv`, `openai`

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
OPENAI_MODEL=your_preferred_openai_embedding_model
OPENAI_CHAT_MODEL=your_preferred_openai_chat_model
```

### Database Setup

Ensure your PostgreSQL database is set up with the `pgvector` extension for handling vector operations:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Install Dependencies

Install the necessary Python packages by running:

```bash
pip install -r requirements.txt
```

## Usage

To run the main processes of the project, you need to execute the individual Python scripts in this order:

```bash
python get_emails.py  # For fetching emails
python embedd.py  # For processing and embedding emails
python chat.py  # For handling and responding to user queries
```

This will process the specified text file, generate embeddings, store them in the database, and set up the environment for handling queries with AI-generated responses.

## Project Structure

Below is an overview of the main components of the project:

- `chat.py`: Handles user queries, retrieves relevant chunks from the database, and generates responses using OpenAI's chat model.
- `embedd.py`: Responsible for processing text files, generating embeddings, and storing them in the PostgreSQL database.
- `get_emails.py`: Script to fetch email data that will be processed.
- `requirements.txt`: Lists all the Python dependencies required for the project, which can be installed via `pip`.
