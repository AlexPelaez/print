import openai
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()


class OpenAIClient:
    """Handles all OpenAI API interactions for both text and images."""

    @staticmethod
    def generate_text(system_message, user_message, model="gpt-3.5-turbo", max_tokens=150, temperature=0.7):
        """Handles API calls for text generation."""
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                model=model,
                max_tokens=max_tokens,
                n=1,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in text API call: {e}")
            return None

    @staticmethod
    def generate_image(prompt, model="dall-e-3", size="1792x1024", quality="hd"):
        """Handles OpenAI image generation."""
        try:
            response = client.images.generate(
                prompt=prompt,
                model=model,
                size=size,
                quality=quality,
                n=1
            )
            return response.data[0].url
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
