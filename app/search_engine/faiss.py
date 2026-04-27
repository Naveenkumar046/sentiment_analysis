import os
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document

openai_api_key = os.getenv("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings(api_key=openai_api_key)
INDEX_PATH = os.getenv("INDEX_PATH")

def get_vectorstore():
    if os.path.exists(INDEX_PATH):
        return FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        # Initialize with a dummy doc if empty
        init_doc = [Document(page_content="Index Initialized", metadata={"source": "init"})]
        vectorstore = FAISS.from_documents(init_doc, embeddings)
        vectorstore.save_local(INDEX_PATH)
        return vectorstore

def store_rag(content, metadata):
    """Used by the CDC worker to update the index"""
    vectorstore = get_vectorstore()
    doc = Document(page_content=content, metadata=metadata)
    vectorstore.add_documents([doc])
    vectorstore.save_local(INDEX_PATH) # Persist changes
    print(f"Sync complete: {metadata.get('usecase')}")

def search_rag(query):
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=5)
    return "\n\n".join([f"Content: {d.page_content}\nMetadata: {d.metadata}" for d in docs])


def rag_tool(query: str) -> str:
    """Search the knowledge base using RAG for policies and general knowledge."""
    return search_rag(query)






