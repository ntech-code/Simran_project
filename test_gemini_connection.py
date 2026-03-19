"""
Test script to verify Gemini API integration
"""
import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_gemini_connection():
    """Test Gemini API connection"""

    # Load environment variables
    load_dotenv()

    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found in .env file")
        return False

    print(f"✓ API Key loaded: {api_key[:10]}...")

    try:
        # Create Gemini client
        client = genai.Client(api_key=api_key)

        # Model configuration
        model = "gemini-3-flash-preview"

        # Test prompt
        test_prompt = "Respond with 'Gemini connected successfully'"

        print(f"\n📤 Sending test prompt: '{test_prompt}'")
        print(f"   Using model: {model}")

        # Create content
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=test_prompt),
                ],
            ),
        ]

        # Generate content config
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
        )

        # Generate response
        print("\n📥 Response received:")
        print("   ", end="")

        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                print(chunk.text, end="")
                response_text += chunk.text

        print("\n")
        print("✅ Gemini API connection successful!")
        print(f"   Model used: {model}")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: Failed to connect to Gemini API")
        print(f"   Error details: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GEMINI API CONNECTION TEST")
    print("=" * 60)

    success = test_gemini_connection()

    print("\n" + "=" * 60)
    if success:
        print("STATUS: READY TO PROCEED WITH AGENT DEVELOPMENT")
    else:
        print("STATUS: PLEASE FIX API CONNECTION ISSUES")
    print("=" * 60)
