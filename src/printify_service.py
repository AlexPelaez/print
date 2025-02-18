import requests
import os
import base64
import random
import string
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("PRINTIFY_API_KEY")

# Printify Popup - 20434486
# Amazon - 
# Ebay - 20496160
SHOP_ID = '20434486'  # Replace with your actual shop ID

BASE_URL = "https://api.printify.com/v1"
UPLOAD_IMAGE_URL = f"{BASE_URL}/uploads/images.json"
CREATE_PRODUCT_URL = f"{BASE_URL}/shops/{SHOP_ID}/products.json"

# Headers for the API requests
headers = {
	"Authorization": f"Bearer {API_KEY}",
	"Content-Type": "application/json",
}

class PrintifyService:
	def __init__(self, name):
		self.name = name

	def upload_image(self, image_path):  # Added 'self'
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

	def get_product_details(self, product_id):  # Added 'self'
		FETCH_PRODUCT_DETAILS_URL = f"{BASE_URL}/shops/{SHOP_ID}/products/{product_id}.json"
		response = requests.get(FETCH_PRODUCT_DETAILS_URL, headers=headers)

		if response.status_code == 200:
			return response.json()
		else:
			print(f"Error fetching product details: {response.status_code} - {response.text}")
			return None

	def publish_product(self, product_id):  # Added 'self'
		# Get product details to ensure we have the required data
		product_details = self.get_product_details(product_id)

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
			"keyFeatures": True,
			"shipping_template": True
		}

		# Publish the product
		publish_url = f"{BASE_URL}/shops/{SHOP_ID}/products/{product_id}/publish.json"
		response = requests.post(publish_url, json=publish_data, headers=headers)

		if response.status_code == 200:
			print(f"Product {product_id} published successfully!")
		else:
			print(f"Error publishing product: {response.status_code} - {response.text}")

	def generate_sku(self, length=18):
		"""Generate a random SKU with the specified length (default 18 digits)."""
		return ''.join(random.choices(string.digits, k=length))

	def duplicate_product(self, product_id, new_image_id, title, description):  # Added 'self'
		# Get product details
		product_details = self.get_product_details(product_id)

		if not product_details:
			print("Could not retrieve product details. Exiting.")
			return

		# Update image IDs in print_areas (Placeholders)
		for product in product_details.get('print_areas', []):
			for placeholder in product.get('placeholders', []):
				for image in placeholder.get('images', []):
					image['id'] = new_image_id['id']  # Update the image ID in print areas

		# Update SKUs in variants with random numbers (same number of digits as original SKUs)
		variants = product_details.get('variants', [])
		for variant in variants:
			original_sku = variant.get('sku', '')
			if original_sku:
				sku_length = len(original_sku)  # Maintain the same length for the new SKU
				variant['sku'] = self.generate_sku(sku_length)  # Generate new SKU


		product_details['title'] = title
		product_details['description'] = description

		# Create the duplicated product
		response = requests.post(CREATE_PRODUCT_URL, json=product_details, headers=headers)

		if response.status_code == 200:
			new_product_id = response.json()['id']
			print(f"Product duplicated successfully! New product ID: {new_product_id}")

			return new_product_id
		else:
			print(f"Error creating new product: {response.status_code} - {response.text}")

	def delete_product(self, product_id):
		"""Deletes a product from Printify using the Printify API."""
		delete_url = f"{BASE_URL}/shops/{SHOP_ID}/products/{product_id}.json"
		response = requests.delete(delete_url, headers=headers)

		if response.status_code == 200:
			print(f"Product {product_id} deleted successfully!")
		else:
			print(f"Error deleting product: {response.status_code} - {response.text}")


	def get_printify_mockup(self, product_id, save_folder="~/test_mocks"):
		# Ensure save directory exists
		save_folder = os.path.expanduser(save_folder)
		os.makedirs(save_folder, exist_ok=True)

		# Printify product details endpoint
		fetch_product_url = f"{BASE_URL}/shops/{SHOP_ID}/products/{product_id}.json"
		response = requests.get(fetch_product_url, headers=headers)

		if response.status_code == 200:
			product_data = response.json()
			mockups = product_data.get("images", [])

			# Ensure there are at least 76 mockups
			if len(mockups) < 76:
				print("Error: The product does not have a 76th mockup.")
				return

			# Get the 76th mockup image URL
			mockup_url = mockups[75]["src"]  # Index 75 corresponds to the 76th item
			image_response = requests.get(mockup_url, stream=True)

			if image_response.status_code == 200:
				image_filename = os.path.join(save_folder, f"{product_id}_mockup_76.jpg")

				with open(image_filename, "wb") as file:
					for chunk in image_response.iter_content(1024):
						file.write(chunk)

				print(f"76th Mockup saved: {image_filename}")
			else:
				print(f"Failed to download the 76th mockup: {image_response.status_code}")

		else:
			print(f"Error: {response.status_code} - {response.text}")
