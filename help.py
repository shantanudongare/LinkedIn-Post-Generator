from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()

# Correcting the parameter name
llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.3-70b-versatile")

if __name__ == "__main__":
    res = llm.invoke("What are the symptoms of COVID-19?")
    print(res.content)
