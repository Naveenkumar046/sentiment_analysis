from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

openai_api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)

intent_prompt = PromptTemplate(
    input_variables=["query"],
    template="""
        Classify the user's query into one of the following intents:
        - rag: For questions about policies, searches, knowledge-based queries requiring deep research from documents or knowledge graphs.
        - Knowledge graph: For queries about relationships, entities, or graph-based data.
        - sql: For queries about prices, offers, products, or any relational data from databases.
        - incident: For queries about incidents, files, data from Jira, SharePoint, or OpenSearch.
        - general: For plain general questions that don't fit the above categories.

        Query: {query}

        Intent:
        """
)

intent_chain = LLMChain(llm=llm, prompt=intent_prompt)

def classify_intent(query):
    response = intent_chain.run(query=query).strip().lower()
    
    if "rag" in response:
        return "rag"
    elif "sql" in response:
        return "sql"
    elif "incident" in response:
        return "incident"
    elif "knowledge graph" in response:
        return "knowledge graph"
    else:
        return "general"