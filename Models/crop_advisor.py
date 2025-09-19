import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class CropAdvisorAgent:
    """
    Handles crop-related queries dynamically via Gemini API.
    """
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a smart agricultural crop advisor."),
            ("user", "{query}")
        ])

    def handle_query(self, query: str) -> dict:
        response = self.llm(self.prompt_template.format_prompt(query=query).to_messages())
        return {
            "agent": "Crop Advisor",
            "query_received": query,
            "recommendation": response.content
        }
