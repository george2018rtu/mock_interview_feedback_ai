import re

FILLER_PHRASES = {
    "um": r"\bum\b",
    "uh": r"\buh\b",
    "er": r"\ber\b",
    "you know": r"\byou know\b",
    "I mean": r"\bi mean\b",
    "kind of": r"\bkind of\b",
    "sort of": r"\bsort of\b",
    "basically": r"\bbasically\b",
    "literally": r"\bliterally\b",
    "actually": r"\bactually\b"
}

def tokenize(text):
    return re.findall(r"\b[a-zA-Z']+\b", text.lower())

def count_fillers(transcript):
    details = {}
    for name, pattern in FILLER_PHRASES.items():
        count = len(re.findall(pattern, transcript, flags=re.IGNORECASE))
        if count:
            details[name] = count
    return details

def analyze_speech(transcript, duration_seconds):
    words = tokenize(transcript)
    word_count = len(words)
    words_per_minute = round(word_count / (max(duration_seconds, 1) / 60))
    filler_details = count_fillers(transcript)
    filler_count = sum(filler_details.values())
    return {
        "duration_seconds": round(duration_seconds, 1),
        "word_count": word_count,
        "words_per_minute": words_per_minute,
        "filler_count": filler_count,
        "filler_details": filler_details,
        "pace_score": calculate_pace_score(words_per_minute),
        "filler_score": calculate_filler_score(filler_count, word_count),
        "length_score": calculate_length_score(word_count, duration_seconds)
    }

def calculate_pace_score(wpm):
    if 120 <= wpm <= 170:
        return 100
    if 100 <= wpm < 120 or 170 < wpm <= 190:
        return 85
    if 80 <= wpm < 100 or 190 < wpm <= 220:
        return 65
    return 40

def calculate_filler_score(filler_count, word_count):
    if word_count == 0:
        return 0
    ratio = filler_count / word_count * 100
    if ratio <= 1:
        return 100
    if ratio <= 3:
        return 85
    if ratio <= 5:
        return 65
    return 40

def calculate_length_score(word_count, duration_seconds):
    if word_count == 0:
        return 0
    if 45 <= duration_seconds <= 120:
        return 100
    if 30 <= duration_seconds < 45 or 120 < duration_seconds <= 150:
        return 80
    return 55
