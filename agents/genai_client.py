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
    from google.genai import types
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")
    
    # Set a 300-second HTTP timeout so the client never hangs indefinitely
    http_options = types.HttpOptions(timeout=300000)  # 300 seconds in ms
    return genai.Client(api_key=api_key, http_options=http_options)


def get_model_name():
    """Returns the model name to use for document parsing (fast, stable)."""
    return "models/gemini-flash-latest"


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
                # Gemini rate limits reset every ~60 seconds — wait 30/60/90s
                wait_time = 30 + (attempt * 30)
                print(f"  ⏳ Gemini rate limited (429). Waiting {wait_time}s before retry... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            elif "503" in err_str or "UNAVAILABLE" in err_str or "overloaded" in err_str.lower():
                wait_time = 10 + (attempt * 10)
                print(f"  ⏳ Gemini overloaded (503). Waiting {wait_time}s before retry... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                raise 
                
    raise Exception(f"Gemini API rate limited after {max_retries} retries")
