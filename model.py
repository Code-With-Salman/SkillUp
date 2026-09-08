# ---------------------------
# FILE: model.py
# ---------------------------

import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Gemini API setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it in your .env file.")

# Define a list of Gemini models to try, in order of preference.
# Replace these placeholder names with actual Gemini model identifiers.
GEMINI_MODELS = [
    # "gemini-2.0-flash",
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-pro"
]

async def call_gemini_with_fallback(prompt: str) -> str:
    """
    Makes an asynchronous call to the Gemini API, with fallback to other models
    if the primary one is unavailable or returns an error.
    """
    for model_name in GEMINI_MODELS:
        GEMINI_MODEL_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        body = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        async with httpx.AsyncClient() as client:
            try:
                print(f"Attempting to call Gemini model: {model_name}")
                response = await client.post(GEMINI_MODEL_URL, json=body, timeout=60.0)
                response.raise_for_status()  # Raise an exception for 4xx or 5xx responses

                candidates = response.json().get("candidates", [])
                if not candidates:
                    print(f"Gemini API ({model_name}) returned no candidates: {response.text}")
                    # If no candidates but no HTTP error, try next model
                    continue

                text_response = candidates[0].get("content", {}).get("parts", [])[0].get("text", "")
                if not text_response:
                    print(f"Gemini API ({model_name}) returned empty text response.")
                    continue # Try next model if response is empty

                return text_response

            except httpx.HTTPStatusError as e:
                print(f"⚠️ HTTP error with Gemini model {model_name}: {e.response.status_code} - {e.response.text}")
                # Continue to next model if it's a server error or rate limit
                if e.response.status_code >= 500 or e.response.status_code == 429: # Server error or Too Many Requests
                    continue
                else:
                    raise # Re-raise for client-side errors that shouldn't trigger fallback

            except httpx.RequestError as e:
                print(f"⚠️ Network error with Gemini model {model_name}: {e}")
                continue # Continue to next model on network issues

            except json.JSONDecodeError as e:
                print(f"⚠️ JSON decoding error with Gemini model {model_name}: {e}")
                continue # Continue to next model on JSON issues

            except Exception as e:
                print(f"⚠️ An unexpected error occurred with Gemini model {model_name}: {e}")
                continue # Catch any other unexpected errors and try next model

    # If all models fail
    raise ConnectionError("All available Gemini models failed to respond.")