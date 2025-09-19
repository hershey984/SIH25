from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .supervisor_models import AnalysisResult
from .supervisor_tools import get_user_location, fetch_contextual_data
from dotenv import load_dotenv
import os

load_dotenv()

def create_supervisor_chain():
    print("--- Creating Supervisory Agent Chain ---")

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a highly intelligent Supervisory AI agent for a smart farming application.
Analyze the user's query and return the following JSON object exactly in this structure:

{{
  "agent_required": "<crop_advisor | resource_manager | plant_doctor | general_query>",
  "query_for_next_agent": "<refined query for the selected agent>",
  "supporting_info": {{
     "agricultural_context": "<short context>",
     "market_context": "<short context>"
  }}
}}

Rules:
- Choose the most suitable agent.
- Always fill ALL fields.
- If 'crop_advisor' or 'resource_manager', call your tools to get context before answering.
- If 'plant_doctor', skip fetching context.
"""),
        ("user", "{query}")
    ])

    llm_with_tools = llm.bind_tools([get_user_location, fetch_contextual_data])
    chain = prompt | llm_with_tools.with_structured_output(AnalysisResult)
    return chain
