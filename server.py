from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import sqlite3
from flask import jsonify
from s2s import VoiceAssistant
from stt_groq import transcribe_audio
from llm import process_transcript_with_llm
from memory import Memory  # Import our new Memory module

app = Flask(__name__, template_folder='.')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize voice assistant
assistant = VoiceAssistant()
assistant_thread = None
current_response_thread = None
speech_event = threading.Event()

# Initialize memory system
memory = Memory()
current_session_id = memory.get_current_session_id()

def start_assistant():
    """Run the voice assistant in a separate thread"""
    assistant.run()

def speak_response_in_thread(response):
    """Handle speaking response with animation triggers"""
    global current_response_thread
    try:
        sentences = response.split('. ')
        socketio.emit('animation_status', {'status': 'speaking'})  # Set speaking state at beginning
        for sentence in sentences:
            if speech_event.is_set():
                break
            if sentence.strip():
                socketio.emit('assistant_speaking', {'text': sentence})
                assistant.speak_response(sentence + '.')
                if not speech_event.is_set():
                    socketio.sleep(0.2)
    finally:
        current_response_thread = None
        socketio.emit('assistant_done_speaking')
        socketio.emit('animation_status', {'status': 'idle'})  # Reset to idle not listening

def init_db():
    # We'll still maintain the old database table for backward compatibility
    dbase = sqlite3.connect('assistant.db')
    cursor = dbase.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS History_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command TEXT,
        response TEXT
    )
    ''')
    dbase.commit()
    dbase.close()
    
    # Initialize our memory system which creates the new table structure
    memory._ensure_db_setup()
        
def save_to_database(command, response):
    try:
        # Keep the old database for backward compatibility
        dbase = sqlite3.connect('assistant.db')
        cursor = dbase.cursor()
        cursor.execute(
            '''INSERT INTO History_data (command, response) VALUES (?, ?)''',
            (command, response)
        )
        dbase.commit()
        dbase.close()
        
        # Also save to our new memory system
        memory.add_interaction(command, response, current_session_id)
    except Exception as e:
        print(f"Error saving to database: {e}")
        
@app.route('/')
def index():
    return render_template('fe.html')

@app.route('/mic-icon.png')
def mic_icon():
    return send_from_directory('.', 'mic-icon.png')

@app.route('/get_history', methods=['GET'])
def get_history():
    try:
        dbase = sqlite3.connect('assistant.db')
        cursor = dbase.cursor()
        cursor.execute('SELECT command, response FROM History_data ORDER BY id DESC')
        history_data = cursor.fetchall()
        dbase.close()
        
        # Convert to list of dictionaries for JSON response
        formatted_history = [{"command": item[0], "response": item[1]} for item in history_data]
        
        return jsonify({"status": "success", "history": formatted_history})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@socketio.on('connect')
def handle_connect():
    global current_session_id
    # Create a new session when client connects
    current_session_id = memory.get_current_session_id()
    emit('status', {'message': 'Connected to server'})
    emit('session', {'session_id': current_session_id})

@socketio.on('start_recording')
def handle_recording():
    global current_response_thread, speech_event
    try:
        speech_event.set()
        if current_response_thread and current_response_thread.is_alive():
            current_response_thread.join()
        speech_event.clear()
        
        socketio.emit('animation_status', {'status': 'listening'})
        raw_audio = assistant.vad_recorder.record_audio()
        if raw_audio:
            transcription = transcribe_audio(raw_audio)
            if transcription:
                emit('status', {'message': f'Transcribed: {transcription}'})
                socketio.emit('display_transcription', {'text': transcription})
                socketio.emit('animation_status', {'status': 'processing'})  # Add processing state
                
                # Get relevant conversation history for context
                memory_context = memory.format_history_for_llm(limit=3, session_id=current_session_id)
                
                # Add any search results if the query seems like it's referencing past information
                if any(keyword in transcription.lower() for keyword in ["remember", "earlier", "before", "previous", "last time"]):
                    search_context = memory.search_memory(transcription)
                    if search_context:
                        memory_context += search_context
                
                # Process with memory context
                response = process_transcript_with_llm(transcription, memory_context, current_session_id)
                socketio.emit('assistant_response', {'text': response, 'query': transcription})

                # Save to both database systems
                save_to_database(transcription, response)
                
                # Speaking animation is now set inside speak_response_in_thread
                current_response_thread = socketio.start_background_task(
                    speak_response_in_thread, response
                )
    
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('new_session')
def handle_new_session():
    global current_session_id
    current_session_id = memory.get_current_session_id()
    emit('session', {'session_id': current_session_id})
    emit('status', {'message': 'Started new conversation session'})

@socketio.on('clear_memory')
def handle_clear_memory(data=None):
    session_id = data.get('session_id') if data else None
    memory.clear_memory(session_id)
    emit('status', {'message': 'Memory cleared successfully'})

@socketio.on('interrupt')
def handle_interruption():
    global speech_event
    speech_event.set()
    assistant.is_speaking = False
    emit('status', {'message': 'Speech interrupted'})

@socketio.on('stop_recording')
def handle_stop_recording():
    try:
        assistant.is_speaking = False
        emit('status', {'message': 'Recording stopped'})
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('disconnect')
def handle_disconnect():
    assistant.should_stop = True
    emit('status', {'message': 'Disconnected from server'})

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, port=5000)