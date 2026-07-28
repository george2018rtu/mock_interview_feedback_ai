const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const statusText = document.getElementById("status");
const questionSelect = document.getElementById("question");
const resultsSection = document.getElementById("results");
const loadingSection = document.getElementById("loading");
const timerText = document.getElementById("timer");
const recordingIndicator = document.getElementById("recordingIndicator");
let mediaRecorder;
let audioChunks = [];
let recordingStartTime;
let timerInterval;

startButton.addEventListener("click", async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({audio: true});
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.addEventListener("dataavailable", event => {
            if (event.data.size > 0) audioChunks.push(event.data);
        });
        mediaRecorder.addEventListener("stop", async () => {
            const durationSeconds = (Date.now() - recordingStartTime) / 1000;
            const audioBlob = new Blob(audioChunks, {type: mediaRecorder.mimeType});
            stream.getTracks().forEach(track => track.stop());
            await submitRecording(audioBlob, durationSeconds);
        });
        recordingStartTime = Date.now();
        mediaRecorder.start();
        startTimer();
        resultsSection.hidden = true;
        loadingSection.hidden = true;
        statusText.textContent = "Recording...";
        recordingIndicator.classList.add("active");
        startButton.disabled = true;
        stopButton.disabled = false;
        questionSelect.disabled = true;
    } catch (error) {
        statusText.textContent = "Microphone access failed. Check browser permissions.";
    }
});

stopButton.addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        clearInterval(timerInterval);
        recordingIndicator.classList.remove("active");
        statusText.textContent = "Analyzing your answer...";
        loadingSection.hidden = false;
        startButton.disabled = true;
        stopButton.disabled = true;
    }
});

function startTimer() {
    timerText.textContent = "00:00";
    timerInterval = setInterval(() => {
        const seconds = Math.floor((Date.now() - recordingStartTime) / 1000);
        const minutesText = String(Math.floor(seconds / 60)).padStart(2, "0");
        const secondsText = String(seconds % 60).padStart(2, "0");
        timerText.textContent = `${minutesText}:${secondsText}`;
    }, 250);
}

async function submitRecording(audioBlob, durationSeconds) {
    const formData = new FormData();
    formData.append("audio", audioBlob, `answer.${getAudioExtension(audioBlob.type)}`);
    formData.append("question_id", questionSelect.value);
    formData.append("duration", durationSeconds.toString());
    try {
        const response = await fetch("/analyze", {method: "POST", body: formData});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Analysis failed.");
        displayResults(data);
    } catch (error) {
        statusText.textContent = error.message;
    } finally {
        loadingSection.hidden = true;
        startButton.disabled = false;
        stopButton.disabled = true;
        questionSelect.disabled = false;
    }
}

function getAudioExtension(type) {
    if (type.includes("ogg")) return "ogg";
    if (type.includes("mp4")) return "mp4";
    return "webm";
}

function setList(id, items, emptyMessage) {
    const list = document.getElementById(id);
    list.innerHTML = "";
    (items.length ? items : [emptyMessage]).forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        list.appendChild(li);
    });
}

function displayResults(data) {
    const scores = data.evaluation.scores;
    document.getElementById("transcript").textContent = data.transcript;
    document.getElementById("overallScore").textContent = `${data.overall_score}/100`;
    document.getElementById("relevanceScore").textContent = `${scores.relevance}/100`;
    document.getElementById("structureScore").textContent = `${scores.structure}/100`;
    document.getElementById("specificityScore").textContent = `${scores.specificity}/100`;
    document.getElementById("communicationScore").textContent = `${scores.communication}/100`;
    document.getElementById("speakingSpeed").textContent = `${data.speech.words_per_minute} WPM`;
    document.getElementById("fillerCount").textContent = data.speech.filler_count;
    setList("strengths", data.evaluation.strengths, "No specific strengths were detected.");
    setList("improvements", data.evaluation.improvements, "No major improvements were identified.");
    setList("missingConcepts", data.evaluation.missing_concepts, "No important concepts were missing.");
    document.getElementById("improvedAnswer").textContent = data.evaluation.improved_answer;
    document.getElementById("followUpQuestion").textContent = data.evaluation.follow_up_question;
    resultsSection.hidden = false;
    statusText.textContent = "Analysis complete.";
    resultsSection.scrollIntoView({behavior: "smooth"});
}
