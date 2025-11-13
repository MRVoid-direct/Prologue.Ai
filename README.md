<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Голосовой ассистент Пролог</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }

        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .status {
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }

        .status.connected {
            background: rgba(76, 175, 80, 0.3);
        }

        .status.disconnected {
            background: rgba(244, 67, 54, 0.3);
        }

        .controls {
            text-align: center;
            margin: 30px 0;
        }

        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 16px;
            cursor: pointer;
            margin: 10px;
            transition: all 0.3s;
        }

        button:hover {
            background: #45a049;
            transform: scale(1.05);
        }

        button:disabled {
            background: #cccccc;
            cursor: not-allowed;
        }

        .voice-btn {
            background: #ff4081;
            width: 80px;
            height: 80px;
            border-radius: 50%;
            font-size: 24px;
        }

        .voice-btn.listening {
            background: #f44336;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        .chat-container {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
            color: #333;
            max-height: 400px;
            overflow-y: auto;
        }

        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 10px;
        }

        .user-message {
            background: #e3f2fd;
            margin-left: 20%;
        }

        .assistant-message {
            background: #f5f5f5;
            margin-right: 20%;
        }

        .input-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        input {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Голосовой ассистент "Пролог"</h1>

        <div id="status" class="status disconnected">
            ❌ Нейросеть недоступна (требуется LM Studio)
        </div>

        <div class="controls">
            <button id="voiceBtn" class="voice-btn" disabled>
                🎤
            </button>
            <p id="statusText">Нажмите для голосового ввода</p>
        </div>

        <div class="input-group">
            <input type="text" id="textInput" placeholder="Введите команду текстом...">
            <button id="sendBtn" disabled>Отправить</button>
        </div>

        <div class="chat-container" id="chatContainer">
            <div class="message assistant-message">
                <strong>Пролог:</strong> Привет! Я голосовой ассистент. Нажмите на микрофон, чтобы начать общение.
            </div>
        </div>
    </div>

    <script>
        class WebVoiceAssistant {
            constructor() {
                this.recognition = null;
                this.isListening = false;
                this.lmStudioUrl = "http://localhost:1234/v1/chat/completions";
                this.neuroAvailable = false;
                this.conversationHistory = [];

                this.initSpeechRecognition();
                this.checkNeuroStatus();
                this.setupEventListeners();
            }

            initSpeechRecognition() {
                if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    this.recognition = new SpeechRecognition();
                    this.recognition.continuous = false;
                    this.recognition.interimResults = false;
                    this.recognition.lang = 'ru-RU';

                    this.recognition.onstart = () => {
                        this.isListening = true;
                        this.updateUI();
                    };

                    this.recognition.onresult = (event) => {
                        const command = event.results[0][0].transcript;
                        this.addMessage(command, 'user');
                        this.processCommand(command);
                    };

                    this.recognition.onerror = (event) => {
                        console.error('Ошибка распознавания:', event.error);
                        this.addMessage('Ошибка распознавания речи', 'assistant');
                    };

                    this.recognition.onend = () => {
                        this.isListening = false;
                        this.updateUI();
                    };

                    document.getElementById('voiceBtn').disabled = false;
                } else {
                    this.addMessage('Ваш браузер не поддерживает распознавание речи', 'assistant');
                }
            }

            async checkNeuroStatus() {
                try {
                    const testPayload = {
                        messages: [{"role": "user", "content": "test"}],
                        max_tokens: 5,
                        temperature: 0.1
                    };

                    const response = await fetch(this.lmStudioUrl, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(testPayload)
                    });

                    this.neuroAvailable = response.ok;
                    this.updateStatus();
                } catch (error) {
                    this.neuroAvailable = false;
                    this.updateStatus();
                }
            }

            updateStatus() {
                const statusElement = document.getElementById('status');
                if (this.neuroAvailable) {
                    statusElement.className = 'status connected';
                    statusElement.innerHTML = '✅ Нейросеть подключена';
                    document.getElementById('sendBtn').disabled = false;
                } else {
                    statusElement.className = 'status disconnected';
                    statusElement.innerHTML = '❌ Нейросьеь недоступна. Запустите LM Studio на localhost:1234';
                }
            }

            updateUI() {
                const voiceBtn = document.getElementById('voiceBtn');
                const statusText = document.getElementById('statusText');

                if (this.isListening) {
                    voiceBtn.classList.add('listening');
                    statusText.textContent = 'Слушаю...';
                } else {
                    voiceBtn.classList.remove('listening');
                    statusText.textContent = 'Нажмите для голосового ввода';
                }
            }

            startListening() {
                if (this.recognition && !this.isListening) {
                    this.recognition.start();
                }
            }

            addMessage(text, sender) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}-message`;
                messageDiv.innerHTML = `<strong>${sender === 'user' ? 'Вы' : 'Пролог'}:</strong> ${text}`;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            async processCommand(command) {
                // Простые команды
                if (command.includes('привет')) {
                    this.addMessage('Привет! Чем могу помочь?', 'assistant');
                    this.speak('Привет! Чем могу помочь?');
                }
                else if (command.includes('время')) {
                    const now = new Date();
                    const timeString = now.toLocaleTimeString('ru-RU');
                    this.addMessage(`Сейчас ${timeString}`, 'assistant');
                    this.speak(`Сейчас ${timeString}`);
                }
                else if (command.includes('открой браузер')) {
                    window.open('https://google.com', '_blank');
                    this.addMessage('Открываю браузер', 'assistant');
                    this.speak('Открываю браузер');
                }
                // Запросы к нейросети
                else if (command.includes('нейросеть') || command.includes('спроси') || command.includes('задай вопрос')) {
                    if (!this.neuroAvailable) {
                        this.addMessage('Нейросеть недоступна. Запустите LM Studio.', 'assistant');
                        this.speak('Нейросеть недоступна. Запустите LM Studio.');
                        return;
                    }

                    let question = command;
                    if (command.includes('спроси')) {
                        question = command.replace('спроси', '').trim();
                    }

                    this.addMessage(`Думаю над ответом на: "${question}"`, 'assistant');
                    this.speak('Думаю над ответом, это может занять минуту...');

                    try {
                        const response = await this.askNeuro(question);
                        this.addMessage(response, 'assistant');
                        this.speak(response);
                    } catch (error) {
                        this.addMessage('Ошибка при обращении к нейросети', 'assistant');
                        this.speak('Ошибка при обращении к нейросети');
                    }
                }
                else {
                    this.addMessage('Не понял команду. Попробуйте сказать "нейросеть" для вопросов к ИИ.', 'assistant');
                    this.speak('Не понял команду');
                }
            }

            async askNeuro(question) {
                const messages = [
                    {
                        "role": "system",
                        "content": "Ты полезный ассистент. Отвечай кратко и по делу."
                    },
                    {"role": "user", "content": question}
                ];

                if (this.conversationHistory.length > 0) {
                    messages.unshift(...this.conversationHistory.slice(-4));
                }

                const payload = {
                    messages: messages,
                    temperature: 0.7,
                    max_tokens: 500,
                    stream: false
                };

                const response = await fetch(this.lmStudioUrl, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                const answer = data.choices[0].message.content.trim();

                // Сохраняем в историю
                this.conversationHistory.push(
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer}
                );

                // Ограничиваем размер истории
                if (this.conversationHistory.length > 6) {
                    this.conversationHistory = this.conversationHistory.slice(-6);
                }

                return answer;
            }

            speak(text) {
                if ('speechSynthesis' in window) {
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = 'ru-RU';
                    utterance.rate = 1.0;
                    speechSynthesis.speak(utterance);
                }
            }

            setupEventListeners() {
                document.getElementById('voiceBtn').addEventListener('click', () => {
                    this.startListening();
                });

                document.getElementById('sendBtn').addEventListener('click', () => {
                    const input = document.getElementById('textInput');
                    const text = input.value.trim();
                    if (text) {
                        this.addMessage(text, 'user');
                        this.processCommand(text);
                        input.value = '';
                    }
                });

                document.getElementById('textInput').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        document.getElementById('sendBtn').click();
                    }
                });
            }
        }

        // Инициализация ассистента при загрузке страницы
        window.addEventListener('load', () => {
            window.assistant = new WebVoiceAssistant();
        });
    </script>
</body>
</html>
