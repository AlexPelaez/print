from services.printify_service import PrintifyService
from config.db_connection import DBConnection
from dao.product_dao import ProductDAO


# This takes a product from the DB (currently stored as a draft on prinitfy) and publishes to the printify store
def main():
	service = PrintifyService(name="MyServiceInstance", shop_id="20434486")


	# 1) Initialize DBConnection
	db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
	db_conn.connect()

	# 2) Create DAO instances
	product_dao = ProductDAO(db_conn)



	try:
		max_draft_id = product_dao.fetch_max_draft_product_id()

		if max_draft_id is not None:
		    print(f"Maximum DRAFT product ID is {max_draft_id}")
		else:
		    print("No product is in DRAFT status.")

		service.publish_product(max_draft_id)
		print("Published Product: ", max_draft_id)
		product_dao.set_status_by_product_id(max_draft_id, "PUBLISHED")
		print("Product: {} marked as published", max_draft_id)

		product_dao.close()
	except ValueError as e:
		print(e)	



if __name__ == "__main__":
	main()
