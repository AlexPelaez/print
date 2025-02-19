from printify_service import PrintifyService
from database_util import DatabaseUtil
from printify_product_models import PrintifyProductModel
# from video_util import VideoUtil
# from open_ai_service import OpenAiService
import uuid
import os
import random
from multiprocessing import Pool as ProcessPool


product_id = '67a325e52405f94e2707d5c8'  # Replace with the product ID to duplicate
image_folder = "/Users/alex/git/print/working_images_vertical"  # Folder where images are stored



def main():
	service = PrintifyService("MyPrintifyService")
	db_util = DatabaseUtil(
		host="localhost",
		user="root",
		password="",        # or your password
		database="print_core_db"
	)

	product_data = service.get_product_details(product_id)
	print(product_data)

	if not product_data:
		print("No product data found.")
		return

	# 1) Convert raw JSON to our model
	product_model = PrintifyProductModel.from_dict(product_data)

	# 2) Store it in DB
	db_util.insert_or_update_product(product_model)

	try:
		product_model_new = db_util.fetch_product_as_model(product_id)
		print("Fetched product:", product_model_new.title, product_model_new.id)
		print("Number of variants:", len(product_model_new.variants))
		new_id = service.duplicate_product_from_model(product_model_new)
		print("New ID: ", new_id)
		# ... further logic ...
	except ValueError as e:
		print(e)

	db_util.close()



if __name__ == "__main__":
	main()
