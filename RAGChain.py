from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

def create_text_embedding(docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    splits = text_splitter.split_documents(docs)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "include_metadata": True}
    )

def create_rag_chain(retriever):
    llm = GoogleGenerativeAI(model="gemini-pro")
    system_prompt = """
    You are an assistant for question-answering tasks. 
    Use the following pieces of retrieved context to answer the question about emails received recently.
    Analyze each of the emails and use relevant information to answer the user's query.
    Context: {context}
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    retrieval_chain = create_retrieval_chain(retriever, question_answer_chain)

    def wrapped_chain(input):
        result = retrieval_chain.invoke(input)
        return {
            "answer": result["answer"],
            "source_documents": result["context"]
        }

    return wrapped_chain
