from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from datetime import datetime, timedelta
import math

from config.db_connection import DBConnection
from dao.template_dao import TemplateDAO
from services.printify_service import PrintifyService
from models.printify_template_models import PrintifyTagModel

# Create template blueprint
template_bp = Blueprint('template', __name__, template_folder='../dashboard/templates')

# Cache for mockup images
mockup_cache = {}

# Default shop ID
DEFAULT_SHOP_ID = "20510104"

# Number of templates per page
TEMPLATES_PER_PAGE = 12

@template_bp.route('/dashboard')
def dashboard():
    """Template dashboard that displays template statistics and recent templates"""
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
        tag_counts = {}
        
        for template in recent_templates:
            for tag in template.tags:
                if tag and hasattr(tag, 'tag') and tag.tag:
                    unique_tags.add(tag.tag)
                    tag_counts[tag.tag] = tag_counts.get(tag.tag, 0) + 1
        
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
            "unique_tags": len(unique_tags),
            "tag_counts": tag_counts
        }
        
        # Include current year for copyright in footer
        now = datetime.now()
        
        return render_template('template_dashboard.html', stats=stats, recent_templates=templates_for_display, now=now)
    
    finally:
        # Close the database connection
        db_conn.close()

@template_bp.route('/templates')
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
        
        return render_template('templates.html', 
                              templates=templates_for_display, 
                              page=page, 
                              total_pages=total_pages, 
                              search=search,
                              now=now)
    
    finally:
        # Close the database connection
        db_conn.close()

@template_bp.route('/template/<template_id>')
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
            return redirect(url_for('template.templates'))
    
    finally:
        # Close the database connection
        db_conn.close()

@template_bp.route('/api/templates')
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
        templates_json = []
        
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
            
            # Format dates as strings
            created_at = template.created_at
            if isinstance(created_at, str):
                try:
                    created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
            elif isinstance(created_at, datetime):
                created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            updated_at = template.updated_at
            if isinstance(updated_at, str):
                try:
                    updated_at = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
            elif isinstance(updated_at, datetime):
                updated_at = updated_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # Add to the display list
            templates_json.append({
                "id": template_id,
                "title": template.title or "Untitled Template",
                "description": template.description or "No description",
                "mockup_url": mockup_url,
                "created_at": created_at,
                "updated_at": updated_at,
                "tags": [tag.tag for tag in template.tags if tag and hasattr(tag, 'tag') and tag.tag]
            })
        
        # Return JSON response
        return jsonify({
            "templates": templates_json,
            "page": page,
            "total_pages": total_pages,
            "total_templates": total_templates
        })
    
    finally:
        # Close the database connection
        db_conn.close()

@template_bp.route('/template/<template_id>/edit', methods=['GET'])
def edit_template(template_id):
    """Display form for editing a template"""
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        template_dao = TemplateDAO(db_conn)
        
        # Get the template
        try:
            template = template_dao.fetch_template_from_template_id(template_id)
            
            # Format the template data for the form
            template_data = {
                "id": template.id,
                "title": template.title or "",
                "description": template.description or "",
                "blueprint_id": template.blueprint_id,
                "print_provider_id": template.print_provider_id,
                "user_id": template.user_id,
                "shop_id": template.shop_id,
                "visible": template.visible,
                "is_locked": template.is_locked,
                "reviewed": template.reviewed,
                "tags": [tag.tag for tag in template.tags if tag and tag.tag],
                "variants": [var.data for var in template.variants],
                "print_areas": [pa.data for pa in template.print_areas],
                "options": [opt.data for opt in template.options],
                "images": [img.data for img in template.images],
                "external": template.external.data if template.external else None,
                "sales_channel_properties": [scp.data for scp in template.sales_channel_properties],
                "files": [f.data for f in template.files],
                "additional_options": [ao.data for ao in template.additional_options],
                "selling_prices": [sp.data for sp in template.selling_prices],
                "views": [view.data for view in template.views],
            }
            
            # Include current year for copyright in footer
            now = datetime.now()
            
            return render_template('edit_template.html', template=template_data, now=now)
            
        except ValueError as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('template.templates'))
    
    finally:
        # Close the database connection
        db_conn.close()

@template_bp.route('/template/<template_id>/edit', methods=['POST'])
def update_template(template_id):
    """Handle template update form submission"""
    # Connect to the database
    db_conn = DBConnection(host="localhost", user="root", password="", database="print_core_db")
    db_conn.connect()
    
    try:
        # Initialize the DAO
        template_dao = TemplateDAO(db_conn)
        
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        blueprint_id = request.form.get('blueprint_id')
        print_provider_id = request.form.get('print_provider_id')
        user_id = request.form.get('user_id')
        shop_id = request.form.get('shop_id')
        visible = request.form.get('visible') == 'true'
        is_locked = request.form.get('is_locked') == 'true'
        reviewed = request.form.get('reviewed') == 'true'
        tags = request.form.getlist('tags[]')
        
        # Update the template
        try:
            template = template_dao.fetch_template_from_template_id(template_id)
            
            # Update basic fields
            template.title = title
            template.description = description
            template.blueprint_id = int(blueprint_id) if blueprint_id else None
            template.print_provider_id = int(print_provider_id) if print_provider_id else None
            template.user_id = int(user_id) if user_id else None
            template.shop_id = int(shop_id) if shop_id else None
            template.visible = visible
            template.is_locked = is_locked
            template.reviewed = reviewed
            
            # Update tags
            template.tags = [PrintifyTagModel(template_id, tag) for tag in tags if tag]
            
            # Save the template
            template_dao.update_template(template)
            
            flash("Template updated successfully!", "success")
            return redirect(url_for('template.template_detail', template_id=template_id))
            
        except ValueError as e:
            flash(f"Error updating template: {str(e)}", "error")
            return redirect(url_for('template.edit_template', template_id=template_id))
            
    finally:
        # Close the database connection
        db_conn.close() 