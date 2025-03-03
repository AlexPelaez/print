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



product_id = '67a1c8af8a72c38bef02bb46'  # Replace with the product ID to duplicate
shop_id = "20510104"

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
	new_product = TemplateProductMapper.map_template_to_product(template)


	new_description = text_generator.generate_product_description("trippy mandlebrot set inspired design with crazy trippy patterns", "Amazon", "iphone 16 case")
	new_title = text_generator.generate_product_title(new_description, "Amazon", "iphone 16 case")

	print("New Title: ", new_title)
	print("new Description: ", new_description)


	# Replace with custom product data
	new_product = TemplateProductMapper.replace_product_title(new_product, new_title)
	new_product = TemplateProductMapper.replace_product_description(new_product, new_description)
	new_product = TemplateProductMapper.replace_all_sku(new_product)
	# new_product = TemplateProductMapper.replace_product_id(new_product, new_product_id)



	print(new_product)

	

	new_id = printify_service.duplicate_product_from_model(new_product)
	print("New ID: ", new_id)
	
	product_dao.insert_or_update_product(new_product)


	

	# map to new product




	# template_data = service.get_product_details(product_id)
	# print(template_data)

	# if not template_data:
	# 	print("No product data found.")
	# 	return

	# # 1) Convert raw JSON to our model
	# template_model = PrintifyTemplateModel.from_dict(template_data)

	# # 2) Store it in DB
	# template_dao.insert_or_update_template(template_model)

	# template_dao.set_status_by_template_id(template_model.id, "DRAFT")

	# # 3) Fetch if we want
	# try:
	# 	template_model_new = template_dao.fetch_template_from_template_id(product_id)
	# 	print("Fetched template:", template_model_new.title, template_model_new.id)
	# 	print("Number of variants:", len(template_model_new.variants))
	# 	# new_id = service.duplicate_product_from_model(product_model_new)
	# 	# print("New ID: ", new_id)
	# 	# ... further logic ...
	# except ValueError as e:
	# 	print(e)

	db_conn.close()



if __name__ == "__main__":
	main()
