
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

text = "test"
model = "models/gemini-embedding-001"
res = genai.embed_content(model=model, content=text, task_type="retrieval_document")
print(f"Model: {model}, Size: {len(res['embedding'])}")

model = "models/gemini-embedding-001"
try:
    res = genai.embed_content(model=model, content=text, task_type="retrieval_document")
    print(f"Model: {model}, Size: {len(res['embedding'])}")
except Exception as e:
    print(f"Model: {model} failed: {e}")
