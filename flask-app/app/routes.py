from flask import Blueprint, render_template, request

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def home():
    response = None

    if request.method == "POST":
        prompt = request.form.get("prompt")
        data = request.form.get("data")

        # Replace with your processing logic
        response = f"Processed:\nPrompt: {prompt}\nData: {data}"

    return render_template("base.html", response=response)
