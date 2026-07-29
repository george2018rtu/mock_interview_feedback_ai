const startBtn = document.getElementById("startButton");
const stopBtn = document.getElementById("stopButton");
const status = document.getElementById("status");
const questionBox = document.getElementById("question");
const results = document.getElementById("results");
const loading = document.getElementById("loading");
const timer = document.getElementById("timer");
const recordIcon = document.getElementById("recordingIndicator");

let recorder;
let chunks = [];
let startTime;
let timerId;

startBtn.addEventListener("click", async () =>
{
    try
    {
        const stream = await navigator.mediaDevices.getUserMedia(
            {
                audio: true
            }
        );

        chunks = [];
        recorder = new MediaRecorder(stream);

        recorder.addEventListener("dataavailable", (event) =>
        {
            if (event.data.size > 0)
            {
                chunks.push(event.data);
            }
        });

        recorder.addEventListener("stop", async () =>
        {
            const seconds = (Date.now() - startTime) / 1000;

            const audio = new Blob(
                chunks,
                {
                    type: recorder.mimeType
                }
            );

            stream.getTracks().forEach((track) =>
            {
                track.stop();
            });

            await sendRecording(audio, seconds);
        });

        startTime = Date.now();

        recorder.start();
        runTimer();

        results.hidden = true;
        loading.hidden = true;

        status.textContent = "Recording...";
        recordIcon.classList.add("active");

        startBtn.disabled = true;
        stopBtn.disabled = false;
        questionBox.disabled = true;
    }
    catch (error)
    {
        status.textContent =
            "Microphone access failed. Check browser permissions.";
    }
});

stopBtn.addEventListener("click", () =>
{
    if (recorder && recorder.state === "recording")
    {
        recorder.stop();

        clearInterval(timerId);

        recordIcon.classList.remove("active");

        status.textContent = "Analyzing your answer...";
        loading.hidden = false;

        startBtn.disabled = true;
        stopBtn.disabled = true;
    }
});

function runTimer()
{
    timer.textContent = "00:00";

    timerId = setInterval(() =>
    {
        const totalSeconds =
            Math.floor((Date.now() - startTime) / 1000);

        const mins =
            String(Math.floor(totalSeconds / 60)).padStart(2, "0");

        const secs =
            String(totalSeconds % 60).padStart(2, "0");

        timer.textContent = `${mins}:${secs}`;
    }, 250);
}

async function sendRecording(audio, seconds)
{
    const form = new FormData();

    const ext = getExtension(audio.type);

    form.append("audio", audio, `answer.${ext}`);
    form.append("question_id", questionBox.value);
    form.append("duration", seconds.toString());

    try
    {
        const res = await fetch(
            "/analyze",
            {
                method: "POST",
                body: form
            }
        );

        const data = await res.json();

        if (!res.ok)
        {
            throw new Error(data.error || "Analysis failed.");
        }

        showResults(data);
    }
    catch (error)
    {
        status.textContent = error.message;
    }
    finally
    {
        loading.hidden = true;

        startBtn.disabled = false;
        stopBtn.disabled = true;
        questionBox.disabled = false;
    }
}

function getExtension(type)
{
    if (type.includes("ogg"))
    {
        return "ogg";
    }

    if (type.includes("mp4"))
    {
        return "mp4";
    }

    return "webm";
}

function fillList(id, items, emptyText)
{
    const list = document.getElementById(id);

    list.innerHTML = "";

    const values = items.length ? items : [emptyText];

    values.forEach((item) =>
    {
        const li = document.createElement("li");

        li.textContent = item;

        list.appendChild(li);
    });
}

function showResults(data)
{
    const evalData = data.evaluation;
    const scores = evalData.scores;
    const speech = data.speech;

    document.getElementById("transcript").textContent =
        data.transcript;

    document.getElementById("overallScore").textContent =
        `${data.overall_score}/100`;

    document.getElementById("relevanceScore").textContent =
        `${scores.relevance}/100`;

    document.getElementById("structureScore").textContent =
        `${scores.structure}/100`;

    document.getElementById("specificityScore").textContent =
        `${scores.specificity}/100`;

    document.getElementById("communicationScore").textContent =
        `${scores.communication}/100`;

    document.getElementById("speakingSpeed").textContent =
        `${speech.words_per_minute} WPM`;

    document.getElementById("fillerCount").textContent =
        speech.filler_count;

    fillList(
        "strengths",
        evalData.strengths,
        "No specific strengths were detected."
    );

    fillList(
        "improvements",
        evalData.improvements,
        "No major improvements were identified."
    );

    fillList(
        "missingConcepts",
        evalData.missing_concepts,
        "No important concepts were missing."
    );

    document.getElementById("improvedAnswer").textContent =
        evalData.improved_answer;

    document.getElementById("followUpQuestion").textContent =
        evalData.follow_up_question;

    results.hidden = false;

    status.textContent = "Analysis complete.";

    results.scrollIntoView(
        {
            behavior: "smooth"
        }
    );
}