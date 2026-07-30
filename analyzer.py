import re

#hardcode a dictonary with common filler words to check the response the user recorded if it has any of them
FILLERS = {
    "um": r"\bum\b", #to make sure we don't think in things like umbrella or whatnot
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

#get all words in the text
def get_words(text):
    return re.findall( r"\b[a-zA-Z']+\b", text.lower())


#function to get all filler words and the associated amount
def get_fillers(text):
    #define a list for all filler words
    found = {}

    #iterate through all of the values in the hardcoded fillers with the text/transcript of the users ecording
    #and set all filler words spoken in transcript audio to how many times it was said.
    for name, pattern in FILLERS.items():
        count = len( re.findall(pattern, text, flags=re.IGNORECASE ) )
        if count > 0:
            found[name] = count

    #return the dictonary with the associated values
    return found

#check words per minutes, amount of fillers, the dictonary with all the fillers, and the scores for what has been seen in the transcript
def analyze_speech(transcript, seconds):
    #get the words in the transcript
    words = get_words(transcript)

    #get the length/how many words there are 
    word_count = len(words)

    #make sure that we don't divide by zero
    safe_seconds = max(seconds, 1)

    #get words per minute
    wpm = round(word_count / (safe_seconds / 60))

    #get the dictonary with all the fillers and how many times each appears
    filler_info = get_fillers(transcript)

    #get how many fillers has been said in total.
    filler_count = sum( filler_info.values())

    #return all the information to display in our webpage.
    return {
        "duration_seconds": round(seconds, 1),
        "word_count": word_count,
        "words_per_minute": wpm,
        "filler_count": filler_count,
        "filler_details": filler_info,
        "pace_score": pace_score(wpm),
        "filler_score": filler_score(filler_count, word_count),
        "length_score": length_score(word_count, seconds)
    }


#this is pace score and returns a score designated with how fast you were talking
#(don't want to be talking like the flash out here)
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

#essentially divide the filler amount by the amount of words and get the percent
def filler_score(filler_count, word_count):
    if word_count == 0:
        return 0
    ratio = filler_count / word_count * 100

    #associate score with hardcoded amount of fillers that is acceptable
    if ratio <= 1:
        return 100
    if ratio <= 3:
        return 85
    if ratio <= 5:
        return 65
    return 40


#make sure that the person didn't speak forever, and if they didn't speak at all, just return 0
#one flaw is that whenever we don't say anything into the recording, the AI automatically shows that we said "Thank You".
#however, I don't believe this is going to be a big problem
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