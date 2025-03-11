from flask import Flask, render_template, request, flash, redirect, url_for
import os
from services.printify_service import PrintifyService
from config.db_connection import DBConnection
from models.printify_template_models import PrintifyTemplateModel
from dao.template_dao import TemplateDAO

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Default shop IDs
SHOP_IDS = {
    "Printify Popup": "20434486",
    "Amazon": "20510104",
    "Ebay": "20496160"
}

@app.route('/', methods=['GET', 'POST'])
def save_template_to_db():
    if request.method == 'POST':
        product_id = request.form.get('product_id', '').strip()
        shop_id = request.form.get('shop_id', '').strip()
        
        if not product_id:
            flash('Please enter a product ID', 'error')
            return redirect(url_for('save_template_to_db'))
            
        if not shop_id:
            flash('Please enter a shop ID', 'error')
            return redirect(url_for('save_template_to_db'))
        
        try:
            result = process_template_to_db(product_id, shop_id)
            flash(result, 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('save_template_to_db'))
        
    return render_template('save_template_form.html', shop_ids=SHOP_IDS)

def process_template_to_db(product_id, shop_id):
    """Process the template saving to database"""
    printify_service = PrintifyService(name="PrintifyService", shop_id=shop_id)
    
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        template_dao = TemplateDAO(db_conn)

        # Fetch the template data from Printify
        template_data = printify_service.get_product_details(product_id)
        
        if not template_data:
            raise ValueError("No product data found.")

        # Convert raw JSON to our model
        template_model = PrintifyTemplateModel.from_dict(template_data)
        
        # Store it in DB
        template_dao.insert_or_update_template(template_model)
        template_dao.set_status_by_template_id(template_model.id, "DRAFT")
        
        # Fetch to verify
        template_model_new = template_dao.fetch_template_from_template_id(product_id)
        
        return f"Successfully saved template: {template_model_new.title} (ID: {template_model_new.id})"
    
    except Exception as e:
        raise e
    
    finally:
        db_conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
