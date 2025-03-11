import os
import random
import string
import requests
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import json

from clients.printify_client import PrintifyClient
from models.printify_product_models import PrintifyProductModel, PrintifyTagModel

load_dotenv()

# Printify Popup - 20434486
# Amazon - 20510104
# Ebay - 20496160

BASE_URL = "https://api.printify.com/v1"

# Headers for the API requests
headers = {
	"Authorization": f"Bearer {os.getenv('PRINTIFY_API_KEY')}",
	"Content-Type": "application/json",
}

class PrintifyService:
	def __init__(self, name: str, shop_id: str):
		"""
		Initialize the Printify Service.
		
		Args:
			name: Arbitrary descriptor for this service instance
			shop_id: Your Printify shop ID, e.g., '20434486'
		"""
		self.name = name
		self.shop_id = shop_id
		self.client = PrintifyClient()

	def upload_image(self, image_path: str) -> Optional[Dict[str, Any]]:
		"""
		Upload an image to Printify.
		
		Args:
			image_path: Path to the image file
			
		Returns:
			Dict with image data including ID if successful, None otherwise
		"""
		return self.client.upload_image(image_path)

	def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
		"""
		Get product details from Printify.
		
		Args:
			product_id: Printify product ID
			
		Returns:
			Dict with product data if successful, None otherwise
		"""
		return self.client.get_product(self.shop_id, product_id)

	def publish_product(self, product_id: str) -> bool:
		"""
		Publish a product on Printify.
		
		Args:
			product_id: Printify product ID
			
		Returns:
			True if successful, False otherwise
		"""
		# Required fields for publish request
		publish_data = {
			"title": True,
			"description": True,
			"tags": True,
			"variants": True,
			"images": True,
			"keyFeatures": True,
			"shipping_template": True
		}
		
		return self.client.publish_product(self.shop_id, product_id, publish_data)

	def generate_sku(self, length: int = 18) -> str:
		"""
		Generate a random SKU with the specified length.
		
		Args:
			length: Length of the SKU to generate
			
		Returns:
			Random SKU string
		"""
		return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

	def duplicate_product_for_id(self, product_id: str) -> Optional[str]:
		"""
		Duplicate a product with a new ID.
		
		Args:
			product_id: Printify product ID to duplicate
			
		Returns:
			New product ID if successful, None otherwise
		"""
		# Get product details
		product_details = self.get_product_details(product_id)

		if not product_details:
			print("Could not retrieve product details. Exiting.")
			return None
			
		# Update SKUs in variants with random numbers
		variants = product_details.get('variants', [])
		for variant in variants:
			original_sku = variant.get('sku', '')
			if original_sku:
				sku_length = len(original_sku)  # Maintain the same length for new SKU
				variant['sku'] = self.generate_sku(sku_length)

		# Create the duplicated product
		response = self.client.create_product(self.shop_id, product_details)
		
		if response:
			new_product_id = response.get('id')
			print(f"Product duplicated successfully! New product ID: {new_product_id}")
			return new_product_id
		
		return None

	def duplicate_product(self, product_id: str, new_image_id: Dict[str, Any], title: str, description: str) -> Optional[str]:
		"""
		Duplicate a product with new image, title, and description.
		
		Args:
			product_id: Printify product ID to duplicate
			new_image_id: Dict containing new image ID data
			title: New product title
			description: New product description
			
		Returns:
			New product ID if successful, None otherwise
		"""
		# Get product details
		product_details = self.get_product_details(product_id)

		if not product_details:
			print("Could not retrieve product details. Exiting.")
			return None

		# Update image IDs in print_areas (placeholders)
		for product in product_details.get('print_areas', []):
			for placeholder in product.get('placeholders', []):
				for image in placeholder.get('images', []):
					image['id'] = new_image_id['id']  # Update the image ID

		# Update SKUs in variants with random numbers
		variants = product_details.get('variants', [])
		for variant in variants:
			original_sku = variant.get('sku', '')
			if original_sku:
				sku_length = len(original_sku)  # Maintain the same length for new SKU
				variant['sku'] = self.generate_sku(sku_length)

		product_details['title'] = title
		product_details['description'] = description

		# Create the duplicated product
		response = self.client.create_product(self.shop_id, product_details)
		
		if response:
			new_product_id = response.get('id')
			print(f"Product duplicated successfully! New product ID: {new_product_id}")
			return new_product_id
		
		return None

	def duplicate_product_from_model(self, product_model: PrintifyProductModel) -> Optional[str]:
		"""
		Creates a new product on Printify (duplicates locally stored model),
		matching the official product properties schema from Printify.
		
		Args:
			product_model: PrintifyProductModel to duplicate
			
		Returns:
			New product ID if successful, None otherwise
		"""
		# Build the core product_details structure
		product_details = {
			"title": product_model.title,
			"description": product_model.description,
			"blueprint_id": product_model.blueprint_id,
			"print_provider_id": product_model.print_provider_id,
			"tags": [],
			"variants": [],
			"print_areas": []
		}

		# 1) Add tags
		for tag_model in product_model.tags:
			product_details["tags"].append(tag_model.tag)

		# 2) Variants
		for variant_model in product_model.variants:
			var_data = variant_model.data
			if not isinstance(var_data, dict):
				continue
			variant_id = var_data.get("id")
			price = var_data.get("price")
			if variant_id is None or price is None:
				continue
			sku = var_data.get("sku")
			is_enabled = var_data.get("is_enabled", True)
			is_default = var_data.get("is_default", False)
			variant_payload = {
				"id": variant_id,
				"price": price,
				"sku": sku,
				"is_enabled": is_enabled,
				"is_default": is_default
			}
			product_details["variants"].append(variant_payload)

		# 3) Print Areas
		for pa_model in product_model.print_areas:
			pa_data = pa_model.data
			if not isinstance(pa_data, dict):
				continue
			variant_ids = pa_data.get("variant_ids", [])
			placeholders = pa_data.get("placeholders", [])

			pa_payload = {
				"variant_ids": variant_ids,
				"placeholders": []
			}
			for placeholder in placeholders:
				position = placeholder.get("position")
				images_list = placeholder.get("images", [])
				ph_payload = {
					"position": position,
					"images": images_list
				}
				pa_payload["placeholders"].append(ph_payload)

			product_details["print_areas"].append(pa_payload)

		# 4) Optional: print_details
		if hasattr(product_model, "print_details") and product_model.print_details:
			product_details["print_details"] = product_model.print_details

		# 5) External (for shipping_template_id, etc.)
		if product_model.external and isinstance(product_model.external.data, dict):
			product_details["external"] = [product_model.external.data]

		# 6) Sales channel properties
		if hasattr(product_model, "sales_channel_properties") and product_model.sales_channel_properties:
			scp_data_list = []
			for scp_model in product_model.sales_channel_properties:
				scp_data = scp_model.data
				if isinstance(scp_data, dict):
					scp_data_list.append(scp_data)
			if scp_data_list:
				product_details["sales_channel_properties"] = scp_data_list[0]

		# Now make the POST request to create the product
		response = self.client.create_product(self.shop_id, product_details)
		
		if response:
			new_product_id = response.get("id")
			print(f"Product duplicated successfully from model! New product ID: {new_product_id}")
			return new_product_id
		
		return None

	def delete_product(self, product_id: str) -> bool:
		"""
		Delete a product from Printify.
		
		Args:
			product_id: Printify product ID
			
		Returns:
			True if successful, False otherwise
		"""
		return self.client.delete_product(self.shop_id, product_id)

	def get_printify_mockup(self, product_id: str, mockup_index: int = 75, save_folder: str = "~/test_mocks") -> Optional[str]:
		"""
		Download a mockup image for a product.
		
		Args:
			product_id: Printify product ID
			mockup_index: Index of the mockup image to download (default is 75)
			save_folder: Folder to save the mockup image
			
		Returns:
			Path to the saved mockup image if successful, None otherwise
		"""
		# Ensure save directory exists
		save_folder = os.path.expanduser(save_folder)
		os.makedirs(save_folder, exist_ok=True)

		# Fetch product details from Printify
		product_data = self.get_product_details(product_id)
		
		if not product_data:
			return None

		mockups = product_data.get("images", [])

		# Ensure there are at least mockup_index+1 mockups
		if len(mockups) <= mockup_index:
			print(f"Error: The product does not have a {mockup_index+1}th mockup.")
			return None

		# Get the mockup image URL
		mockup_url = mockups[mockup_index]["src"]
		image_response = requests.get(mockup_url, stream=True)

		if image_response.status_code == 200:
			image_filename = os.path.join(save_folder, f"{product_id}_mockup_{mockup_index+1}.jpg")
			with open(image_filename, "wb") as file:
				for chunk in image_response.iter_content(1024):
					file.write(chunk)
			print(f"Mockup saved: {image_filename}")
			return image_filename
		else:
			print(f"Failed to download the mockup: {image_response.status_code}")
			return None
