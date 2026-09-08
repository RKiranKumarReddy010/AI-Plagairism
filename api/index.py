import os
import sys

# Ensure root directory is on Python path so 'src' can be resolved
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
