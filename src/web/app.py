from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import sys
import math
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from config.db_connection import DBConnection
from dao.template_dao import TemplateDAO
from services.printify_service import PrintifyService

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Default shop IDs
SHOP_IDS = {
    "Printify Popup": "20434486",
    "Amazon": "20510104",
    "Ebay": "20496160"
}

# Default shop ID to use
DEFAULT_SHOP_ID = "20510104"

# Number of templates per page
TEMPLATES_PER_PAGE = 12


# Cache for mockup images (so we don't re-download them)
mockup_cache = {}


@app.route('/')
def index():
    """Homepage that displays templates from the database"""
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        template_dao = TemplateDAO(db_conn)
        
        # Get stats for the dashboard
        total_templates = template_dao.count_templates()
        
        # Calculate recent updates (in the last 7 days)
        # This would ideally use a SQL query but we'll simulate it here
        recent_templates = template_dao.fetch_templates_paginated(limit=6, offset=0)
        
        # Count recent updates
        recent_updates = 0
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Convert string dates to datetime objects for comparison
        for template in recent_templates:
            # Convert updated_at to datetime if it's a string
            if template.updated_at and isinstance(template.updated_at, str):
                try:
                    # Try different formats as needed
                    try:
                        template_date = datetime.strptime(template.updated_at, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        template_date = datetime.strptime(template.updated_at, '%Y-%m-%d')
                    if template_date > seven_days_ago:
                        recent_updates += 1
                except (ValueError, TypeError):
                    # Skip if we can't parse the date
                    pass
            elif template.updated_at and isinstance(template.updated_at, datetime):
                # If it's already a datetime object, compare directly
                if template.updated_at > seven_days_ago:
                    recent_updates += 1
        
        # Get unique tags
        unique_tags = set()
        for template in recent_templates:
            for tag in template.tags:
                if tag and hasattr(tag, 'tag') and tag.tag:
                    unique_tags.add(tag.tag)
        
        # Format the recent templates for display
        templates_for_display = []
        
        # Initialize Printify service for mockups
        printify_service = PrintifyService(name="PrintifyService", shop_id=DEFAULT_SHOP_ID)
        
        for template in recent_templates:
            # Check if we have a mockup image cached
            mockup_url = None
            template_id = template.id
            
            if template_id in mockup_cache:
                mockup_url = mockup_cache[template_id]
            else:
                # Try to fetch mockup from Printify
                try:
                    template_details = printify_service.get_product_details(template_id)
                    if template_details and "images" in template_details and len(template_details["images"]) > 0:
                        # Get the first mockup image
                        mockup_url = template_details["images"][0]["src"]
                        # Cache it
                        mockup_cache[template_id] = mockup_url
                except Exception as e:
                    print(f"Error fetching mockup for template {template_id}: {str(e)}")
            
            # Add to the display list
            templates_for_display.append({
                "id": template_id,
                "title": template.title or "Untitled Template",
                "description": template.description or "No description",
                "mockup_url": mockup_url,
                "created_at": datetime.strptime(template.created_at, '%Y-%m-%d %H:%M:%S') if isinstance(template.created_at, str) else template.created_at,
                "updated_at": datetime.strptime(template.updated_at, '%Y-%m-%d %H:%M:%S') if isinstance(template.updated_at, str) else template.updated_at,
                "tags": ', '.join([tag.tag for tag in template.tags if tag and hasattr(tag, 'tag') and tag.tag])
            })
        
        # Stats for the dashboard
        stats = {
            "total_templates": total_templates,
            "recent_updates": recent_updates,
            "unique_tags": len(unique_tags)
        }
        
        # Include current year for copyright in footer
        now = datetime.now()
        
        return render_template('index.html', stats=stats, recent_templates=templates_for_display, now=now)
    
    finally:
        # Close the database connection
        db_conn.close()


@app.route('/templates')
def templates():
    """Display templates with pagination"""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        template_dao = TemplateDAO(db_conn)
        
        # Get total count of templates for pagination
        total_templates = template_dao.count_templates(search_term=search)
        total_pages = math.ceil(total_templates / TEMPLATES_PER_PAGE)
        
        # Calculate offset
        offset = (page - 1) * TEMPLATES_PER_PAGE
        
        # Get templates for current page
        templates_data = template_dao.fetch_templates_paginated(
            limit=TEMPLATES_PER_PAGE, 
            offset=offset,
            search_term=search
        )
        
        # Log the templates for debugging
        print(f"Found {len(templates_data)} templates for page {page}")
        
        # Format the data for display
        templates_for_display = []
        
        # Initialize Printify service for mockups
        printify_service = PrintifyService(name="PrintifyService", shop_id=DEFAULT_SHOP_ID)
        
        for template in templates_data:
            # Check if we have a mockup image cached
            mockup_url = None
            template_id = template.id
            
            if template_id in mockup_cache:
                mockup_url = mockup_cache[template_id]
            else:
                # Try to fetch mockup from Printify
                try:
                    template_details = printify_service.get_product_details(template_id)
                    if template_details and "images" in template_details and len(template_details["images"]) > 0:
                        # Get the first mockup image
                        mockup_url = template_details["images"][0]["src"]
                        # Cache it
                        mockup_cache[template_id] = mockup_url
                except Exception as e:
                    print(f"Error fetching mockup for template {template_id}: {str(e)}")
            
            # Add to the display list
            templates_for_display.append({
                "id": template_id,
                "title": template.title or "Untitled Template",
                "description": template.description or "No description",
                "mockup_url": mockup_url,
                "created_at": datetime.strptime(template.created_at, '%Y-%m-%d %H:%M:%S') if isinstance(template.created_at, str) else template.created_at,
                "updated_at": datetime.strptime(template.updated_at, '%Y-%m-%d %H:%M:%S') if isinstance(template.updated_at, str) else template.updated_at,
                "tags": ', '.join([tag.tag for tag in template.tags if tag and hasattr(tag, 'tag') and tag.tag])
            })
        
        # Include current year for copyright in footer
        now = datetime.now()
        
        # Render the template page
        return render_template(
            'templates.html',
            templates=templates_for_display,
            page=page,
            total_pages=total_pages,
            search=search,
            now=now
        )
    
    finally:
        # Close the database connection
        db_conn.close()


@app.route('/template/<template_id>')
def template_detail(template_id):
    """Display details for a specific template"""
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        template_dao = TemplateDAO(db_conn)
        
        # Get the template
        try:
            template = template_dao.fetch_template_from_template_id(template_id)
            
            # Initialize Printify service for mockups
            printify_service = PrintifyService(name="PrintifyService", shop_id=DEFAULT_SHOP_ID)
            
            # Get mockup images
            mockup_images = []
            template_details = printify_service.get_product_details(template_id)
            
            if template_details and "images" in template_details:
                mockup_images = [img["src"] for img in template_details["images"]]
            
            # Format the template data for display
            template_data = {
                "id": template.id,
                "title": template.title or "Untitled Template",
                "description": template.description or "No description",
                "blueprint_id": template.blueprint_id,
                "print_provider_id": template.print_provider_id,
                "created_at": datetime.strptime(template.created_at, '%Y-%m-%d %H:%M:%S') if isinstance(template.created_at, str) else template.created_at,
                "updated_at": datetime.strptime(template.updated_at, '%Y-%m-%d %H:%M:%S') if isinstance(template.updated_at, str) else template.updated_at,
                "tags": ', '.join([tag.tag for tag in template.tags if tag and tag.tag]),
                "product_type": template.title.split(' - ')[0] if template.title else "Unknown",
                "variant_id": template.variants[0].data.get("id") if template.variants else None,
                "print_areas": [pa.data.get("position") for pa in template.print_areas] if template.print_areas else []
            }
            
            # Include current year for copyright in footer
            now = datetime.now()
            
            return render_template('template_detail.html', template=template_data, mockup_images=mockup_images, now=now)
        
        except ValueError as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('templates'))
    
    finally:
        # Close the database connection
        db_conn.close()


