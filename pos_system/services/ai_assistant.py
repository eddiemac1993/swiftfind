from openai import OpenAI, RateLimitError
import os, time

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_chatgpt(messages, retries=3, max_tokens=500):
    """
    Send a chat history to OpenAI and return the assistant's reply.
    Handles rate limits gracefully with retries + backoff.
    """
    for i in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # good balance of speed & quality
                messages=messages,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        
        except RateLimitError:
            # exponential backoff
            wait_time = (2 ** i) * 5  
            if i < retries - 1:
                time.sleep(wait_time)
            else:
                return "⚠️ Our AI assistant is currently overloaded. Please try again later."
        
        except Exception as e:
            return f"⚠️ An error occurred: {str(e)}"
