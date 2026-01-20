from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json, random, os

from engine import (
    speech_to_text,
    sentence_to_phonemes,
    user_speech_to_phonemes,
    detect_pronunciation
)

# ------------------------
# CONFIGURE FLASK FRONTEND
# ------------------------

frontend_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)

app = Flask(
    __name__,
    static_folder=os.path.join(frontend_dir, "static"),
    template_folder=frontend_dir
)

CORS(app)

# Load sentences
with open("sentences.json", "r") as f:
    SENTENCE_DB = json.load(f)


# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.get("/get-sentences")
def get_sentences():
    level = request.args.get("level", "beginner").lower()
    count = int(request.args.get("count", 10))

    if level not in SENTENCE_DB:
        return jsonify({"error": "Invalid level"}), 400

    sentences = random.sample(SENTENCE_DB[level], count)

    return jsonify({
        "level": level,
        "sentences": sentences
    })


@app.post("/evaluate")
def evaluate():
    reference_sentence = request.form.get("sentence")
    audio_file = request.files.get("audio")

    if not reference_sentence or not audio_file:
        return jsonify({"error": "Missing sentence or audio"}), 400

    os.makedirs("recordings", exist_ok=True)
    wav_path = "recordings/user.wav"
    audio_file.save(wav_path)

    # Convert speech → text
    recognized = speech_to_text(wav_path)

    # If nothing recognized → mark as NOT SPOKEN
    if not recognized:
        ordered = []
        for word in reference_sentence.lower().split():
            ordered.append({"word": word, "status": "NOT SPOKEN"})
        return jsonify({"recognized": "", "results": ordered})

    # Phoneme extraction
    ref_ph = sentence_to_phonemes(reference_sentence)
    user_ph = user_speech_to_phonemes(recognized)

    results = detect_pronunciation(
        ref_ph, user_ph, recognized, reference_sentence
    )

    ordered = []
    for word in reference_sentence.lower().split():
        clean = ''.join(ch for ch in word if ch.isalpha())  # remove punctuation
        status = results.get(clean, "NOT SPOKEN")
        ordered.append({
            "word": word.rstrip(".,!?"),  # keep display nice
            "status": status
        })

    return jsonify({
        "recognized": recognized,
        "results": ordered
    })


@app.get("/ping")
def ping():
    return "Backend running"


if __name__ == "__main__":
    app.run(port=5000, debug=True)
