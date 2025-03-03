import openai
from openai import OpenAI
import re
import os
import requests
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

class OpenAiService:
    def __init__(self, name):
        self.name = name

    @staticmethod
    def _generate_response(system_message, user_message, model="gpt-3.5-turbo", max_tokens=150, temperature=0.7):
        """Handles API calls for text generation, reducing redundancy."""
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
            print(f"Error in API call: {e}")
            return None

    def generate_psychedelic_prompt(self):
        """Generates a creative prompt for psychedelic and fractal art."""
        system_message = "You are an AI that helps generate creative prompts for psychedelic and fractal art."
        user_message = (
            "Generate a highly creative and detailed prompt for an AI image generator to create a trippy, vibrant fractal image. "
            "The prompt should emphasize psychedelic color schemes, intricate geometric patterns, surreal depth, and glowing, otherworldly aesthetics. "
            "The prompt should describe unique elements such as swirling neon fractals, kaleidoscopic symmetry, cosmic energy flows, or organic, biomorphic shapes. "
            "The goal is to create visually stunning and mind-bending fractal compositions that feel immersive and hypnotic."
        )
        return self._generate_response(system_message, user_message, max_tokens=150, temperature=0.9)

    def generate_product_description(self, prompt):
        """Generates an SEO-optimized product description for psychedelic and fractal art on eBay."""
        system_message = (
            "You are an AI that helps generate creative and SEO-focused product descriptions for psychedelic and fractal art sold on eBay. "
            "You have a strong focus on eBay SEO. Using the description of the tapestry provided, generate a unique, engaging, and SEO-heavy product description."
        )
        return self._generate_response(system_message, prompt, max_tokens=700, temperature=0.7)

    def generate_product_title(self, description):
        """Generates a concise, SEO-friendly product title for eBay."""
        system_message = (
            "You are an AI that helps generate creative product titles for psychedelic and fractal art. "
            "You have a strong focus on SEO. Using the provided tapestry description, generate a single unique title for an eBay listing."
        )
        title = self._generate_response(system_message, description, max_tokens=15, temperature=0.7)

        if title:
            clean_title = re.sub(r'[\d"|\']', '', title).replace(".", "").replace("-", "")
            return f"Tapestry - {clean_title}"
        return None

    @staticmethod
    def _generate_image_response(prompt, model="dall-e-3", size="1792x1024", quality="hd"):
        """Handles image generation API calls."""
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

    def generate_image(self, prompt):
        """Generates an AI image based on a given prompt."""
        return self._generate_image_response(prompt)

    @staticmethod
    def download_image(image_url, save_path):
        """Downloads an image from the given URL and saves it to the specified path."""
        try:
            save_path = os.path.expanduser(save_path)
            directory = os.path.dirname(save_path)

            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            response = requests.get(image_url)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    file.write(response.content)
                print(f"Image saved as {save_path}")
            else:
                print(f"Failed to retrieve image. HTTP Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error downloading image: {e}")
