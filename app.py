from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import traceback
import re
import os

# ✅ Initialize OpenAI client (SECURE WAY)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# ✅ Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Request model
class ChatRequest(BaseModel):
    question: str

# ✅ Fetch & clean site content
def get_website_content(url):
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text(separator=" ", strip=True)
        return text[:6000]
    except Exception as e:
        print("❌ Website fetch error:", e)
        return "Website content unavailable."

# ✅ Cache site content
site_content = get_website_content("https://www.dryousufmemon.pk/")

# ✅ Chat endpoint
@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    user_question = request.question.lower().strip()

    # ✅ Use regex to match exact words only
    simple_responses = {
        r"\bhi\b": "Hello! 👋 How can I assist you today?",
        r"\bhello\b": "Hi there! 😊 How can I help?",
        r"\bsalam\b": "Wa Alaikum Assalam! 🌸 How can I assist you?",
        r"\bassalamualaikum\b": "Wa Alaikum Assalam! 🌙",
        r"\bthanks\b": "You're welcome! 😊",
        r"\bthank you\b": "Happy to help! 🙏",
        r"\bbye\b": "Goodbye! 👋 Take care.",
        r"\bgood morning\b": "Good morning! ☀️",
        r"\bgood evening\b": "Good evening! 🌙",
    }

    for pattern, value in simple_responses.items():
        if re.search(pattern, user_question):
            return {"reply": value}

    # ✅ Smart AI response for real questions
    prompt = f"""
You are a friendly and professional AI assistant for Dr. Yousuf Memon's official website.

Use ONLY information from the website content below.
If you don't know something, politely say: "I'm sorry, I don't have that information right now."
Keep your tone warm, helpful, and human.

If the user asks about contacting the doctor, appointments, WhatsApp, phone number, or communication details,
you must clearly respond with:
"You can contact Dr. Yousuf Memon at 0339-99888767 for appointments or inquiries."

Website Content:
{site_content}

User Question:
{user_question}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )
        answer = response.choices[0].message.content.strip()
        return {"reply": answer}

    except Exception as e:
        print("❌ OpenAI API Error:", e)
        traceback.print_exc()
        return {"reply": "There was an issue generating a response. Please try again later."}

# ✅ Root route
@app.get("/")
def home():
    return {"message": "Chatbot API is running smoothly."}

# ✅ Add this for Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
