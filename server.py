# run.py

import sys
import os

# Add the app directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app import create_app

app = create_app()

application = app
if __name__ == "__main__":
    app.run(debug=True)
