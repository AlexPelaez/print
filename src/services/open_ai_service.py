import openai
from openai import OpenAI
import re
import os
client = OpenAI()
import requests
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class OpenAiService:
	def __init__(self, name):
		self.name = name

	def generate_psychedelic_prompt():
	    try:
	        # Make the API call using OpenAI's ChatCompletion method
	        response = client.chat.completions.create(
	            messages=[
	                {"role": "system", "content": "You are an AI that helps generate creative prompts for psychedelic and fractal art."},
	                {"role": "user", "content": "Generate a highly creative and detailed prompt for an AI image generator to create a trippy, vibrant fractal image. The prompt should emphasize psychedelic color schemes, intricate geometric patterns, surreal depth, and glowing, otherworldly aesthetics. The prompt should describe unique elements such as swirling neon fractals, kaleidoscopic symmetry, cosmic energy flows, or organic, biomorphic shapes. The goal is to create visually stunning and mind-bending fractal compositions that feel immersive and hypnotic."}
	            ],
	            model="gpt-3.5-turbo",
	            max_tokens=150,
	            n=1,  # Requesting a single response
	            temperature=0.9
	        )


	        prompt = response.choices[0].message.content

	        # Print or return the generated prompts
	        print(f"Generated prompt: {prompt}")
	        return prompt

	    except Exception as e:
	        print(f"Error generating prompt: {e}")

	def generate_product_description(prompt):
	    try:
	        additional_text = """
	           
	        """ 
	        # Make the API call using OpenAI's ChatCompletion method
	        response = client.chat.completions.create(
	            messages=[
	                {"role": "system", "content": "You are an AI that helps generate creative and SEO focused product descriptions for psychedelic and fractal art that is sold on Ebay. You have a strong focus on Ebay SEO. Using the description of the tapestry provided a unique and engaging and SEO heavy product description for a tapestry."},
	                {"role": "user", "content": prompt}
	            ],
	            model="gpt-3.5-turbo",
	            max_tokens=700,
	            n=1,  # Requesting a single response
	            temperature=0.7
	        )


	        description = response.choices[0].message.content + additional_text

	        # Print or return the generated description
	        print(f"Generated description: {description}")
	        return description

	    except Exception as e:
	        print(f"Error generating description: {e}")

	def generate_product_title(description):
	    try:
	        # Make the API call using OpenAI's ChatCompletion method
	        response = client.chat.completions.create(
	            messages=[
	                {"role": "system", "content": "You are an AI that helps generate creative product titles for psychedelic and fractal art. You have a strong focus on SEO. Using the description of the tapestry that is provided generate a single unique title for an Ebay listing of a tapestry"},
	                {"role": "user", "content": description}
	            ],
	            model="gpt-3.5-turbo",
	            max_tokens=15,
	            n=1,  # Requesting a single response
	            temperature=0.7
	        )


	        title = response.choices[0].message.content.replace(".", "").replace("-", "")

	        # Print or return the generated title
	        print(f"Generated title: {re.sub(r'[\d"|\']', '', title)}")
	        return "Tapestry - "+re.sub(r'[\d"|\']', '', title)

	    except Exception as e:
	        print(f"Error generating title: {e}")

	def generate_image(prompt):
		try:
		    response = client.images.generate(
		        prompt=prompt,
		        model="dall-e-3",
		        size="1792x1024",
		        quality="hd",
		        n=1
		    )

		    result = response.data[0].url
		    print(f"Generated image for prompt: {result}")
		    return result
		except Exception as e:
			print(f"Error generating image: {e}")

	def download_image(image_url, save_path):
	    try:
	        # Expand ~ to the full home directory
	        save_path = os.path.expanduser(save_path)
	        
	        # Ensure the directory exists
	        directory = os.path.dirname(save_path)
	        if directory and not os.path.exists(directory):
	            os.makedirs(directory)

	        # Send a GET request to the image URL
	        response = requests.get(image_url)
	        
	        # Check if the request was successful (status code 200)
	        if response.status_code == 200:
	            # Open a file in binary write mode and save the image
	            with open(save_path, 'wb') as file:
	                file.write(response.content)
	            print(f"Image saved as {save_path}")
	        else:
	            print(f"Failed to retrieve image. HTTP Status Code: {response.status_code}")
	    except Exception as e:
	        print(f"Error downloading image: {e}")