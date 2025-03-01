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

BASE_URL = "https://api.printify.com/v1"

# Headers for the API requests
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


class PrintifyService:
    def __init__(self, name, shop_id):
        """
        :param name: Arbitrary descriptor for this service instance.
        :param shop_id: Your Printify shop ID, e.g., '20434486'.
        """
        self.name = name
        self.shop_id = shop_id

        # Common endpoints
        self.upload_image_url = f"{BASE_URL}/uploads/images.json"
        self.create_product_url = f"{BASE_URL}/shops/{self.shop_id}/products.json"

    def upload_image(self, image_path):
        try:
            # Ensure the file exists
            if not os.path.exists(image_path):
                print(f"File does not exist: {image_path}")
                return None

            # Extract the file name from the path
            file_name = os.path.basename(image_path)

            # Open the image file in binary mode and encode it to Base64
            with open(image_path, 'rb') as image_file:
                encoded_contents = base64.b64encode(image_file.read()).decode('utf-8')

            # Prepare the data with Base64-encoded contents
            data = {
                'file_name': file_name,
                'contents': encoded_contents
            }

            # Send the request to upload the image
            response = requests.post(self.upload_image_url, headers=headers, json=data)

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
        fetch_product_details_url = f"{BASE_URL}/shops/{self.shop_id}/products/{product_id}.json"
        response = requests.get(fetch_product_details_url, headers=headers)

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

        # Publish the product
        publish_url = f"{BASE_URL}/shops/{self.shop_id}/products/{product_id}/publish.json"
        response = requests.post(publish_url, json=publish_data, headers=headers)

        if response.status_code == 200:
            print(f"Product {product_id} published successfully!")
        else:
            print(f"Error publishing product: {response.status_code} - {response.text}")

    def generate_sku(self, length=18):
        """Generate a random SKU with the specified length (default 18 digits)."""
        return ''.join(random.choices(string.digits, k=length))

    def duplicate_product(self, product_id, new_image_id, title, description):
        # Get product details
        product_details = self.get_product_details(product_id)

        if not product_details:
            print("Could not retrieve product details. Exiting.")
            return

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
        response = requests.post(self.create_product_url, json=product_details, headers=headers)

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
        response = requests.post(self.create_product_url, json=product_details, headers=headers)

        if response.status_code == 200:
            new_product_id = response.json().get("id")
            print(f"Product duplicated successfully from model! New product ID: {new_product_id}")
            return new_product_id
        else:
            print(f"Error creating new product: {response.status_code} - {response.text}")
            return None

    def delete_product(self, product_id):
        """Deletes a product from Printify."""
        delete_url = f"{BASE_URL}/shops/{self.shop_id}/products/{product_id}.json"
        response = requests.delete(delete_url, headers=headers)

        if response.status_code == 200:
            print(f"Product {product_id} deleted successfully!")
        else:
            print(f"Error deleting product: {response.status_code} - {response.text}")

    def get_printify_mockup(self, product_id, save_folder="~/test_mocks"):
        # Ensure save directory exists
        save_folder = os.path.expanduser(save_folder)
        os.makedirs(save_folder, exist_ok=True)

        # Fetch product details from Printify
        fetch_product_url = f"{BASE_URL}/shops/{self.shop_id}/products/{product_id}.json"
        response = requests.get(fetch_product_url, headers=headers)

        if response.status_code == 200:
            product_data = response.json()
            mockups = product_data.get("images", [])

            # Ensure there are at least 76 mockups
            if len(mockups) < 76:
                print("Error: The product does not have a 76th mockup.")
                return

            # Get the 76th mockup image URL
            mockup_url = mockups[75]["src"]
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
