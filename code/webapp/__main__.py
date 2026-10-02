# Run the web app from the code/ directory with: python -m webapp
# Set FLASK_DEBUG=1 for the debugger and auto-reload during development.
import os

from webapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
