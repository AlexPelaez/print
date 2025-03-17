from services.printify_service import PrintifyService
from services.open_ai_service import OpenAiService
from clients.open_ai_client import OpenAIClient
from services.product_generator_service import ProductGeneratorService
from config.db_connection import DBConnection
from models.printify_template_models import PrintifyTemplateModel
from dao.template_dao import TemplateDAO
from dao.product_dao import ProductDAO
from mappers.template_product_mapper import TemplateProductMapper
from util.text_generator_util import TextGenerator
import os
from concurrent.futures import ThreadPoolExecutor


product_id = '67cfca8600271d354f0a1f70'  # Replace with the product ID to duplicate
shop_id = "20510104"
image_folder = "/Users/alex/git/print/working_images_vertical" 

def process_image(image_name, image_folder, text_generator, printify_service, template, product_dao):
	try:
		image_path = os.path.join(image_folder, image_name)
		
		# Check if the file is an image
		if not (os.path.isfile(image_path) and image_name.lower().endswith(('.png', '.jpg', '.jpeg'))):
			return
			
		print(f"\nProcessing image: {image_name}")
		
		# Upload the new image to Printify
		print("Uploading image to Printify...")
		new_image_id = printify_service.upload_image(image_path)
		if not new_image_id:
			print("Failed to upload image to Printify")
			return
		print(f"Image uploaded successfully, got image ID: {new_image_id}")
		
		print("\nGenerating product content...")
		new_description = text_generator.generate_product_description("trippy mandlebrot set inspired design with crazy trippy patterns", "Amazon", "iphone 16 case")
		new_title = text_generator.generate_product_title(new_description, "Amazon", "phone case")
		
		print(f"Generated Title: {new_title}")
		print(f"Generated Description: {new_description}")
		
		# Generate bullet points for the product
		print("\nGenerating bullet points...")
		bullet_points = text_generator.generate_product_bullets(new_description, "Amazon", "phone case")
		for i, bullet_point in enumerate(bullet_points, 1):
			print(f"Bullet point {i}: {bullet_point}")
		
		print("\nCreating product from template...")
		# Map template to new product and replace with custom data
		new_product = TemplateProductMapper.map_template_to_product(template)
		if not new_product:
			print("Failed to map template to product")
			return
			
		new_product = TemplateProductMapper.replace_product_title(new_product, new_title)
		new_product = TemplateProductMapper.replace_product_description(new_product, new_description)
		new_product = TemplateProductMapper.replace_all_sku(new_product)
		new_product = TemplateProductMapper.replace_all_image_ids(new_product, new_image_id)
		new_product = TemplateProductMapper.replace_product_bullet_points(new_product, bullet_points)
		
		# Verify product data before creating on Printify
		print("\nVerifying product data before Printify creation:")
		print(f"Title: {new_product.title}")
		print(f"Description length: {len(new_product.description or '')}")
		print(f"Number of variants: {len(new_product.variants)}")
		print(f"Number of images: {len(new_product.images)}")
		
		print("\nCreating product on Printify...")
		new_id = printify_service.duplicate_product_from_model(new_product)
		if not new_id:
			print("Failed to create product on Printify")
			return
		print(f"Successfully created product on Printify with ID: {new_id}")
		
		# Update the product with the new Printify ID
		new_product.id = new_id  # Set the external product ID (Printify ID)
		
		print("\nSaving product to database...")
		# Verify product has required fields before saving
		if not new_product.id:
			print("Error: Product ID is missing")
			return
			
		try:
			print("Product data being saved:")
			print(f"Product ID: {new_product.id}")
			print(f"Title: {new_product.title}")
			print(f"Description: {new_product.description[:100]}...")  # First 100 chars
			print(f"Blueprint ID: {new_product.blueprint_id}")
			print(f"Print Provider ID: {new_product.print_provider_id}")
			
			product_dao.insert_or_update_product(new_product)
			print(f"Successfully saved product {new_id} to database")
			
			# Verify the product was saved
			saved_product = product_dao.fetch_product_from_product_id(new_id)
			if saved_product:
				print("Successfully verified product in database")
			else:
				print("Warning: Product was not found in database after saving")
			
			# Set initial status as DRAFT
			product_dao.set_status_by_product_id(new_id, "DRAFT")
			print(f"Set product {new_id} status to DRAFT")
			
		except Exception as e:
			print(f"Error saving product to database: {e}")
			import traceback
			print("Full error:")
			print(traceback.format_exc())
			
	except Exception as e:
		print(f"Error in process_image: {e}")
		import traceback
		print("Full error:")
		print(traceback.format_exc())

def main():
	db_conn = None
	try:
		openai_client = OpenAIClient()
		text_generator = TextGenerator(openai_client)
		product_generator_service = ProductGeneratorService(name="ProductGeneratorService")
		printify_service = PrintifyService(name="PrintifyService", shop_id=shop_id)

		# Set up database connection
		db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
		db_conn.connect()
		template_dao = TemplateDAO(db_conn)
		product_dao = ProductDAO(db_conn)

		# Fetch template from the database
		template = template_dao.fetch_template_from_template_id(product_id)
		if not template:
			print(f"Error: Template not found for ID {product_id}")
			return

		# Check if the folder exists
		if not os.path.exists(image_folder):
			print(f"Error: Image folder '{image_folder}' not found.")
			return

		# Get list of image files in the folder
		image_files = [f for f in os.listdir(image_folder) 
					if os.path.isfile(os.path.join(image_folder, f)) 
					and f.lower().endswith(('.png', '.jpg', '.jpeg'))]
		
		if not image_files:
			print("No image files found in the folder.")
			return
			
		print(f"Found {len(image_files)} images to process")
		
		# Process images one at a time to avoid memory issues
		for image_name in image_files:
			process_image(
				image_name, 
				image_folder, 
				text_generator, 
				printify_service, 
				template, 
				product_dao
			)
			
		print("All images have been processed.")
		
	except Exception as e:
		print(f"An error occurred: {e}")
		import traceback
		print(traceback.format_exc())
		
	finally:
		# Always close the database connection
		if db_conn:
			try:
				db_conn.close()
				print("Database connection closed.")
			except Exception as e:
				print(f"Error closing database connection: {e}")

if __name__ == "__main__":
	main()
