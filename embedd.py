import os
import psycopg2
from openai import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()  # This loads environment variables from the .env file
client = OpenAI()


def chunk_text(file_path, chunk_size=8000, chunk_overlap=200):
    """
    Read and chunk the text from the file.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)


def generate_and_save_embeddings(chunks, db_config):
    """
    Generate embeddings for each chunk of text and save to the database.
    """
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            id SERIAL PRIMARY KEY,
            text_chunk TEXT,
            embedding vector(3072)  -- Adjust dimension if needed
        );
        """
    )

    model_name = os.getenv("OPENAI_MODEL", "text-embedding-3-large")

    for chunk in chunks:
        embedding = client.embeddings.create(
            input=chunk, model=model_name, dimensions=3072
        )

        embedding_vector = embedding.data[0].embedding
        cursor.execute(
            "INSERT INTO embeddings (text_chunk, embedding) VALUES (%s, %s)",
            (chunk, embedding_vector),
        )

    conn.commit()
    cursor.close()
    conn.close()


def process_and_store_embeddings(file_path, db_config):
    """
    Process the text file and store embeddings in the database.
    """
    chunks = chunk_text(file_path)
    print(f"Number of chunks: {len(chunks)}")
    generate_and_save_embeddings(chunks, db_config)


if __name__ == "__main__":
    db_config = {
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
    }
    file_path = "emails.txt"
    process_and_store_embeddings(file_path, db_config)
