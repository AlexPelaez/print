from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from datetime import datetime, timedelta
import math

from config.db_connection import DBConnection
from dao.product_dao import ProductDAO
from dao.template_dao import TemplateDAO
from services.printify_service import PrintifyService

# Create product blueprint
product_bp = Blueprint('product', __name__, template_folder='../dashboard/products')

# Cache for mockup images
mockup_cache = {}

# Default shop ID
DEFAULT_SHOP_ID = "20510104"

# Number of products per page
PRODUCTS_PER_PAGE = 12

@product_bp.route('/dashboard/home')
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
        
        return render_template('./logged_out/index.html', stats=stats, now=now)
    
    finally:
        # Close the database connection
        db_conn.close()

@product_bp.route('/dashboard')
def dashboard():
    """Product dashboard that displays product statistics and recent products"""
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        product_dao = ProductDAO(db_conn)
        
        # Get stats for the dashboard
        total_products = product_dao.count_products()
        published_products = product_dao.count_products(status="PUBLISHED")
        
        # Get recent products
        recent_products = product_dao.fetch_products_paginated(limit=6, offset=0)
        
        # Calculate average price
        avg_price = 0
        total_with_price = 0
        
        # Get unique tags and count them
        unique_tags = set()
        tag_counts = {}
        
        for product in recent_products:
            for tag in product.tags:
                if tag and hasattr(tag, 'tag') and tag.tag:
                    unique_tags.add(tag.tag)
                    if tag.tag in tag_counts:
                        tag_counts[tag.tag] += 1
                    else:
                        tag_counts[tag.tag] = 1
            
            # Add to average price calculation if the product has a price
            if hasattr(product, 'price') and product.price:
                try:
                    price_value = float(product.price)
                    avg_price += price_value
                    total_with_price += 1
                except (ValueError, TypeError):
                    pass
        
        # Calculate the average price if we have products with prices
        if total_with_price > 0:
            avg_price = avg_price / total_with_price
        
        # Format the recent products for display
        products_for_display = []
        
        # Initialize Printify service for mockups
        printify_service = PrintifyService(name="PrintifyService", shop_id=DEFAULT_SHOP_ID)
        
        for product in recent_products:
            # Check if we have a mockup image cached
            mockup_url = None
            product_id = product.id
            
            if product_id in mockup_cache:
                mockup_url = mockup_cache[product_id]
            else:
                # Try to fetch mockup from Printify
                try:
                    product_details = printify_service.get_product_details(product_id)
                    if product_details and "images" in product_details and len(product_details["images"]) > 0:
                        # Get the first mockup image
                        mockup_url = product_details["images"][0]["src"]
                        # Cache it
                        mockup_cache[product_id] = mockup_url
                except Exception as e:
                    print(f"Error fetching mockup for product {product_id}: {str(e)}")
            
            # Add to the display list
            products_for_display.append({
                "id": product_id,
                "title": product.title or "Untitled Product",
                "description": product.description or "No description",
                "mockup_url": mockup_url,
                "created_at": datetime.strptime(product.created_at, '%Y-%m-%d %H:%M:%S') if isinstance(product.created_at, str) else product.created_at,
                "updated_at": datetime.strptime(product.updated_at, '%Y-%m-%d %H:%M:%S') if isinstance(product.updated_at, str) else product.updated_at,
                "tags": product.tags,
                "status": product.status,
                "price": product.price
            })
        
        # Stats for the dashboard
        stats = {
            "total_products": total_products,
            "published_products": published_products,
            "unique_tags": len(unique_tags),
            "tag_counts": tag_counts,
            "avg_price": avg_price
        }
        
        # Include current year for copyright in footer
        now = datetime.now()
        
        return render_template('product_dashboard.html', stats=stats, recent_products=products_for_display, now=now)
    
    finally:
        # Close the database connection
        db_conn.close()

@product_bp.route('/products')
def products():
    """Display products with pagination"""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        product_dao = ProductDAO(db_conn)
        
        # Get total count of products for pagination
        total_products = product_dao.count_products(search_term=search, status=status)
        total_pages = math.ceil(total_products / PRODUCTS_PER_PAGE)
        
        # Calculate offset
        offset = (page - 1) * PRODUCTS_PER_PAGE
        
        # Get products for current page
        products_data = product_dao.fetch_products_paginated(
            limit=PRODUCTS_PER_PAGE, 
            offset=offset,
            search_term=search,
            status=status,
            sort_by=sort_by
        )
        
        # Log the products for debugging
        print(f"Found {len(products_data)} products for page {page}")
        
        # Format the data for display
        products_for_display = []
        
        # Initialize Printify service for mockups
        printify_service = PrintifyService(name="PrintifyService", shop_id=DEFAULT_SHOP_ID)
        
        for product in products_data:
            # Check if we have a mockup image cached
            mockup_url = None
            product_id = product.id
            
            if product_id in mockup_cache:
                mockup_url = mockup_cache[product_id]
            else:
                # Try to fetch mockup from Printify
                try:
                    product_details = printify_service.get_product_details(product_id)
                    if product_details and "images" in product_details and len(product_details["images"]) > 0:
                        # Get the first mockup image
                        mockup_url = product_details["images"][0]["src"]
                        # Cache it
                        mockup_cache[product_id] = mockup_url
                except Exception as e:
                    print(f"Error fetching mockup for product {product_id}: {str(e)}")
            
            # Add to the display list
            products_for_display.append({
                "id": product_id,
                "title": product.title or "Untitled Product",
                "description": product.description or "No description",
                "mockup_url": mockup_url,
                "created_at": datetime.strptime(product.created_at, '%Y-%m-%d %H:%M:%S') if isinstance(product.created_at, str) else product.created_at,
                "updated_at": datetime.strptime(product.updated_at, '%Y-%m-%d %H:%M:%S') if isinstance(product.updated_at, str) else product.updated_at,
                "tags": product.tags,
                "status": product.status,
                "price": product.price
            })
        
        # Include current year for copyright in footer
        now = datetime.now()
        
        return render_template('products.html', 
                              products=products_for_display, 
                              page=page, 
                              total_pages=total_pages, 
                              search=search,
                              status=status,
                              sort_by=sort_by,
                              now=now)
    
    finally:
        # Close the database connection
        db_conn.close()

