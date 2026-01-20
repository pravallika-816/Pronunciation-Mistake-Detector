import json, random
from engine import record_audio, speech_to_text, detect_pronunciation

with open("sentences.json", "r") as f:
    db = json.load(f)

level = "easy"
ref_sentence = random.choice(db[level])

print("\nSentence:")
print(ref_sentence)

record_audio()

recognized = speech_to_text("recordings/user.wav")
print("\nRecognized:", recognized)

results = detect_pronunciation(ref_sentence, recognized)

print("\n--- FEEDBACK ---")
for w, status in results.items():
    print(w, "→", status)
