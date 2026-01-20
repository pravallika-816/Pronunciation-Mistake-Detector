import speech_recognition as sr
import nltk
from nltk.corpus import cmudict
from Levenshtein import distance

# --------------------------
# PHONEME DICTIONARY (CMU)
# --------------------------
cmu = cmudict.dict()

def normalize_word(w):
    return ''.join(ch for ch in w.lower() if ch.isalpha())


# --------------------------
# SPEECH TO TEXT (STABLE)
# --------------------------
def speech_to_text(wav_path):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            # attempt to clean ambient noise
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.record(source)

        text = r.recognize_google(audio)
        print("[ASR]:", text)
        return text.lower()

    except sr.UnknownValueError:
        print("[ASR]: could not understand audio")
        return ""

    except sr.RequestError as e:
        print("[ASR]: request to Google failed:", e)
        return ""


# --------------------------
# REFERENCE PHONEMES
# --------------------------
def sentence_to_phonemes(sentence):
    words = [normalize_word(w) for w in sentence.split()]
    phonemes = []

    for w in words:
        if w in cmu:
            # use first pronunciation variant
            phones = cmu[w][0]
            # remove stress digits: AH0 → AH
            phones = [p.rstrip('0123456789') for p in phones]
            phonemes.append((w, phones))
        else:
            phonemes.append((w, []))  # unknown → empty phoneme

    return phonemes


# --------------------------
# USER PHONEMES FROM ASR TEXT
# --------------------------
def user_speech_to_phonemes(asr_text):
    words = [normalize_word(w) for w in asr_text.split()]
    phonemes = []

    for w in words:
        if w in cmu:
            phones = cmu[w][0]
            phones = [p.rstrip('0123456789') for p in phones]
            phonemes.append((w, phones))
        else:
            phonemes.append((w, []))
    return phonemes


# --------------------------
# PHONEME PRONUNCIATION ALIGNMENT
# --------------------------
def detect_pronunciation(ref_ph, user_ph, asr_text, reference_sentence):
    """
    ref_ph = [(word, [phonemes])]
    user_ph = [(word, [phonemes])]
    return: {word -> status}
    """

    results = {}
    ref_words = [w for w, _ in ref_ph]
    user_words = [w for w, _ in user_ph]

    for i, (ref_w, ref_p) in enumerate(ref_ph):

        # --- CASE 1: user didn't speak enough words
        if i >= len(user_ph):
            results[ref_w] = "NOT SPOKEN"
            continue

        user_w, user_p = user_ph[i]

        # --- CASE 2: word mismatch → morphological / wrong form / substitution
        if user_w != ref_w:
            results[ref_w] = "MISPRONOUNCED"
            continue

        # --- CASE 3: phoneme comparison
        if not ref_p or not user_p:
            results[ref_w] = "MISPRONOUNCED"
            continue

        d = distance(' '.join(ref_p), ' '.join(user_p))

        if d == 0:
            results[ref_w] = "CORRECT"
        else:
            results[ref_w] = "MISPRONOUNCED"

    return results
