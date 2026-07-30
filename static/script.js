/*get all important html elements*/ 
const startBtn = document.getElementById("startButton");
const stopBtn = document.getElementById("stopButton");
const status = document.getElementById("status");
const questionBox = document.getElementById("question");
const results = document.getElementById("results");
const loading = document.getElementById("loading");
const timer = document.getElementById("timer");
const recordIcon = document.getElementById("recordingIndicator");
const sectorBox = document.getElementById("sector");
const useFollowUpButton = document.getElementById("useFollowUpButton");
/*for example, in the future I can later do status.textContent is recording....*/ 

let recorder;
let chunks = [];
let startTime;
let timerId;

/*on start button click run function*/
startBtn.addEventListener("click", async () =>
{
    try
    {
        /*get microphone access permission through browser; if approved, stream contains the live audio recording/microphone audio*/
        const stream = await navigator.mediaDevices.getUserMedia(
            {
                audio: true
            }
        );
        /*reset chunks if the person has already used microphone recording already*/
        chunks = [];

        /*creating the recorder; the mediarecorder browser API records the microphone stream.*/
        recorder = new MediaRecorder(stream);

        /*if data (from the browser producing audio data) is available in the recorder/someone recorded, */
        recorder.addEventListener("dataavailable", (event) =>
        {
            /*add to array if there is actually data from the browser producing audio data*/
            if (event.data.size > 0)
            {
                chunks.push(event.data);
            }
        });

        /*if the recording has been stopped*/
        recorder.addEventListener("stop", async () =>
        {
            /*because data.now() return milliseconds, we divide by 1000 to get seconds*/
            const seconds = (Date.now() - startTime) / 1000;

            /*combines all chunks into one audio recording which will be called audio*/
            const audio = new Blob(
                chunks,
                {
                    type: recorder.mimeType
                }
            );

            /*stops all microphone tracks*/
            stream.getTracks().forEach((track) =>
            {
                track.stop();
            });

            /*sending to flask; calls the function that sends the audio to /analyze.*/
            await sendRecording(audio, seconds);
        });

        startTime = Date.now();
        recorder.start();
        runTimer();
        results.hidden = true;
        loading.hidden = true;

        /*because it's recording right now, we make status recording....*/
        status.textContent = "Recording...";

        /*activates recording animation*/
        recordIcon.classList.add("active");

        /*while the audio is recording, make it so that start button is disabled (can't start again), stop button is not disabled, and make sure the user can't change question halfway*/
        startBtn.disabled = true;
        stopBtn.disabled = false;
        questionBox.disabled = true;
    }
    /*if error, make the status text content to say that the microphone access has failed*/
    catch (error)
    {
        status.textContent = "Microphone access failed. Check browser permissions.";
    }
});

/*runs whenever the user chooses a new sector.*/
sectorBox.addEventListener("change", async () => {
    /*get sector value*/
    const sector = sectorBox.value;

    /*nothing on the questionBox because I set innerHtml if there is no sector to be select a sector first*/
    questionBox.innerHTML = "";

    /*if no sector was chosen, make it so that they can't choose a question and make the innerHtml of the question box say select a sector first*/
    if (!sector) {
        questionBox.disabled = true;

        questionBox.innerHTML = `
            <option value="">
                Select a sector first
            </option>
        `;
        return;
    }
    questionBox.disabled = true;
    questionBox.innerHTML = `
        <option value="">
            Loading questions...
        </option>
    `;

    try {
        /*sends a get request to flask; encodeuricomponent safely formats spaces and special characters.*/
        const response = await fetch(
            `/questions?sector=${encodeURIComponent(sector)}`
        );
        /*converts the server’s json into a js array.*/
        const questions = await response.json();
        questionBox.innerHTML = "";
        /*addditional checking*/
        if (questions.length === 0) {
            questionBox.innerHTML = `
                <option value="">
                    No questions found
                </option>
            `;
            return;
        }
        questionBox.innerHTML = `
            <option value="">
                Select a question
            </option>
        `;

        /*loops through every returned question*/
        questions.forEach(question => {
            /*create a new option for every return question*/
            const option = document.createElement("option");

            /*the hidden submitted value when creating a new option is the question id*/
            option.value = question.id;
            /*make the option include the difficult and the question of course*/
            option.textContent =`${question.question} (${question.difficulty})`;

            /*add it to questionbox for the dropdown*/
            questionBox.appendChild(option);
        });
        /*make it so that when all the questions have bene added, it becomes available to chosoe the questions*/
        questionBox.disabled = false;

    } 
    /*if there is an error*/
    catch (error) {
        console.error(error);

        questionBox.innerHTML = `
            <option value="">
                Could not load questions
            </option>
        `;
    }
});

