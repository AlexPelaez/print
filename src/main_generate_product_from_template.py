from services.printify_service import PrintifyService
from services.open_ai_service import OpenAiService
from services.product_generator_service import ProductGeneratorService
from config.db_connection import DBConnection
from models.printify_template_models import PrintifyTemplateModel
from dao.template_dao import TemplateDAO
from dao.product_dao import ProductDAO
from mappers.template_product_mapper import TemplateProductMapper



product_id = '67a1c8af8a72c38bef02bb46'  # Replace with the product ID to duplicate
shop_id = "20510104"

def main():
	product_generator_service = ProductGeneratorService(name="ProductGeneratorService")
	printify_service = PrintifyService(name="PrintifyService", shop_id=shop_id)

	db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
	db_conn.connect()
	template_dao = TemplateDAO(db_conn)
	product_dao = ProductDAO(db_conn)


	template = template_dao.fetch_template_from_template_id(product_id)

	# new_product_id = printify_service.duplicate_product_for_id(product_id)
	# print("here", new_product_id)


	new_product = TemplateProductMapper.map_template_to_product(template)
	new_product = TemplateProductMapper.replace_product_title(new_product, "test title")
	new_product = TemplateProductMapper.replace_product_description(new_product, "test description")
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
