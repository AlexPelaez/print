from services.printify_service import PrintifyService
from config.db_connection import DBConnection
from models.printify_template_models import PrintifyTemplateModel
from dao.template_dao import TemplateDAO

product_id = '67cfca8600271d354f0a1f70'  # Replace with the product ID to duplicate
shop_id = "20510104"

def main():
	printify_service = PrintifyService(name="PrintifyService", shop_id=shop_id)
	db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
	db_conn.connect()

	template_dao = TemplateDAO(db_conn)

	template_data = printify_service.get_product_details(product_id)
	print(template_data)

	if not template_data:
		print("No product data found.")
		return


	# 1) Convert raw JSON to our model
	template_model = PrintifyTemplateModel.from_dict(template_data)
	print("hey hey hey here")
	# print(template_model.print_string_verbose())

	# # 2) Store it in DB
	template_dao.insert_or_update_template(template_model)

	template_dao.set_status_by_template_id(template_model.id, "TEMPLATE")

	# 3) Fetch if we want
	try:
		template_model_new = template_dao.fetch_template_from_template_id(product_id)
		print("we here")
		print(template_model_new.print_string_verbose())
		# print("Fetched template:", template_model_new.title, template_model_new.id)
		# print("Number of variants:", len(template_model_new.variants))
		# new_id = printify_service.duplicate_product_from_model(product_model_new)
		# print("New ID: ", new_id)
		# ... further logic ...
	except ValueError as e:
		print(e)

	db_conn.close()



if __name__ == "__main__":
	main()
