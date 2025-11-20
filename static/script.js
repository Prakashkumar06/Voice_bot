let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let responseAudio = null;

const recordButton = document.getElementById("recordButton");
const wave = document.getElementById("wave");
const chatBox = document.getElementById("chat-box");


function showWave(active) {
  wave.classList.toggle("active", active);
}


function addMessage(text, sender) {
  const msgDiv = document.createElement("div");
  msgDiv.className = sender === "user" ? "user-msg" : "bot-msg";
  msgDiv.textContent = text;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}


recordButton.addEventListener("click", async () => {
  if (responseAudio && !responseAudio.paused) {
    responseAudio.pause();
    responseAudio = null;
  }

  if (!isRecording) {
    isRecording = true;
    recordButton.textContent = " Listening...";
    showWave(true);
    audioChunks = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        sendAudioToServer(audioBlob);
      };

      mediaRecorder.start();
      console.log("🎧 Recording started...");
    } catch (error) {
      alert("Microphone access denied or not available.");
      console.error("Mic error:", error);
      resetUI();
    }
  } else {
    isRecording = false;
    recordButton.textContent = "Ask your question";
    showWave(false);
    mediaRecorder.stop();
    console.log(" Recording stopped.");
  }
});


async function sendAudioToServer(audioBlob) {
  addMessage(" Processing your question...", "bot");

  const formData = new FormData();
  formData.append("audio_data", audioBlob, "recording.webm");

  try {
    const response = await fetch("/process_audio", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    console.log(" Server response:", data);

    if (data.error) {
      addMessage(" " + data.error, "bot");
      return resetUI();
    }

    addMessage("You said: " + data.transcript, "user");
    addMessage(" " + data.response, "bot");

    if (data.audio_base64) {
      const audioUrl = "data:audio/wav;base64," + data.audio_base64;
      responseAudio = new Audio(audioUrl);
      responseAudio.playbackRate = 1;
      responseAudio.play();
    }

  } catch (error) {
    console.error("Upload error:", error);
    addMessage("Something went wrong.", "bot");
  } finally {
    resetUI();
  }
}


function resetUI() {
  isRecording = false;
  showWave(false);
  recordButton.textContent = "Ask your question";
}
