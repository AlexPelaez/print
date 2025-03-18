from .product_controller import product_bp
from .template_controller import template_bp
from .auth_controller import auth_bp

# List of all blueprints to be registered
all_blueprints = [
    (product_bp, '/product'),
    (template_bp, '/template'),
    (auth_bp, '/auth')
] 