#!/home/emily/Desktop/School/Fall-26/Capstone/LLM_Prompt_Injection_Capstone/.venv/bin/python3
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
