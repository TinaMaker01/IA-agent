"""Build the local Chroma vector store from files in ./knowledge."""

import os
import logging
from typing import List
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")
PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chromadb")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
EMBEDDING_MODEL = "text-embedding-v3"

def build_vector_store() -> None:
    """Load documents, split them into chunks, and save to a Chroma vector store."""
    if not os.path.exists(KNOWLEDGE_DIR):
        logger.error(f"Knowledge directory not found: {KNOWLEDGE_DIR}")
        return

    logger.info(f"Loading documents from {KNOWLEDGE_DIR}...")
    loader = DirectoryLoader(
        KNOWLEDGE_DIR,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()
    logger.info(f"Loaded {len(docs)} document(s)")

    if not docs:
        logger.warning("No documents found to process.")
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ",", ".", "!", "?"],
    )
    chunks = text_splitter.split_documents(docs)
    logger.info(f"Split into {len(chunks)} chunk(s)")

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("DASHSCOPE_API_KEY environment variable is not set.")
        return

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=BASE_URL,
        api_key=api_key,
    )

    logger.info(f"Creating vector store in {PERSIST_DIR}...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
    )
    logger.info("Vector store saved successfully.")

if __name__ == "__main__":
    build_vector_store()
