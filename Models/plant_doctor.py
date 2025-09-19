import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class PlantDoctorAgent:
    """
    Handles plant disease queries dynamically via Gemini API.
    """
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a plant doctor who diagnoses plant diseases based on text descriptions."),
            ("user", "{query}")
        ])

    def handle_query(self, query: str) -> dict:
        response = self.llm(self.prompt_template.format_prompt(query=query).to_messages())
        return {
            "agent": "Plant Doctor",
            "query_received": query,
            "diagnosis": response.content
        }
