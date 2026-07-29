import re


FILLERS = {
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


def get_words(text):
    return re.findall(
        r"\b[a-zA-Z']+\b",
        text.lower()
    )


def get_fillers(text):
    found = {}

    for name, pattern in FILLERS.items():
        count = len(
            re.findall(
                pattern,
                text,
                flags=re.IGNORECASE
            )
        )

        if count > 0:
            found[name] = count

    return found


def analyze_speech(transcript, seconds):
    words = get_words(transcript)

    word_count = len(words)

    safe_seconds = max(seconds, 1)

    wpm = round(
        word_count / (safe_seconds / 60)
    )

    filler_info = get_fillers(transcript)

    filler_count = sum(
        filler_info.values()
    )

    return {
        "duration_seconds": round(seconds, 1),
        "word_count": word_count,
        "words_per_minute": wpm,
        "filler_count": filler_count,
        "filler_details": filler_info,
        "pace_score": pace_score(wpm),
        "filler_score": filler_score(
            filler_count,
            word_count
        ),
        "length_score": length_score(
            word_count,
            seconds
        )
    }


def pace_score(wpm):
    if 120 <= wpm <= 170:
        return 100

    if 100 <= wpm < 120:
        return 85

    if 170 < wpm <= 190:
        return 85

    if 80 <= wpm < 100:
        return 65

    if 190 < wpm <= 220:
        return 65

    return 40


def filler_score(filler_count, word_count):
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


def length_score(word_count, seconds):
    if word_count == 0:
        return 0

    if 45 <= seconds <= 120:
        return 100

    if 30 <= seconds < 45:
        return 80

    if 120 < seconds <= 150:
        return 80

    return 55