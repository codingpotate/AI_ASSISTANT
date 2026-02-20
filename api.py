from flask import Flask, request, jsonify
from flask_cors import CORS
from app import PersonalAssistant

app = Flask(__name__)
CORS(app)

# Cache assistants per session to maintain conversation history
assistants = {}

def get_assistant(session_id):
    if session_id not in assistants:
        assistants[session_id] = PersonalAssistant(mode="text")
    return assistants[session_id]

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/command', methods=['POST'])
def command():
    data = request.get_json()
    if not data or 'command' not in data or 'session_id' not in data:
        return jsonify({"error": "Missing command or session_id"}), 400
    cmd = data['command']
    session_id = data['session_id']
    assistant = get_assistant(session_id)
    response = assistant.ai_core.process_command(cmd)
    return jsonify({"response": response})

@app.route('/api/history/<session_id>', methods=['GET'])
def history(session_id):
    assistant = get_assistant(session_id)
    # Return the raw conversation history (list of dicts)
    return jsonify(assistant.ai_core.conversation_history)

@app.route('/api/plugins', methods=['GET'])
def plugins():
    # Use a dummy session to get plugin list
    assistant = get_assistant("dummy")
    plugins = assistant.plugin_registry.get_all_plugins()
    plugin_list = [{"name": p.get_name(), "description": p.get_description()} for p in plugins]
    return jsonify(plugin_list)

if __name__ == '__main__':
    app.run(debug=True, port=5000)