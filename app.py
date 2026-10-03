from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload limit

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}


@app.route("/")
def home():
    return render_template("analyzer.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    image = request.files.get("image")
    repo_url = request.form.get("repo_url", "").strip()

    if not image or image.filename == "":
        return jsonify({"error": "Please choose a screenshot first."}), 400
    if image.mimetype not in ALLOWED_TYPES:
        return jsonify({"error": "Please upload a PNG, JPG or WEBP image."}), 400

    image_bytes = image.read()

    # Placeholder for now. In Steps 3 and 4 this will fetch the repo's
    # rules and call Gemma 4.
    return jsonify({
        "message": "received",
        "filename": image.filename,
        "size_kb": round(len(image_bytes) / 1024, 1),
        "repo_url": repo_url,
    })


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "That image is too large. Please keep it under 8 MB."}), 413


if __name__ == "__main__":
    app.run(debug=True)