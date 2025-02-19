import requests
import os
import base64
import random
import string
from dotenv import load_dotenv
import json

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

	def upload_image(self, image_path): 
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

	def get_product_details(self, product_id):
		FETCH_PRODUCT_DETAILS_URL = f"{BASE_URL}/shops/{SHOP_ID}/products/{product_id}.json"
		response = requests.get(FETCH_PRODUCT_DETAILS_URL, headers=headers)

		if response.status_code == 200:
			return response.json()
		else:
			print(f"Error fetching product details: {response.status_code} - {response.text}")
			return None

	def publish_product(self, product_id):
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
			
	def duplicate_product_from_model(self, product_model):
		"""
		Creates a new product on Printify (duplicates locally stored model),
		matching the official product properties schema from Printify.
		
		For read-only fields (e.g., created_at, updated_at, images, blueprint_id,
		print_provider_id, etc.), we only include them if needed at creation time.
		By default, blueprint_id and print_provider_id are required for creation,
		but afterwards they're read-only.

		:param product_model: A PrintifyProductModel (or similar) containing all
							  required data for Printify's product creation.
		:return: The new Printify product ID if successful, or None on error.
		"""

		# 1) Build the core product_details structure.
		#    Many fields (like 'images', 'created_at', 'updated_at') are read-only
		#    or won't do anything if we send them, so we skip them unless absolutely needed.
		#    Required or recommended fields from your schema:
		product_details = {
			# Required fields:
			"title": product_model.title,                     # str
			"description": product_model.description,         # str
			"blueprint_id": product_model.blueprint_id,       # int
			"print_provider_id": product_model.print_provider_id,  # int

			# Optional or recommended:
			# "safety_information": product_model.safety_information, # str if you store it

			# Read-only, so normally not set on creation:
			# "user_id": product_model.user_id,
			# "shop_id": product_model.shop_id,
			# "created_at": product_model.created_at,
			# "updated_at": product_model.updated_at,
			# "is_locked": product_model.is_locked,
			# "visible": product_model.visible,
			# "is_printify_express_eligible": ...
			# "is_economy_shipping_eligible": ...
			# "is_printify_express_enabled": ...
			# "is_economy_shipping_enabled": ...

			# "status": ... # if your model has it, but printify docs say it's read-only.
			# "category": ...
			# "brand": ...
			# "campaign_id": ...

			# 2) Sub-structures below:
			"tags": [],
			"variants": [],
			"print_areas": [],
			# read-only for creation:
			# "images": [],

			# "print_details": {},  # Only if your model uses print_details for e.g. "print_on_side"
			# "external": [],       # or a dict if you want to pass "shipping_template_id" etc.
			# "sales_channel_properties": [],
		}

		# 2) If your model includes safety_information (optional):
		#    See docs for "safety_information" field
		# if hasattr(product_model, "safety_information") and product_model.safety_information:
		#     product_details["safety_information"] = product_model.safety_information

		# 3) Add tags
		#    Printify’s docs: "tags": ["T-shirt", "Men's"]
		for tag_model in product_model.tags:
			product_details["tags"].append(tag_model.tag)

		# 4) Variants
		#    Each variant must at least have 'id' (the blueprint variant ID) and 'price'.
		#    Additional fields: "title", "sku", "grams", "is_enabled", "is_printify_express_eligible", ...
		for variant_model in product_model.variants:
			var_data = variant_model.data
			if not isinstance(var_data, dict):
				continue
			# Required:
			variant_id = var_data.get("id")      # blueprint variant ID
			price = var_data.get("price")        # in cents (e.g. 1000 => $10.00)
			if variant_id is None or price is None:
				# Skip or handle error if missing required fields
				continue

			# Optional:
			sku = var_data.get("sku")
			title = var_data.get("title")        # read-only but might be included
			grams = var_data.get("grams")
			is_enabled = var_data.get("is_enabled", True)
			is_default = var_data.get("is_default", False)
			# cost is read-only
			# is_available, is_printify_express_eligible = read-only

			# Build the payload
			variant_payload = {
				"id": variant_id,
				"price": price,
				# optional
				"sku": sku,
				"is_enabled": is_enabled,
				"is_default": is_default,
				# "title": title,       # read-only, so typically not included on create
				# "grams": grams,       # also read-only
			}

			product_details["variants"].append(variant_payload)

		# 5) Print Areas
		#    "print_areas": [{
		#       "variant_ids": [123, 124],
		#       "placeholders": [{
		#          "position": "front",
		#          "images": [...]
		#       }],
		#    }]
		for pa_model in product_model.print_areas:
			pa_data = pa_model.data
			if not isinstance(pa_data, dict):
				continue
			variant_ids = pa_data.get("variant_ids", [])  # which variants this area belongs to
			placeholders = pa_data.get("placeholders", [])

			pa_payload = {
				"variant_ids": variant_ids,
				"placeholders": []
			}

			for placeholder in placeholders:
				position = placeholder.get("position")   # e.g. "front"
				images_list = placeholder.get("images", [])
				# Each image: {id, src, name, type, height, width, x, y, scale, angle, pattern? ...}
				# Printify requires the positioning fields (x, y, scale, angle).
				ph_payload = {
					"position": position,
					"images": images_list
				}
				pa_payload["placeholders"].append(ph_payload)

			product_details["print_areas"].append(pa_payload)

		# 6) Print Details (optional)
		#    e.g. "print_details": {"print_on_side": "regular"}
		if hasattr(product_model, "print_details") and product_model.print_details:
			# Suppose product_model.print_details is a dict
			product_details["print_details"] = product_model.print_details

		# 7) External - for shipping_template_id or references
		#    Docs say "external": [{
		#       "id": "A123abceASd",
		#       "handle": "/path/to/product",
		#       "shipping_template_id": "B123abceASd"
		#    }]
		# Typically it's an array, but docs also mention "CONDITIONAL" singular object.
		# You can adapt as needed:
		if product_model.external and isinstance(product_model.external.data, dict):
			product_details["external"] = [product_model.external.data]

		# 8) Sales Channel Properties (optional)
		#    e.g. "sales_channel_properties": {"free_shipping": false, ...}
		# If your model stores them as a dictionary or list of dictionaries
		if hasattr(product_model, "sales_channel_properties") and product_model.sales_channel_properties:
			# Some channels expect an object, some an array. Adjust as needed:
			# We'll assume one dictionary with channel-specific keys
			# If you have multiple objects, you might store them in an array
			scp_data_list = []
			for scp_model in product_model.sales_channel_properties:
				scp_data = scp_model.data
				if isinstance(scp_data, dict):
					scp_data_list.append(scp_data)
			# If the Printify docs require a single object, you might do `scp_data_list[0]`
			# Otherwise if you can pass an array, pass them all
			# The docs show "sales_channel_properties": { ... } (an object), not an array.
			if scp_data_list:
				# We'll just take the first
				product_details["sales_channel_properties"] = scp_data_list[0]

		# 9) is_printify_express_enabled
		#    If you want to enable Printify Express for an eligible product:
		# if hasattr(product_model, "is_printify_express_enabled"):
		#     product_details["is_printify_express_enabled"] = bool(product_model.is_printify_express_enabled)

		# 10) Now make the POST request to create the product on Printify
		response = requests.post(CREATE_PRODUCT_URL, json=product_details, headers=headers)

		if response.status_code == 200:
			new_product_id = response.json().get("id")
			print(f"Product duplicated successfully from model! New product ID: {new_product_id}")
			return new_product_id
		else:
			print(f"Error creating new product: {response.status_code} - {response.text}")
			return None



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
