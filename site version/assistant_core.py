import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import requests
import threading
import time


class SimpleVoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.setup_voice()

        self.conversation_history = []
        self.lm_studio_url = "http://localhost:1234/v1/chat/completions"
        self.neuro_available = self.check_neuro_availability()

    def check_neuro_availability(self):
        """Проверка доступности LM Studio с коротким таймаутом"""
        try:
            # Быстрая проверка с коротким таймаутом
            test_payload = {
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5,
                "temperature": 0.1
            }
            response = requests.post(self.lm_studio_url, json=test_payload, timeout=10)
            return response.status_code == 200
        except:
            print("❌ LM Studio недоступен!")
            return False

    def setup_voice(self):
        voices = self.tts_engine.getProperty('voices')
        self.tts_engine.setProperty('voice', voices[0].id)
        self.tts_engine.setProperty('rate', 150)

    def speak(self, text):
        print(f"Пролог: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self):
        with sr.Microphone() as source:
            print("Слушаю...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)

        try:
            command = self.recognizer.recognize_google(audio, language="ru-RU")
            print(f"Вы сказали: {command}")
            return command.lower()
        except sr.UnknownValueError:
            return "не понял"
        except sr.RequestError:
            return "ошибка связи"

    def ask_neuro(self, question):
        """Улучшенный запрос к нейросети с обработкой таймаутов"""
        if not self.neuro_available:
            return "Нейросеть недоступна. Запустите LM Studio и загрузите модель."

        try:
            # Упрощаем системный промпт для ускорения
            messages = [
                {
                    "role": "system",
                    "content": "Кратко ответь:"
                },
                {"role": "user", "content": question}
            ]

            # Ограничиваем историю для ускорения
            if self.conversation_history:
                messages = self.conversation_history[-2:] + messages  # Только последние 2 обмена

            payload = {
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 10000,  # Уменьшаем длину ответа
                "stream": False
            }

            print("🔄 Отправляю запрос к нейросети...")

            # УВЕЛИЧИВАЕМ таймаут до 60 секунд и добавляем повторы
            for attempt in range(2):  # 2 попытки
                try:
                    response = requests.post(self.lm_studio_url, json=payload, timeout=60)  # 60 секунд

                    if response.status_code == 200:
                        result = response.json()
                        answer = result['choices'][0]['message']['content'].strip()

                        # Сохраняем в историю
                        self.conversation_history.extend([
                            {"role": "user", "content": question},
                            {"role": "assistant", "content": answer}
                        ])

                        # Ограничиваем размер истории
                        if len(self.conversation_history) > 6:
                            self.conversation_history = self.conversation_history[-6:]

                        return answer
                    else:
                        return f"Ошибка нейросети: код {response.status_code}"

                except requests.exceptions.Timeout:
                    if attempt == 0:  # Первая попытка таймаута
                        print("⏰ Таймаут, пробую еще раз...")
                        continue
                    else:
                        return "Нейросеть долго не отвечает. Попробуйте упростить вопрос."

        except Exception as e:
            return f"Ошибка: {str(e)}"

    def speak_neuro_response(self, question):
        """Озвучивание ответа нейросети с индикацией"""
        if not self.neuro_available:
            self.speak("Нейросеть недоступна. Запустите LM Studio.")
            return

        self.speak("Думаю над ответом, это может занять минуту...")
        neuro_response = self.ask_neuro(question)
        self.speak(neuro_response)

    def process_command(self, command):
        if "привет" in command:
            self.tts_engine.say("Привет! Чем могу помочь?")

        elif "время" in command:
            current_time = datetime.datetime.now().strftime("%H:%M")
            self.tts_engine.say(f"Сейчас {current_time}")

        elif "открой браузер" in command:
            webbrowser.open("https://google.com")
            self.speak("Открываю браузер")

        # Команды для нейросети
        elif "нейросеть" in command or "задай вопрос" in command:
            if not self.neuro_available:
                self.speak("Нейросеть сейчас недоступна. Запустите LM Studio.")
            else:
                self.speak("Что вы хотите спросить у нейросети?")
                question = self.listen()

                if question not in ["не понял", "ошибка связи"]:
                    thread = threading.Thread(target=self.speak_neuro_response, args=(question,))
                    thread.daemon = True
                    thread.start()
                else:
                    self.speak("Не удалось распознать вопрос")

        elif "спроси" in command and len(command) > 10:
            if not self.neuro_available:
                self.speak("Нейросеть сейчас недоступна.")
            else:
                question = command.replace("спроси", "").strip()
                thread = threading.Thread(target=self.speak_neuro_response, args=(question,))
                thread.daemon = True
                thread.start()

        elif "проверь нейросеть" in command:
            self.speak("Проверяю подключение к нейросети...")
            self.neuro_available = self.check_neuro_availability()
            if self.neuro_available:
                self.speak("Нейросеть подключена и готова к работе!")
            else:
                self.speak("Нейросеть недоступна. Запустите LM Studio.")

        elif "упрости запрос" in command:
            # Упрощаем настройки для ускорения
            self.speak("Упрощаю настройки для более быстрых ответов")

        elif "пока" in command:
            self.speak("До свидания!")
            return False

        else:
            self.speak("1")

        return True

    def run(self):
        self.speak("Пролог запущен")
        if not self.neuro_available:
            self.speak("Внимание: нейросеть недоступна. Скажите 'проверь нейросеть' после запуска LM Studio.")

        while True:
            command = self.listen()
            if not self.process_command(command):
                break


# Запуск ассистента
if __name__ == "__main__":
    assistant = SimpleVoiceAssistant()
    assistant.run()