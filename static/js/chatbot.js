const chatBox = document.getElementById("chatBox");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const micIcon = document.getElementById("micIcon");
const indicator = document.getElementById("recordingIndicator");

let isRecording = false;
let recognition = null;

/* ------------------------
   SEND TEXT
------------------------ */
function sendMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    addMessage(msg, "user");
    chatInput.value = "";

    fetch("/chatbot/api", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: msg})
    })
    .then(res => res.json())
    .then(data => addMessage(data.reply, "bot"));
}

function addMessage(text, sender) {
    const div = document.createElement("div");
    div.className = "chat-msg " + sender;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

/* ------------------------
   SPEECH TO TEXT
------------------------ */
if ("webkitSpeechRecognition" in window) {
    console.log("SpeechRecognition supported!");

    recognition = new webkitSpeechRecognition();
    recognition.lang = "vi-VN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
        console.log("Recording started");
        isRecording = true;
        micBtn.classList.add("listening");
        indicator.style.display = "block";
    };

    recognition.onerror = (e) => {
        console.error("SpeechRecognition error:", e);
        alert("Không bật được microphone: " + e.error);
    };

    recognition.onend = () => {
        console.log("Recording stopped");
        isRecording = false;
        micBtn.classList.remove("listening");
        indicator.style.display = "none";
    };

    recognition.onresult = (event) => {
        let text = event.results[0][0].transcript;
        console.log("Recognized:", text);
        chatInput.value = text;
        sendMessage();
    };
} else {
    console.warn("Browser does NOT support webkitSpeechRecognition");
    alert("Trình duyệt này không hỗ trợ Voice Recognition!");
}

micBtn.onclick = () => {
    if (!recognition) return alert("Trình duyệt không hỗ trợ Speech Recognition!");

    if (!isRecording) {
        console.log("Starting recognition...");
        recognition.start();
    } else {
        console.log("Stopping recognition...");
        recognition.stop();
    }
};
sendBtn.onclick = sendMessage;
chatInput.onkeypress = (e) => {
    if (e.key === "Enter") sendMessage();
};