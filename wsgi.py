# /home/deployuser/bmxii_org_app/wsgi.py

import sys
import os

# Add your project directory to the sys.path
# This helps Python find your application modules
project_home = u'/home/deployuser/bmxii_org_app'
if project_home not in sys.path:
     sys.path.insert(0, project_home)

# Import your Flask app instance
# IMPORTANT: Replace 'your_main_app_file' with the actual Python file name
# where your Flask 'app = Flask(__name__)' instance is defined.
# For example:
# If your main app is in 'app.py' (e.g., app.py contains `app = Flask(__name__)`), use:
# from app import app
# If your app is structured as a package (e.g., in 'bmxii/__init__.py'), use:
# from bmxii import app  (assuming 'app' is the Flask instance name)
from app import app # <--- Adjust this line based on your app's structure!

# This line is specifically for Gunicorn to find your application
application = app