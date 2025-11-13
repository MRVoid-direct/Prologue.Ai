from flask import Flask, render_template, request, jsonify, session
from assistant_core import SimpleVoiceAssistant
import threading
import time
import json

app = Flask(__name__)
app.secret_key = '7874228337'

# Глобальный экземпляр ассистента
assistant = SimpleVoiceAssistant()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Возвращает статус ассистента и нейросети"""
    status = {
        'neuro_available': assistant.neuro_available,
        'assistant_ready': True
    }
    return jsonify(status)


@app.route('/api/process_command', methods=['POST'])
def process_command():
    """Обрабатывает текстовую команду"""
    data = request.json
    command = data.get('command', '').lower()

    if not command:
        return jsonify({'error': 'Пустая команда'})

    try:
        # Обрабатываем команду
        response = assistant.process_text_command(command)

        return jsonify({
            'success': True,
            'response': response,
            'command': command
        })

    except Exception as e:
        return jsonify({
            'error': f'Ошибка обработки: {str(e)}'
        })


@app.route('/api/ask_neuro', methods=['POST'])
def ask_neuro():
    """Запрос к нейросети"""
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({'error': 'Пустой вопрос'})

    try:
        response = assistant.ask_neuro(question)

        return jsonify({
            'success': True,
            'question': question,
            'answer': response
        })

    except Exception as e:
        return jsonify({
            'error': f'Ошибка нейросети: {str(e)}'
        })


@app.route('/api/toggle_listening', methods=['POST'])
def toggle_listening():
    """Включение/выключение прослушивания"""
    data = request.json
    action = data.get('action', 'start')

    # Здесь можно добавить логику для реального голосового управления
    # Пока просто возвращаем статус

    return jsonify({
        'success': True,
        'listening': action == 'start',
        'message': 'Прослушивание ' + ('активировано' if action == 'start' else 'деактивировано')
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)