"""
WSGI configuration for PythonAnywhere deployment
This file is used by PythonAnywhere to run the FastAPI application
"""

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/HackOHIO/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables if needed
os.environ['PYTHONUNBUFFERED'] = '1'

# Import the FastAPI app
from main_weather import app

# PythonAnywhere expects a variable called 'application'
application = app
