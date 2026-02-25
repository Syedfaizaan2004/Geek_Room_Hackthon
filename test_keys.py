import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("Testing Groq...")
groq_key = os.getenv("GROQ_API_KEY")
r_groq = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {groq_key}"},
    json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "hi"}]}
)
print("Groq:", r_groq.status_code, r_groq.text[:150])

print("Testing Gemini...")
gemini_key = os.getenv("GEMINI_API_KEY")
r_gemini = requests.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}",
    headers={"Content-Type": "application/json"},
    json={"contents": [{"parts": [{"text": "hi"}]}]}
)
print("Gemini:", r_gemini.status_code, r_gemini.text[:150])
