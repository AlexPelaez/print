from flask import Flask, render_template, request, redirect, url_for, g, current_app
import os
import sys
from pathlib import Path
from datetime import datetime
import math
from jinja2 import ChoiceLoader, FileSystemLoader

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from config.db_connection import DBConnection
from dao.template_dao import TemplateDAO
from dao.product_dao import ProductDAO
from controllers import all_blueprints

# Create Flask app with standard template folder
app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)

# Set up custom template loader for multiple directories
base_path = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(base_path, 'templates')
products_path = os.path.join(base_path, 'products')
components_path = os.path.join(base_path, 'components')
dashboard_path = os.path.join(base_path, 'dashboard')
logged_out_path = os.path.join(base_path, 'logged_out')

# Create a choice loader with multiple template directories
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(template_path),
    FileSystemLoader(products_path),
    FileSystemLoader(components_path),
    FileSystemLoader(dashboard_path),
    FileSystemLoader(logged_out_path)
])

# Add hasattr function to Jinja2 environment
app.jinja_env.globals['hasattr'] = hasattr

# Add current_app to template context
@app.context_processor
def inject_current_app():
    return dict(current_app=current_app)

# Register all blueprints
for blueprint, url_prefix in all_blueprints:
    app.register_blueprint(blueprint, url_prefix=url_prefix)

@app.route('/')
def index():
    """Main homepage with navigation to templates and products"""
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAOs
        template_dao = TemplateDAO(db_conn)
        product_dao = ProductDAO(db_conn)
        
        # Get stats for the dashboard
        stats = {
            "total_templates": template_dao.count_templates(),
            "total_products": product_dao.count_products(),
            "published_products": product_dao.count_products(status="PUBLISHED"),
            "unique_tags": 0  # We'd need to count this across both templates and products
        }
        
        # Include current year for copyright in footer
        now = datetime.now()
        
        return render_template('index.html', stats=stats, now=now)
    
    finally:
        # Close the database connection
        db_conn.close()

# Redirects for backward compatibility
@app.route('/templates')
def templates_redirect():
    return redirect(url_for('template.templates'))

@app.route('/products')
def products_redirect():
    return redirect(url_for('product.products'))

@app.route('/dashboard')
def dashboard_redirect():
    return redirect(url_for('index'))

@app.route('/template/<template_id>')
def template_detail_redirect(template_id):
    return redirect(url_for('template.template_detail', template_id=template_id))

@app.route('/product/<product_id>')
def product_detail_redirect(product_id):
    return redirect(url_for('product.product_detail', product_id=product_id))

# Database connection handling
@app.before_request
def before_request():
    """Initialize database connection for the request"""
    # Store database connection in Flask's g object for the duration of the request
    g.db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    g.db_conn.connect()

@app.teardown_request
def teardown_request(exception):
    """Close database connection after request"""
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5002) 