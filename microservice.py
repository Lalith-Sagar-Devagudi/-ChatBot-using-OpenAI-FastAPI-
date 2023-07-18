from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
import openai
import os
from pymongo import MongoClient
from pymongo.collection import Collection
from pydantic import BaseModel
import pyttsx3

app = FastAPI()

origins = ["http://localhost:8001"]  # adjust this to match your actual domain

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the speech engine
engine = pyttsx3.init()

class ChatInput(BaseModel):
    """Data model for chat input."""
    user_id: str
    message: str

# Set OpenAI API key
openai.api_key = "******************"  # set your OpenAI API key in environment variables

# Connect to MongoDB client
client = MongoClient(os.getenv("mongodb://localhost:27017"))  # MongoDB connection string
db = client['chatbot']  # Replace with your database name

@app.post("/chat")
async def chat(chat_input: ChatInput) -> dict:
    """
    Function to handle chat with the bot.
    It saves conversation to the database, calls the AI model to get response,
    converts the response to speech and returns the AI response.
    """
    user_id = chat_input.user_id
    message = chat_input.message
    
    # Load conversation history from DB
    history = db.conversations.find_one({"user_id": user_id})
    if history is None:
        history = {"user_id": user_id, "conversation": []}
    
    # Use OpenAI API to generate a response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role": "user",
            "content": message
        }],
        max_tokens=150
    )

    # Check if the response from OpenAI is empty or not
    if response is None or len(response.choices) == 0:
        raise HTTPException(status_code=500, detail="OpenAI response is empty")

    # Store the new messages in the conversation history
    new_messages = {
        "user": message,
        "assistant": response.choices[0].message['content'],
    }
    history['conversation'].append(new_messages)
    db.conversations.update_one({"user_id": user_id}, {"$set": history}, upsert=True)

    # Convert text to speech
    tts = gTTS(text=response.choices[0].message['content'], lang='en')
    tts.save("output.mp3")

    # Speak the response
    engine.say(response.choices[0].message['content'])
    engine.runAndWait()

    return {"message": response.choices[0].message['content']}



@app.get("/history/{user_id}")
async def get_history(user_id: str) -> FileResponse:
    """
    Function to get chat history for a given user id.
    It fetches the conversation from database, converts it to text file and returns as FileResponse.
    """
    history = db.conversations.find_one({"user_id": user_id})
    if history is None:
        raise HTTPException(status_code=404, detail="No conversation history found for this user")
    
    # Convert the conversation list into a single string, each message on a new line
    history_string = "\n".join([f"User: {msg['user']}\nAssistant: {msg['assistant']}" for msg in history["conversation"]])
    
    # Write the history string to a text file
    with open("outputs/history.txt", "w") as file:
        file.write(history_string)

    # Return the file as a response
    return FileResponse("outputs/history.txt", media_type="text/plain", filename=f"{user_id}_history.txt")

@app.get("/audio")
async def get_audio() -> FileResponse:
    """
    Function to return the most recent AI response as audio file.
    """
    return FileResponse("outputs/output.mp3", media_type="audio/mpeg", filename="output.mp3")
