import re

class TextGenerator:
    """Handles text generation tasks using OpenAIClient."""

    def __init__(self, client):
        """
        Initializes the TextGenerator with an OpenAIClient.
        
        :param client: An instance of OpenAIClient.
        """
        self.client = client

    def generate_psychedelic_prompt(self):
        """Generates a creative prompt for psychedelic and fractal art."""
        system_message = "You are an AI that helps generate creative prompts for psychedelic and fractal art."
        user_message = (
            "Generate a highly creative and detailed prompt for an AI image generator to create a trippy, vibrant fractal image. "
            "The prompt should emphasize psychedelic color schemes, intricate geometric patterns, surreal depth, and glowing, otherworldly aesthetics. "
            "The prompt should describe unique elements such as swirling neon fractals, kaleidoscopic symmetry, cosmic energy flows, or organic, biomorphic shapes. "
            "The goal is to create visually stunning and mind-bending fractal compositions that feel immersive and hypnotic."
        )
        return self.client.generate_text(system_message, user_message, max_tokens=150, temperature=0.9)

    def generate_product_description(self, prompt, store_name, product_type):
        """Generates an SEO-optimized product description dynamically based on store and product type."""
        system_message = (
            f"You are an AI that helps generate creative and SEO-focused product descriptions for {product_type}s sold on {store_name}. "
            f"You have a strong focus on {store_name} SEO. Using the description of the products design, generate a unique, engaging, and SEO-heavy product description."
        )
        return self.client.generate_text(system_message, prompt, max_tokens=700, temperature=0.7)

    def generate_product_title(self, description, store_name, product_type):
        """Generates a concise, SEO-friendly product title dynamically based on store and product type."""
        system_message = (
            f"You are an AI that helps generate creative product titles for {product_type}s. "
            f"You have a strong focus on SEO. Using the provided description, generate a single unique title for a {store_name} listing."
        )
        title = self.client.generate_text(system_message, description, max_tokens=25, temperature=0.7)

        if title:
            clean_title = re.sub(r'[\d"|\']', '', title).replace(".", "").replace("-", "")
            return f"{product_type.capitalize()} - {clean_title}"
        return None

