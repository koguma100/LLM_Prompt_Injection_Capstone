import requests

def local_llm_call(user_prompt: str):
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "phi3:mini",
        "prompt": f"""Answer the following question in one short sentence. Keep it short and sweet. Do not generate new questions or instructions.

    Question: {user_prompt}

    Answer:""",
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 50,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"LLM call failed: {e}")
        return False

    return response.json()["response"]
