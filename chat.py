import psycopg2
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


def get_query_embedding(query, model=None):
    """
    Generate embedding for the user query.
    """
    if model is None:
        model = os.getenv("OPENAI_MODEL", "text-embedding-3-large")
    response = client.embeddings.create(input=query, model=model, dimensions=3072)
    print(
        "Query Embedding:", len(response.data[0].embedding)
    )  # Print the embedding to see its structure
    return response.data[0].embedding


def retrieve_relevant_chunks(query_embedding, db_config, limit=5):
    """
    Retrieve the most relevant text chunks based on the query embedding.
    """
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Format the embedding as a PostgreSQL array-like string (e.g., [1.0,2.0,...])
    embedding_as_vector = "[" + ",".join(map(str, query_embedding)) + "]"
    print(
        "Formatted Embedding for SQL:", len(embedding_as_vector)
    )  # Verify the format before sending to SQL

    # Using pgvector's built-in KNN functionality, with proper vector formatting
    cursor.execute(
        """
        SELECT text_chunk
        FROM embeddings
        ORDER BY embedding <-> vector(%s)
        LIMIT %s;
        """,
        (embedding_as_vector, limit),
    )

    results = cursor.fetchall()
    print(
        "Retrieved Chunks Length:", len(results)
    )  # Print the retrieved chunks to check what is being fetched
    conn.close()
    return [result[0] for result in results]


def generate_chat_response(messages, model=None):
    """
    Generate a coherent response in a chat context using OpenAI's chat completions.
    """
    if model is None:
        model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
    response = client.chat.completions.create(model=model, messages=messages)
    print(
        "Chat Response:", response.choices[0].message.content
    )  # Print the generated response from the chat model
    return response.choices[0].message.content


def answer_query_in_chat(query, db_config):
    """
    Complete workflow to answer a user query in a chat-like interaction.
    """
    print(
        "Received Query:", query
    )  # Print the initial user query to see what is being processed

    # Step 1: Get query embedding
    query_embedding = get_query_embedding(query)

    # Step 2: Retrieve relevant chunks
    relevant_chunks = retrieve_relevant_chunks(query_embedding, db_config)

    # Step 3: Generate chat response using the retrieved chunks as context
    context_chunk = " ".join(relevant_chunks)
    print(
        "Context for Response Generation:", len(context_chunk)
    )  # Print the context being sent for response generation
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": query},
        {"role": "assistant", "content": context_chunk},
    ]
    response = generate_chat_response(messages)
    print("Final Response:", response)  # Print the final response to the user


if __name__ == "__main__":
    db_config = {
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
    }
    user_query = "Summarize these mails"
    answer_query_in_chat(user_query, db_config)
