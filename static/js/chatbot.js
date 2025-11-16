const chatBox = document.getElementById("chatBox");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");

function addMsg(text, sender="bot") {
    const div = document.createElement("div");
    div.className = `msg ${sender}`;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    let text = chatInput.value.trim();
    if (!text) return;

    addMsg(text, "user");
    chatInput.value = "";

    const res = await fetch("/chatbot/api", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ message:text })
    });

    const data = await res.json();
    addMsg(data.reply, "bot");
}

sendBtn.onclick = sendMessage;
chatInput.onkeypress = (e)=>{ if(e.key==="Enter") sendMessage(); };

// ===== Speech Recognition =====
let recognition = null;
if ("webkitSpeechRecognition" in window) {
    recognition = new webkitSpeechRecognition();
    recognition.lang = "vi-VN";
    recognition.continuous = false;

    recognition.onstart = () => micBtn.classList.add("recording");
    recognition.onend = () => micBtn.classList.remove("recording");

    recognition.onresult = (event)=>{
        const text = event.results[0][0].transcript;
        chatInput.value = text;
        sendMessage();
    }
}

micBtn.onclick = () => {
    if (!recognition) return alert("Trình duyệt không hỗ trợ microphone.");
    recognition.start();
};
