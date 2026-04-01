"""
Shared Gemini/Vertex AI Client Factory (Singleton).
Uses Vertex AI with Google Cloud free credits (service account JSON).
Falls back to Gemini API key if Vertex AI is not configured.
"""
import os
import time
from dotenv import load_dotenv
load_dotenv()

# Singleton client — initialized once, reused everywhere
_client = None
_client_initialized = False

def get_genai_client():
    from google import genai
    from google.genai.errors import APIError
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")
        
    return genai.Client(api_key=api_key)


def get_model_name():
    """Returns the model name to use."""
    return "gemini-2.5-flash-lite"


def safe_generate(client, model, contents, config, max_retries=3):
    """
    Wrapper around client.models.generate_content with automatic retry
    for 429 RESOURCE_EXHAUSTED errors.
    """
    from google.genai import types
    
    safety_settings = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE
        ),
    ]
    
    if config:
        config.safety_settings = safety_settings
    else:
        config = types.GenerateContentConfig(safety_settings=safety_settings)

    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait_time = 3 + (attempt * 2)
                print(f"  ⏳ Gemini rate limited (429). Waiting {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                raise 
                
    raise Exception(f"Gemini API rate limited after {max_retries} retries")
