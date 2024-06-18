import os
import psycopg2
import pandas as pd
import numpy as np
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

# Load environment variables from .env file
load_dotenv()

# Get API keys and connection strings
connection_string = os.getenv("TIMESCALE_CONNECTION_STRING")

# Connect to PostgreSQL database
conn = psycopg2.connect(connection_string)
cur = conn.cursor()

# Install pgvector extension if not already installed
cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
conn.commit()

# Register pgvector
register_vector(conn)


# Function to clean the text content
def clean_text_content(text):
    soup = BeautifulSoup(text, "html.parser")
    for style in soup(["style"]):
        style.decompose()
    return soup.get_text()


# Function to read and clean content from a .txt file
def read_and_clean_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
    cleaned_text = clean_text_content(text)
    return cleaned_text


# Helper function: calculate number of tokens
def num_tokens_from_string(string: str, encoding_name="cl100k_base") -> int:
    if not string:
        return 0
    encoding = openai.Encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


# Load the OpenAI Embedding class
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=1024)

# Read and clean text from the .txt file
file_path = "input.txt"  # Replace with your .txt file path
cleaned_text = read_and_clean_file(file_path)

# Create new list with small content chunks to not hit max token limits
new_list = []
token_len = num_tokens_from_string(cleaned_text)
if token_len <= 512:
    new_list.append(["Title", cleaned_text, "URL", token_len])
else:
    start = 0
    ideal_token_size = 512
    ideal_size = int(ideal_token_size // (4 / 3))
    end = ideal_size
    words = cleaned_text.split()
    words = [x for x in words if x != " "]
    total_words = len(words)
    chunks = total_words // ideal_size
    if total_words % ideal_size != 0:
        chunks += 1
    for j in range(chunks):
        if end > total_words:
            end = total_words
        new_content = words[start:end]
        new_content_string = " ".join(new_content)
        new_content_token_len = num_tokens_from_string(new_content_string)
        if new_content_token_len > 0:
            new_list.append(["Title", new_content_string, "URL", new_content_token_len])
        start += ideal_size
        end += ideal_size

# Create embeddings for each piece of content
for i in range(len(new_list)):
    text = new_list[i][1]
    embedding = embeddings.embed_documents([text])[0]
    new_list[i].append(embedding)

# Create a new dataframe from the list
df_new = pd.DataFrame(
    new_list, columns=["title", "content", "url", "tokens", "embeddings"]
)

# Batch insert embeddings and metadata into PostgreSQL database
data_list = [
    (
        row["title"],
        row["url"],
        row["content"],
        int(row["tokens"]),
        np.array(row["embeddings"]),
    )
    for index, row in df_new.iterrows()
]
execute_values(
    cur,
    "INSERT INTO embeddings (title, url, content, tokens, embedding) VALUES %s",
    data_list,
)
conn.commit()


# Function to get top 3 most similar documents from the database
def get_top3_similar_docs(query_embedding, conn):
    embedding_array = np.array(query_embedding)
    cur = conn.cursor()
    cur.execute(
        "SELECT content FROM embeddings ORDER BY embedding <=> %s LIMIT 3",
        (embedding_array,),
    )
    top3_docs = cur.fetchall()
    return top3_docs


# Helper function: get text completion from OpenAI API
def get_completion_from_messages(
    messages, model="gpt-3.5-turbo-0613", temperature=0, max_tokens=1000
):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]


# Function to process input with retrieval of most similar documents from the database
def process_input_with_retrieval(user_input):
    delimiter = "```"
    related_docs = get_top3_similar_docs(embeddings.embed_query(user_input), conn)
    system_message = """
    You are a friendly chatbot. \
    You can answer questions about timescaledb, its features and its use cases. \
    You respond in a concise, technically credible tone.
    """
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{user_input}{delimiter}"},
        {
            "role": "assistant",
            "content": f"Relevant Timescale case studies information: \n {related_docs[0][0]} \n {related_docs[1][0]} {related_docs[2][0]}",
        },
    ]
    final_response = get_completion_from_messages(messages)
    return final_response


# Example usage
input_question = "How is Timescale used in IoT?"
response = process_input_with_retrieval(input_question)
print("User input:", input_question)
print("Model response:", response)

input_question_2 = "Tell me about Edeva and Hopara. How do they use Timescale?"
response_2 = process_input_with_retrieval(input_question_2)
print("User input:", input_question_2)
print("Model response:", response_2)
