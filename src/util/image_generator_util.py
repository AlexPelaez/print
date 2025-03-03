import os
import requests
from openai_client import OpenAIClient


class ImageGenerator:
    """Handles image generation tasks using OpenAIClient."""

    def __init__(self, client: OpenAIClient):
        self.client = client

    def generate_image(self, prompt):
        """Generates an AI image based on a given prompt."""
        return self.client.generate_image(prompt)

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