/*for when the user clicks stop button*/
stopBtn.addEventListener("click", () =>
{
    /*check to see if the recorder is cuurrently recording*/
    if (recorder && recorder.state === "recording")
    {
        /*stop recording if it was recording*/
        recorder.stop();

        /*stops the visual timer*/
        clearInterval(timerId);

        /*turns off the recording animation*/
        recordIcon.classList.remove("active");

        /* say analyzing your answer*/
        status.textContent = "Analyzing your answer...";
        /*shows loading status*/
        loading.hidden = false;

        /* same stop button start button theory*/
        startBtn.disabled = true;
        stopBtn.disabled = true;
    }
});

/*this is just a timer function that updates timer.textContent every second*/
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

/*recieves the full audio and the duration*/
async function sendRecording(audio, seconds)
{
    /*creates a form that can contain both files and text to send to flask.*/
    const form = new FormData();

    /*get extension using the function*/
    const ext = getExtension(audio.type);

    /*adds the audio file*/
    form.append("audio", audio, `answer.${ext}`);
    /*adds question id*/
    form.append("question_id", questionBox.value);
    /*adds whatever follow up question the AI from groq returns as well/whatever is displayed*/
    form.append("custom_question_text",document.getElementById("followUpQuestion").textContent);

    /*adds duration*/
    form.append("duration", seconds.toString());

    /*adds sector*/
    form.append("sector", sectorBox.value);

    /*sends the complete form to Flask.*/
    try
    {
        const res = await fetch(
            "/analyze",
            {
                method: "POST",
                body: form
            }
        );
        /*read flasks json response*/
        const data = await res.json();

        /*res.ok is only true for successful codes like 200, so if it isn't 200, return an error*/
        if (!res.ok)
        {
            throw new Error(data.error || "Analysis failed.");
        }
         /*show successful results*/
        showResults(data);
    }
    /*catch any errors again*/
    catch (error)
    {
        status.textContent = error.message;
    }
    /*run no matter what*/
    finally
    {
        /*make the loading message be hidden*/
        loading.hidden = true;

        /*at this point flask has sent back the results so we just make it so that the person can start recording again and everything reverts to orignal state*/
        startBtn.disabled = false;
        stopBtn.disabled = true;
        questionBox.disabled = false;
    }
}

/*function just to get the extension pretty self explanatory use js key words to see what extension it is*/
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

/*filling the feedback list to give to the user*/
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

/*this function essentially uses the index.html file and fills in text content with the scores*/
function showResults(data)
{
    /*data is what we passed in originally which was the response flask gave from using the /analyze route*/
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

    /*fill the list wiht all the feedback to print out as feedback that the AI provided through data.evaluation*/
    fillList("strengths", evalData.strengths, "No specific strengths were detected.");
    fillList("improvements",  evalData.improvements, "No major improvements were identified.");
    fillList("missingConcepts", evalData.missing_concepts, "No important concepts were missing.");

    /*make the part that shows a better answer whatever the AI returned as a better answer*/
    document.getElementById("improvedAnswer").textContent = evalData.improved_answer;

    /*the AI also generates a follow up question so we display that as well*/
    document.getElementById("followUpQuestion").textContent =
        evalData.follow_up_question;

        /*make the follow up use as next question button not disabled whenever there is a follow up question (which is basically always but just as a good measure to have)*/
        useFollowUpButton.disabled = !evalData.follow_up_question;

    /*make the results available*/
    results.hidden = false;

    /*make status equal to analysis complete*/
    status.textContent = "Analysis complete.";

    /*automatically scoll into the results section with behavior smooth*/
    results.scrollIntoView(
        {
            behavior: "smooth"
        }
    );
}


useFollowUpButton.addEventListener("click", () => {
    /*get the follow up question*/
    const followUp = document.getElementById("followUpQuestion").textContent.trim();

    if (!followUp) {
        return;
    }

    /*avoid creating duplicates*/
    for (const option of questionBox.options) {
        if (option.textContent === followUp) {
            questionBox.value = option.value;
            return;
        }
    }
    /*create new option as the follow up question that the user can choose for the drop down that has the same behavior as a regular question*/
    const option = document.createElement("option");

    option.value = "followup";
    option.textContent = followUp;

    /*insert at the highest value*/
    questionBox.insertBefore(option, questionBox.children[1]);

    /*when the next reocrding is sent, flask sees this and sets question as custom_question_text for the AI evaluation, which will do the same thing except the question this time
    is the follow up question*/
    questionBox.value = "followup";
});