@app.route('/api/templates')
def api_templates():
    """API endpoint to get templates as JSON (for AJAX loading)"""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        template_dao = TemplateDAO(db_conn)
        
        # Get total count of templates for pagination
        total_templates = template_dao.count_templates(search_term=search)
        total_pages = math.ceil(total_templates / TEMPLATES_PER_PAGE)
        
        # Calculate offset
        offset = (page - 1) * TEMPLATES_PER_PAGE
        
        # Get templates for current page
        templates_data = template_dao.fetch_templates_paginated(
            limit=TEMPLATES_PER_PAGE, 
            offset=offset,
            search_term=search
        )
        
        # Format the data for display
        templates_for_display = []
        
        # Initialize Printify service for mockups
        printify_service = PrintifyService(name="PrintifyService", shop_id=DEFAULT_SHOP_ID)
        
        for template in templates_data:
            # Check if we have a mockup image cached
            mockup_url = None
            template_id = template.id
            
            if template_id in mockup_cache:
                mockup_url = mockup_cache[template_id]
            else:
                # Try to fetch mockup from Printify
                try:
                    template_details = printify_service.get_product_details(template_id)
                    if template_details and "images" in template_details and len(template_details["images"]) > 0:
                        # Get the first mockup image
                        mockup_url = template_details["images"][0]["src"]
                        # Cache it
                        mockup_cache[template_id] = mockup_url
                except Exception as e:
                    print(f"Error fetching mockup for template {template_id}: {str(e)}")
            
            # Add to the display list
            templates_for_display.append({
                "id": template_id,
                "title": template.title or "Untitled Template",
                "description": template.description or "No description",
                "mockup_url": mockup_url,
                "created_at": datetime.strptime(template.created_at, '%Y-%m-%d %H:%M:%S') if isinstance(template.created_at, str) else template.created_at,
                "updated_at": datetime.strptime(template.updated_at, '%Y-%m-%d %H:%M:%S') if isinstance(template.updated_at, str) else template.updated_at,
                "tags": [tag.tag for tag in template.tags]
            })
        
        # Return JSON response
        return jsonify({
            "templates": templates_for_display,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_templates
            }
        })
    
    finally:
        # Close the database connection
        db_conn.close()


if __name__ == '__main__':
    # Ensure the templates directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, port=5001) 