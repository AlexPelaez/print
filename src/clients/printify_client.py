import requests
import os
import base64
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("PRINTIFY_API_KEY")
BASE_URL = "https://api.printify.com/v1"

class PrintifyClient:
    """
    Client for interacting with the Printify API.
    Handles all direct API calls.
    """
    
    def __init__(self):
        """Initialize the Printify client with API key from environment variables."""
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        self.base_url = BASE_URL
    
    def upload_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Upload an image to Printify.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict with image data including ID if successful, None otherwise
        """
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
            upload_url = f"{self.base_url}/uploads/images.json"
            response = requests.post(upload_url, headers=self.headers, json=data)

            if response.status_code == 200:
                print("Image uploaded successfully!")
                return response.json()
            else:
                print(f"Error uploading image: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"An error occurred during image upload: {e}")
            return None
    
    def get_product(self, shop_id: str, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a product from Printify.
        
        Args:
            shop_id: Printify shop ID
            product_id: Printify product ID
            
        Returns:
            Dict with product data if successful, None otherwise
        """
        fetch_url = f"{self.base_url}/shops/{shop_id}/products/{product_id}.json"
        response = requests.get(fetch_url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching product: {response.status_code} - {response.text}")
            return None
    
    def create_product(self, shop_id: str, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new product on Printify.
        
        Args:
            shop_id: Printify shop ID
            product_data: Dict with product data
            
        Returns:
            Dict with new product data if successful, None otherwise
        """
        create_url = f"{self.base_url}/shops/{shop_id}/products.json"
        response = requests.post(create_url, headers=self.headers, json=product_data)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error creating product: {response.status_code} - {response.text}")
            return None
    
    def publish_product(self, shop_id: str, product_id: str, publish_data: Dict[str, Any]) -> bool:
        """
        Publish a product on Printify.
        
        Args:
            shop_id: Printify shop ID
            product_id: Printify product ID
            publish_data: Dict with publish options
            
        Returns:
            True if successful, False otherwise
        """
        publish_url = f"{self.base_url}/shops/{shop_id}/products/{product_id}/publish.json"
        response = requests.post(publish_url, headers=self.headers, json=publish_data)

        if response.status_code == 200:
            return True
        else:
            print(f"Error publishing product: {response.status_code} - {response.text}")
            return False
    
    def delete_product(self, shop_id: str, product_id: str) -> bool:
        """
        Delete a product from Printify.
        
        Args:
            shop_id: Printify shop ID
            product_id: Printify product ID
            
        Returns:
            True if successful, False otherwise
        """
        delete_url = f"{self.base_url}/shops/{shop_id}/products/{product_id}.json"
        response = requests.delete(delete_url, headers=self.headers)

        if response.status_code == 200:
            return True
        else:
            print(f"Error deleting product: {response.status_code} - {response.text}")
            return False
    
    def get_mockup_image(self, shop_id: str, product_id: str, image_index: int = 0) -> Optional[str]:
        """
        Get mockup image URL for a product.
        
        Args:
            shop_id: Printify shop ID
            product_id: Printify product ID
            image_index: Index of the mockup image to retrieve
            
        Returns:
            Image URL if successful, None otherwise
        """
        product_data = self.get_product(shop_id, product_id)
        
        if not product_data:
            return None
            
        mockups = product_data.get("images", [])
        
        if not mockups or image_index >= len(mockups):
            print(f"Error: No mockup at index {image_index}")
            return None
            
        return mockups[image_index]["src"] 