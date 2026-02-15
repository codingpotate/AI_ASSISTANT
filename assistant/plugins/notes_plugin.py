from assistant.plugin_base import AssistantPlugin

class SaveNotePlugin(AssistantPlugin):
    def __init__(self, database=None, session_id=None):
        self.database = database
        self.session_id = session_id

    def get_name(self):
        return "save_note"

    def get_description(self):
        return "Save a note with optional title"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The note content"
                },
                "title": {
                    "type": "string",
                    "description": "Optional title for the note"
                }
            },
            "required": ["content"]
        }

    def execute(self, content: str, title: str = None):
        if not self.database:
            return "Notes system not available."
        note_id = self.database.save_note(self.session_id, content, title)
        return f"Note saved with ID {note_id}."


class ListNotesPlugin(AssistantPlugin):
    def __init__(self, database=None, session_id=None):
        self.database = database
        self.session_id = session_id

    def get_name(self):
        return "list_notes"

    def get_description(self):
        return "List saved notes"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of notes to list"
                }
            },
            "required": []
        }

    def execute(self, limit: int = 10):
        if not self.database:
            return "Notes system not available."
        notes = self.database.get_notes(self.session_id, limit)
        if not notes:
            return "No notes found."
        lines = ["Your notes:"]
        for n in notes:
            title = n.get('title') or "Untitled"
            preview = n.get('content', '')[:50]
            lines.append(f"{n['id']}: {title} - {preview}...")
        return "\n".join(lines)


class GetNotePlugin(AssistantPlugin):
    def __init__(self, database=None, session_id=None):
        self.database = database
        self.session_id = session_id

    def get_name(self):
        return "get_note"

    def get_description(self):
        return "Retrieve a specific note by ID"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "note_id": {
                    "type": "integer",
                    "description": "The ID of the note"
                }
            },
            "required": ["note_id"]
        }

    def execute(self, note_id: int):
        if not self.database:
            return "Notes system not available."
        note = self.database.get_note(note_id)
        if not note:
            return f"Note with ID {note_id} not found."
        return f"Note {note_id}:\n{note.get('content', '')}"


class DeleteNotePlugin(AssistantPlugin):
    def __init__(self, database=None, session_id=None):
        self.database = database
        self.session_id = session_id

    def get_name(self):
        return "delete_note"

    def get_description(self):
        return "Delete a note by ID"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "note_id": {
                    "type": "integer",
                    "description": "The ID of the note to delete"
                }
            },
            "required": ["note_id"]
        }

    def execute(self, note_id: int):
        if not self.database:
            return "Notes system not available."
        if self.database.delete_note(note_id):
            return f"Note {note_id} deleted."
        else:
            return f"Note with ID {note_id} not found."