from openai import OpenAI
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding(text, model="text-embedding-3-large"):
    """
    Get embedding for a given text using the specified model.
    """
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def create_embeddings_from_file(
    input_file, output_file, model="text-embedding-3-large"
):
    """
    Create embeddings for each line in the input text file and save to a CSV file.
    """
    # Read the input file
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Create embeddings for each line
    embeddings = []
    for line in lines:
        embedding = get_embedding(line.strip(), model=model)
        embeddings.append(embedding)

    # Create a DataFrame to store the embeddings
    df = pd.DataFrame(embeddings)

    # Save the DataFrame to a CSV file
    df.to_csv(output_file, index=False)


# Example usage
input_file = "emails.txt"
output_file = "embeddings.csv"
create_embeddings_from_file(input_file, output_file)
