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


product_id = '67a1c8af8a72c38bef02bb46'  # Replace with the product ID to duplicate
shop_id = "20510104"
image_folder = "/Users/alex/git/print/working_images_vertical" 

def main():
	openai_client = OpenAIClient()

	text_generator = TextGenerator(openai_client)
	product_generator_service = ProductGeneratorService(name="ProductGeneratorService")
	printify_service = PrintifyService(name="PrintifyService", shop_id=shop_id)

	db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
	db_conn.connect()
	template_dao = TemplateDAO(db_conn)
	product_dao = ProductDAO(db_conn)


	# Fetch template from the database
	template = template_dao.fetch_template_from_template_id(product_id)

	# Map template to new product
	new_product = TemplateProductMapper.map_template_to_product(template) # Folder where images are stored

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
			new_image_id = printify_service.upload_image(image_path)

			new_description = text_generator.generate_product_description("trippy mandlebrot set inspired design with crazy trippy patterns", "Amazon", "iphone 16 case")
			new_title = text_generator.generate_product_title(new_description, "Amazon", "iphone 16 case")

			print("New Title: ", new_title)
			print("new Description: ", new_description)

			# Generate bullet points for the product
			print("Generating bullet points...")
			bullet_points = text_generator.generate_product_bullets(new_description, "Amazon", "iphone 16 case")
			for i, bullet_point in enumerate(bullet_points, 1):
				print(f"Bullet point {i}: {bullet_point}")

			# Replace with custom product data
			new_product = TemplateProductMapper.replace_product_title(new_product, new_title)
			new_product = TemplateProductMapper.replace_product_description(new_product, new_description)
			new_product = TemplateProductMapper.replace_all_sku(new_product)
			new_product = TemplateProductMapper.replace_all_image_ids(new_product, new_image_id)
			new_product = TemplateProductMapper.replace_product_bullet_points(new_product, bullet_points)
			# new_product = TemplateProductMapper.replace_product_id(new_product, new_product_id)
			print(new_product)
			new_id = printify_service.duplicate_product_from_model(new_product)
			print("New ID: ", new_id)
			
			product_dao.insert_or_update_product(new_product)

	db_conn.close()



if __name__ == "__main__":
	main()
