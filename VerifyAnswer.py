from langchain_google_genai import GoogleGenerativeAI

def verify_answer(text_answer, query):
    llm = GoogleGenerativeAI(model="gemini-pro")
    verification_prompt = f"""
    Question: {query}
    Answer: {text_answer}

    Verify if the answer correctly and completely addresses the question.
    Respond with ONLY 'Yes' if the answer is correct and complete, or 'No' if it's incorrect or incomplete.
    Your response should be a single word: Yes or No.
    """
    response = llm.invoke(verification_prompt)
    return response
