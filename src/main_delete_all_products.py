from services.printify_service import PrintifyService
from config.db_connection import DBConnection
from dao.product_dao import ProductDAO
import os
from concurrent.futures import ThreadPoolExecutor

# Configure shop ID - using the same ID from the other file
shop_id = "20510104"

def delete_product(product_id, printify_id, printify_service, product_dao):
    """
    Delete a product from both Printify and the local database
    
    Args:
        product_id: The internal database ID of the product
        printify_id: The ID of the product in Printify
        printify_service: PrintifyService instance
        product_dao: ProductDAO instance
    """
    print(f"Deleting product: {product_id} (Printify ID: {printify_id})")
    
    # First delete from Printify if there's a valid ID
    if printify_id:
        try:
            success = printify_service.delete_product(printify_id)
            if success:
                print(f"Successfully deleted product from Printify: {printify_id}")
            else:
                print(f"Failed to delete product from Printify: {printify_id}")
        except Exception as e:
            print(f"Error deleting product from Printify: {e}")
    
    # Then delete from database regardless of Printify success
    # (to ensure we clean up the DB even if Printify deletion fails)
    try:
        success = product_dao.delete_product(product_id)
        if success:
            print(f"Successfully deleted product from database: {product_id}")
        else:
            print(f"Failed to delete product from database: {product_id}")
    except Exception as e:
        print(f"Error deleting product from database: {e}")

def main():
    db_conn = None
    try:
        # Initialize services
        printify_service = PrintifyService(name="PrintifyService", shop_id=shop_id)
        
        # Set up database connection
        db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
        db_conn.connect()
        product_dao = ProductDAO(db_conn)
        
        # Fetch all products from the database
        products = product_dao.fetch_all_products()
        
        if not products:
            print("No products found in the database.")
            return
        
        print(f"Found {len(products)} products to delete")
        
        # Confirm deletion
        confirmation = input(f"Are you sure you want to delete all {len(products)} products? (yes/no): ")
        if confirmation.lower() != "yes":
            print("Operation cancelled.")
            return
        
        # Process deletions one at a time to avoid memory issues
        for product in products:
            product_id = product.get('id')  # Internal database ID
            printify_id = product.get('printify_id')  # External Printify ID
            
            if not product_id:
                print(f"Warning: Skipping product with no internal ID: {product}")
                continue
                
            delete_product(product_id, printify_id, printify_service, product_dao)
        
        print("All products have been processed.")
        
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