@product_bp.route('/product/<product_id>')
def product_detail(product_id):
    """Display details for a specific product"""
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        product_dao = ProductDAO(db_conn)
        
        # Get the product details
        product = product_dao.get_product_by_id(product_id)
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('product.products'))
        
        # Initialize Printify service for mockups
        printify_service = PrintifyService(name="PrintifyService", shop_id=DEFAULT_SHOP_ID)
        
        # Try to fetch mockup from Printify
        mockup_urls = []
        try:
            product_details = printify_service.get_product_details(product_id)
            if product_details and "images" in product_details:
                for image in product_details["images"]:
                    mockup_urls.append(image["src"])
        except Exception as e:
            print(f"Error fetching mockups for product {product_id}: {str(e)}")
        
        # Include current year for copyright in footer
        now = datetime.now()
        
        return render_template('product_detail.html', 
                              product=product, 
                              mockup_urls=mockup_urls,
                              now=now)
    
    finally:
        # Close the database connection
        db_conn.close()

@product_bp.route('/edit/<product_id>')
def edit_product(product_id):
    """Display form to edit a product"""
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        product_dao = ProductDAO(db_conn)
        
        # Get the product details
        product = product_dao.get_product_by_id(product_id)
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('product.products'))
        
        # Include current year for copyright in footer
        now = datetime.now()
        
        return render_template('edit_product.html', 
                              product=product,
                              now=now)
    
    finally:
        # Close the database connection
        db_conn.close()

@product_bp.route('/update/<product_id>', methods=['POST'])
def update_product(product_id):
    """Update a product"""
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        product_dao = ProductDAO(db_conn)
        
        # Get the product details
        product = product_dao.get_product_by_id(product_id)
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('product.products'))
        
        # Update product with form data
        product.title = request.form.get('title', product.title)
        product.description = request.form.get('description', product.description)
        product.blueprint_id = request.form.get('blueprint_id', product.blueprint_id)
        product.price = request.form.get('price', product.price)
        product.status = request.form.get('status', product.status)
        
        # Update tags if provided
        tags_input = request.form.get('tags', '')
        if tags_input:
            # Split by comma and create tag objects
            tag_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            product.tags = [{"tag": tag} for tag in tag_list]
        
        # Save the updated product
        product_dao.update_product(product)
        
        flash('Product updated successfully', 'success')
        return redirect(url_for('product.product_detail', product_id=product_id))
    
    finally:
        # Close the database connection
        db_conn.close()

@product_bp.route('/delete')
def delete_product():
    """Delete a product"""
    product_id = request.args.get('product_id')
    
    if not product_id:
        flash('Product ID is required', 'error')
        return redirect(url_for('product.products'))
    
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        product_dao = ProductDAO(db_conn)
        
        # Delete the product
        product_dao.delete_product(product_id)
        
        flash('Product deleted successfully', 'success')
        return redirect(url_for('product.products'))
    
    finally:
        # Close the database connection
        db_conn.close()

@product_bp.route('/publish')
def publish_product():
    """Publish a product"""
    product_id = request.args.get('product_id')
    
    if not product_id:
        flash('Product ID is required', 'error')
        return redirect(url_for('product.products'))
    
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        product_dao = ProductDAO(db_conn)
        
        # Get the product
        product = product_dao.get_product_by_id(product_id)
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('product.products'))
        
        # Update status
        product.status = "PUBLISHED"
        product_dao.update_product(product)
        
        flash('Product published successfully', 'success')
        return redirect(url_for('product.product_detail', product_id=product_id))
    
    finally:
        # Close the database connection
        db_conn.close()

@product_bp.route('/unpublish')
def unpublish_product():
    """Unpublish a product"""
    product_id = request.args.get('product_id')
    
    if not product_id:
        flash('Product ID is required', 'error')
        return redirect(url_for('product.products'))
    
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        product_dao = ProductDAO(db_conn)
        
        # Get the product
        product = product_dao.get_product_by_id(product_id)
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('product.products'))
        
        # Update status
        product.status = "DRAFT"
        product_dao.update_product(product)
        
        flash('Product unpublished successfully', 'success')
        return redirect(url_for('product.product_detail', product_id=product_id))
    
    finally:
        # Close the database connection
        db_conn.close() 