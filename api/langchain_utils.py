import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List
from langchain_core.documents import Document
from langchain_core.runnables import Runnable

from chroma_utils import vectorstore

# Load environment variables
load_dotenv()

# Set up GitHub-hosted OpenAI-compatible client
client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=os.environ["GITHUB_TOKEN"]
)

# Custom wrapper to make GitHub OpenAI model usable with LangChain
class GitHubChatLLM(Runnable):
    def __init__(self, model="openai/gpt-4o-mini", temperature=0.3, max_tokens=1024):
        self.client = OpenAI(
            base_url="https://models.github.ai/inference",
            api_key=os.environ["GITHUB_TOKEN"]
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def invoke(self, input, config=None):
        """
        Handles LangChain prompt input format:
        {
            "messages": [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."}
            ]
        }
        """
        # LangChain sends 'input' as {'messages': [...]}
        if isinstance(input, dict) and "messages" in input:
            messages = input["messages"]
        else:
            # fallback in case input is just text
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": str(input)}
            ]

        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content

# Use your existing retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
output_parser = StrOutputParser()

contextualize_q_system_prompt = (
    "You are an AI assistant that helps reformulate user questions for better understanding and retrieval.\n\n"
    "Given a chat history and the latest user query, your task is to rewrite the user's question as a standalone, complete question.\n"
    "The reformulated question should contain all necessary context from the conversation so it can be understood without referring to prior messages.\n\n"
    "Important:\n"
    "- Do NOT answer the question.\n"
    "- Only rewrite the question if needed. If it is already standalone, return it as-is.\n"
    "- Ensure the reformulated version is clear, specific, and self-contained."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

qa_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an intelligent and helpful AI assistant.\n\n"
        "When provided with context from documents, use it to answer the user's question if it's relevant.\n"
        "If the context is missing, unrelated, or doesn't help answer the question, rely on your own general knowledge.\n\n"
        "Guidelines:\n"
        "- If the question relates to the context, use it and summarize or cite as needed.\n"
        "- If not, feel free to answer directly based on what you know.\n"
        "- Do not refuse to answer unless you're truly unsure.\n"
        "- Be clear, helpful, and factually correct."
    ),
    ("system", "Context:\n{context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# Final chain constructor
def get_rag_chain(model="openai/gpt-4o-mini"):
    llm = GitHubChatLLM(model=model)
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain
