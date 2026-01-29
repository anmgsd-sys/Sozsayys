// Элементтерді алу
const recordBtn = document.getElementById('record-btn');
const statusText = document.getElementById('status');
const chatBox = document.getElementById('chat-box');
const topicInput = document.getElementById('topic-input');
const setupSection = document.getElementById('setupSection');
const gameSection = document.getElementById('gameSection');
const turnDisplay = document.getElementById('turn-display');
const manualInput = document.getElementById('manual-input');

let currentTopic = "";
let userSide = "gov"; 
let turnIndex = 0; 
let isRecording = false; 
let chatHistory = "";
let debateEnded = false; 

const roles = [
    "🏛 Үкімет 1 (Лидер)", "🛑 Оппозиция 1 (Лидер)", 
    "🏛 Үкімет 2 (Спикер)", "🛑 Оппозиция 2 (Спикер)", 
    "🏛 Үкімет 3 (Қорытынды)", "🛑 Оппозиция 3 (Қорытынды)"
];

// Модальді терезелер
function openModal(id) { document.getElementById('modal-' + id).style.display = 'block'; }
function closeModals() { document.querySelectorAll('.modal').forEach(m => m.style.display = 'none'); }
window.onclick = function(event) { if (event.target.classList.contains('modal')) closeModals(); }

// Тақырып алу
async function getRandomTopic() {
    topicInput.value = "Жүктелуде...";
    try {
        const response = await fetch('/get_topic');
        const data = await response.json();
        topicInput.value = data.topic;
    } catch { topicInput.value = "Бұл палата жасанды интеллектті мектепте қолдануды қолдайды"; }
}

// Жақты таңдау
function chooseSide(side) {
    userSide = side;
    currentTopic = topicInput.value;
    setupSection.style.display = "none";
    gameSection.style.display = "flex";
    
    addMessage("📢 Резолюция: " + currentTopic, "ai-message");
    
    if (userSide === 'opp') {
        turnIndex = -1; 
        sendToAI("Дебатты бастаңыз"); 
    } else {
        turnIndex = 0; 
        checkTurn();
    }
}

// Кезекті тексеру
function checkTurn() {
    if (debateEnded) return;

    if (turnIndex >= 5) {
        turnDisplay.textContent = "🏁 Барлық спикерлер сөйлеп болды";
        statusText.textContent = "Төреші қорытындысын тыңдау үшін 'Жіберу' батырмасын басыңыз.";
        manualInput.value = "Төреші мырза, дебатты қорытындылаңыз.";
        recordBtn.style.display = "none";
        return;
    }

    turnDisplay.textContent = "Кезекте: " + roles[turnIndex];
    statusText.textContent = "Кезек сізде! Сөзіңізді айтыңыз.";
    recordBtn.disabled = false;
    recordBtn.style.opacity = "1";
}

// Мәтінді қолмен жіберу
function sendManualText() {
    if (debateEnded) return;
    const text = manualInput.value;
    if (text.trim() === "") return;
    
    if (isRecording) {
        stopRecordingAction();
    }

    addMessage(`👤 Сіз: ${text}`, 'user-message');
    manualInput.value = "";
    sendToAI(text);
}

// ЖИ-ге сұраныс жіберу
async function sendToAI(text) {
    if (debateEnded) return;

    statusText.textContent = "🤖 ЖИ жауап дайындап жатыр...";
    recordBtn.disabled = true;

    try {
        const response = await fetch('/process_text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: text, 
                topic: currentTopic, 
                turn_index: turnIndex,
                history: chatHistory
            })
        });

        const data = await response.json();
        
        if (data.ai_text) {
            const roleName = data.role || "ЖИ";
            addMessage(`🤖 ${roleName}: ${data.ai_text}`, 'ai-message');
            chatHistory += `\n${roleName}: ${data.ai_text}`;

            if (data.audio_url) {
                const audio = new Audio(data.audio_url);
                audio.onended = () => {
                    if (data.is_final) {
                        finishDebate();
                    } else {
                        turnIndex += 2; 
                        checkTurn();
                    }
                };
                audio.play();
            } else {
                if (data.is_final) {
                    finishDebate();
                } else {
                    turnIndex += 2;
                    checkTurn();
                }
            }
        }
    } catch (error) {
        console.error(error);
        statusText.textContent = "⚠️ Байланыс үзілді.";
        recordBtn.disabled = false;
    }
}

// Дебатты аяқтау (Хаттамасыз нұсқа)
function finishDebate() {
    debateEnded = true;
    turnDisplay.textContent = "🏆 Дебат қорытындыланды";
    statusText.textContent = "Ойын аяқталды.";
}

function addMessage(text, className) {
    const div = document.createElement('div');
    div.classList.add('message', className);
    div.innerText = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// --- МИКРОФОН ЛОГИКАСЫ ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.lang = 'kk-KZ';
    recognition.continuous = true;
    recognition.interimResults = true;

    recordBtn.addEventListener('click', () => {
        if (debateEnded) return;
        if (!isRecording) {
            startRecordingAction();
        } else {
            stopRecordingAction();
        }
    });

    function startRecordingAction() {
        manualInput.value = "";
        try {
            recognition.start();
            isRecording = true;
            recordBtn.innerText = "🛑 Тоқтату";
            recordBtn.style.background = "#d32f2f";
            statusText.textContent = "Тыңдап тұрмын... Сөйлеңіз.";
        } catch (e) { console.error(e); }
    }

    function stopRecordingAction() {
        recognition.stop();
        isRecording = false;
        recordBtn.innerText = "🎤 Сөзді бастау";
        recordBtn.style.background = "#00796b";
        statusText.textContent = "Дауыс жазылды. 'Жіберу' батырмасын басыңыз.";
    }

    recognition.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript + " ";
            }
        }
        if (finalTranscript !== "") {
            manualInput.value += finalTranscript;
        }
    };

    recognition.onend = () => { if (isRecording) stopRecordingAction(); };
}
