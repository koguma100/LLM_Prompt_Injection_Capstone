# Run the web app from the code/ directory with: python -m webapp
from webapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
