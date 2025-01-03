import sys
import os

# Set the path to your project and virtual environment
project_home = '/home/g304975/test.nyxmedia.es'
venv_path = '/home/g304975/virtualenv/test.nyxmedia.es'

# Add the project directory to the Python path
sys.path.insert(0, project_home)

# Set the Python interpreter from the virtual environment
os.environ['PYTHONHOME'] = venv_path
os.environ['PATH'] = f"{venv_path}/bin:" + os.environ['PATH']

# Import and initialize the Flask application
from server import application  # Adjust this import based on your app structure
