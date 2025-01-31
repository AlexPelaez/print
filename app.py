import requests
import json
import os
import base64
import openai
from openai import OpenAI
import uuid
import re
client = OpenAI()


SHOP_ID = '20434486'


# Printify API base URL
BASE_URL = "https://api.printify.com/v1"
UPLOAD_IMAGE_URL = f"{BASE_URL}/uploads/images.json"
CREATE_PRODUCT_URL = f"{BASE_URL}/shops/{SHOP_ID}/products.json"

# Headers for the API requests
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def upload_image(image_path):
    # Printify image upload endpoint 
    try:
        # Ensure the file exists
        if not os.path.exists(image_path):
            print(f"File does not exist: {image_path}")
            return None

        # Extract the file name from the path (e.g., 'image.jpg')
        file_name = os.path.basename(image_path)

        # Open the image file in binary mode and encode it to Base64
        with open(image_path, 'rb') as image_file:
            # Read the file and encode to Base64
            encoded_contents = base64.b64encode(image_file.read()).decode('utf-8')

        # Prepare the data with Base64-encoded contents
        data = {
            'file_name': file_name,  # The file name as expected by Printify
            'contents': encoded_contents  # Base64-encoded image content
        }

        # Send the request to upload the image
        response = requests.post(UPLOAD_IMAGE_URL, headers=headers, json=data)

        # Debugging: check the full response
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")

        if response.status_code == 200:
            print("Image uploaded successfully!")
            return response.json()  # Returns the image data (ID, file_name, etc.)
        else:
            print(f"Error uploading image: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"An error occurred during image upload: {e}")
        return None

# Function to fetch an existing product's details
def get_product_details(product_id):
    FETCH_PRODUCT_DETAILS_URL = f"{BASE_URL}/shops/{SHOP_ID}/products/{product_id}.json"
    response = requests.get(FETCH_PRODUCT_DETAILS_URL, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching product details: {response.status_code} - {response.text}")
        return None

# Function to publish a product (set its status to 'published')
def publish_product(product_id):
    # Get product details to ensure we have the required data
    product_details = get_product_details(product_id)

    if not product_details:
        print(f"Could not retrieve details for product {product_id}. Exiting.")
        return

   # Ensure all required fields are included in the publish request
    publish_data = {
        "title": True,
        "description": True,
        "tags": True,
        "variants": True,
        "images": True,
    }

    # Publish the product
    publish_url = f"{BASE_URL}/shops/{SHOP_ID}/products/{product_id}/publish.json"
    response = requests.post(publish_url, json=publish_data, headers=headers)

    if response.status_code == 200:
        print(f"Product {product_id} published successfully!")
    else:
        print(f"Error publishing product: {response.status_code} - {response.text}")



# Function to duplicate a product with a new image
def duplicate_product(product_id, new_image_id, title, description):
    # Get product details
    product_details = get_product_details(product_id)

    if not product_details:
        print("Could not retrieve product details. Exiting.")
        return

    # Update image IDs in print_areas (Placeholders)
    for product in product_details.get('print_areas', []):
        for placeholder in product.get('placeholders', []):
            for image in placeholder.get('images', []):
                image['id'] = new_image_id['id']  # Update the image ID in print areas

    new_product_data = {
        "title": title,
        "description": description,
        "tags": product_details.get('tags', []),
        "variants": product_details.get('variants', []),
        "print_provider_id": product_details.get('print_provider_id', None),
        "blueprint_id": product_details.get('blueprint_id', None),
        "print_areas": product_details.get('print_areas', []),
        "images": product_details.get('images', []),
        "shop_id": SHOP_ID,
        "type": product_details.get('type', 'physical'),
        "shipping_profile_id": product_details.get('shipping_profile_id', None),
        "skus": product_details.get('skus', []),
        "price": product_details.get('price', None),
        "currency": product_details.get('currency', 'USD'),
    }

    # Create the duplicated product
    response = requests.post(CREATE_PRODUCT_URL, json=new_product_data, headers=headers)

    if response.status_code == 200:
        new_product_id = response.json()['id']
        print(f"Product duplicated successfully! New product ID: {new_product_id}")

        # After duplication, publish the product
        publish_product(new_product_id)
    else:
        print(f"Error creating new product: {response.status_code} - {response.text}")





# Set your API key

def generate_psychedelic_prompt():
    try:
        # Make the API call using OpenAI's ChatCompletion method
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an AI that helps generate creative prompts for psychedelic and fractal art."},
                {"role": "user", "content": "Generate a very detailed prompt for psychedelic AI art generation that incoroporate mandalas, vibrant colors, and mandelbrot set "}
            ],
            model="gpt-3.5-turbo",
            max_tokens=150,
            n=1,  # Requesting a single response
            temperature=0.8
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
            \nProduct features
            - 100% Polyester for strength and quick drying
            - Hemmed edges for durability
            - Multiple sizes available

            Care instructions
            - Wash the item only cold machine wash with similar colors garments using a gentle cycle. Tumble dry on low settings or hang dry. Do not bleach or dry clean.
        """ 
        # Make the API call using OpenAI's ChatCompletion method
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an AI that helps generate creative product descriptions for psychedelic and fractal art. You have a strong focus on SEO. Using the description of the tapestry provided a unique generate and engaging and SEO heavy product description."},
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
                {"role": "system", "content": "You are an AI that helps generate creative product titles for psychedelic and fractal art. You have a strong focus on SEO. Using the description of the tapestry that is provided generate a single unique 2 or 3 word name for the product variant"},
                {"role": "user", "content": description}
            ],
            model="gpt-3.5-turbo",
            max_tokens=4,
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



def main():
    for i in range(10):
        print(f"Iteration {i+ 1}")
        prompt = generate_psychedelic_prompt()
        description = generate_product_description(prompt)
        title = generate_product_title(description)

        image = generate_image(prompt)

        download_image(image, f"~/gen_images/testing{uuid.uuid4()}.jpg")
        download_image(image, '~/gen_working/test.jpg')
    


        product_id = '679876c72b7d16b390077dc8'  # Replace with the product ID to duplicate
        image_folder = "/Users/alex/gen_working/"  # Folder where images are stored

        # Check if the folder exists
        if not os.path.exists(image_folder):
            print(f"Error: Image folder '{image_folder}' not found.")
            return

        # Iterate through all images in the folder
        for image_name in os.listdir(image_folder):
            image_path = os.path.join(image_folder, image_name)

            # Check if the file is an image (optional: check file extensions if needed)
            if os.path.isfile(image_path) and image_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                print(f"Processing image: {image_name}")

                # Upload the new image to Printify
                image_id = upload_image(image_path)

                if image_id:
                    print(f"Image uploaded successfully with ID: {image_id}")

                    # Duplicate product with the new image
                    duplicate_product(product_id, image_id, title, description)
                else:
                    print(f"Error uploading image '{image_name}'. Skipping.")
            else:
                print(f"Skipping non-image file: {image_name}")

if __name__ == "__main__":
    main()
