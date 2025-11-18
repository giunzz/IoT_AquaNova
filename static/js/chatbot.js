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

sendBtn.onclick = sendMessage;
chatInput.addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
});

/* ------------------------
   SPEECH TO TEXT
------------------------ */
if ("webkitSpeechRecognition" in window) {
    recognition = new webkitSpeechRecognition();
    recognition.lang = "vi-VN";
    recognition.continuous = false;

    recognition.onstart = () => {
        isRecording = true;
        micBtn.classList.add("listening");
        indicator.style.display = "block";
    };

    recognition.onend = () => {
        isRecording = false;
        micBtn.classList.remove("listening");
        indicator.style.display = "none";
    };

    recognition.onresult = (event) => {
        let text = event.results[0][0].transcript;
        chatInput.value = text;
        sendMessage();
    };
}

micBtn.onclick = () => {
    if (!recognition) return alert("Trình duyệt không hỗ trợ Speech Recognition!");

    if (!isRecording) recognition.start();
    else recognition.stop();
};
