import os
import traceback
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from backend.drive_tool import search_drive, read_file_content, describe_image

# Load environment variables
load_dotenv()

app = FastAPI(title="TailorTalk Google Drive Agent API")

# Global error handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("\n" + "="*50)
    print("CRITICAL ERROR IN BACKEND:")
    traceback.print_exc()
    print("="*50 + "\n")
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# Initialize the LLM via Groq
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# Define the tools
tools = [search_drive, read_file_content, describe_image]

# Simplified prompt for better stability
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Google Drive assistant with Vision.
    
    Use 'search_drive' to find files. 
    Use 'read_file_content' to read text files/docs.
    Use 'describe_image' to see and describe images (png, jpg, jpeg).
    
    IMPORTANT: Google Drive search is case-sensitive for exact name matches. 
    ALWAYS use 'name contains' instead of 'name =' to ensure you find files regardless of capitalization.
    
    Example queries:
    - name contains 'untitled'
    - mimeType contains 'image/'
    - name != ''

    IMPORTANT: If a user asks 'what is in this photo' or 'describe this image':
    1. Find the file_id of the image using 'search_drive'.
    2. Pass that file_id to 'describe_image'.
    
    Always provide the filename and the link for every result you find.
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create the agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# Data models
class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str

chat_histories = {}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if request.user_id not in chat_histories:
        chat_histories[request.user_id] = []
    try:
        response = agent_executor.invoke({
            "input": request.message,
            "chat_history": chat_histories[request.user_id]
        })
        output = response["output"]
        chat_histories[request.user_id].append(HumanMessage(content=request.message))
        chat_histories[request.user_id].append(AIMessage(content=output))
        return ChatResponse(response=output)
    except Exception as e:
        raise e

@app.get("/")
async def root():
    return {"status": "ok", "message": "TailorTalk Agent API is running"}
