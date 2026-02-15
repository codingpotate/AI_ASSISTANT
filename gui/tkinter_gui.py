import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
from datetime import datetime
import time
import os
import re

class AssistantGUI:
    def __init__(self, assistant):
        self.assistant = assistant
        self.root = tk.Tk()
        self.setup_style()
        self.setup_window()
        self.setup_widgets()
        self.message_queue = queue.Queue()
        self.setup_reminder_callback()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        self.bg_dark = '#1a1a1a'
        self.bg_medium = '#2d2d2d'
        self.bg_light = '#3a3a3a'
        self.accent = '#10a37f'
        self.text_primary = '#e0e0e0'
        self.text_secondary = '#a0a0a0'
        self.text_accent = '#10a37f'
        
        style.configure('TFrame', background=self.bg_dark)
        style.configure('TLabel', background=self.bg_dark, foreground=self.text_primary, font=('Segoe UI', 10))
        style.configure('TButton', background=self.bg_light, foreground=self.text_primary, borderwidth=0, focuscolor='none', font=('Segoe UI', 9))
        style.map('TButton',
                  background=[('active', self.accent), ('pressed', self.accent)],
                  foreground=[('active', 'white')])
        style.configure('Accent.TButton', background=self.accent, foreground='white', font=('Segoe UI', 9, 'bold'))
        style.map('Accent.TButton',
                  background=[('active', '#0e8c6f'), ('pressed', '#0e8c6f')])
        style.configure('TEntry', fieldbackground=self.bg_light, foreground=self.text_primary, insertcolor=self.accent, borderwidth=0)
        style.configure('TCombobox', fieldbackground=self.bg_light, foreground=self.text_primary, arrowcolor=self.text_secondary)
        style.configure('TNotebook', background=self.bg_dark, tabmargins=[2, 5, 2, 0])
        style.configure('TNotebook.Tab', background=self.bg_medium, foreground=self.text_secondary, padding=[10, 2])
        style.map('TNotebook.Tab', background=[('selected', self.accent)], foreground=[('selected', 'white')])

    def setup_window(self):
        self.root.title("AI Personal Assistant")
        self.root.geometry("1000x700")
        self.root.configure(bg=self.bg_dark)
        self.root.resizable(True, True)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def setup_widgets(self):
        # Header with gradient effect using canvas
        header_canvas = tk.Canvas(self.root, height=100, bg=self.bg_dark, highlightthickness=0)
        header_canvas.grid(row=0, column=0, sticky='ew', padx=0, pady=0)
        header_canvas.grid_columnconfigure(0, weight=1)
        header_canvas.create_rectangle(0, 0, 2000, 100, fill=self.bg_medium, outline='')
        header_canvas.create_text(500, 50, text="AI Personal Assistant", fill='white', font=('Segoe UI', 28, 'bold'), anchor='center')
        header_canvas.create_text(500, 80, text="Your intelligent companion for daily tasks", fill=self.text_secondary, font=('Segoe UI', 11), anchor='center')

        # Main content area with two columns: sidebar and conversation
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Sidebar
        sidebar = ttk.Frame(main_frame, width=150)
        sidebar.grid(row=0, column=0, sticky='ns', padx=(0, 10))
        sidebar.grid_propagate(False)
        
        # Sidebar buttons with icons (emoji)
        buttons = [
            ("🎤 Voice", self.toggle_voice),
            ("🗑️ Clear", self.clear_conversation),
            ("📋 Plugins", self.show_plugins),
            ("❓ Help", self.show_help),
            ("⚙️ Settings", self.show_settings),
            ("❌ Exit", self.exit_app)
        ]
        for i, (text, cmd) in enumerate(buttons):
            btn = ttk.Button(sidebar, text=text, command=cmd, style='TButton')
            btn.pack(fill='x', pady=2)

        # Conversation area with rounded corners
        conv_frame = tk.Frame(main_frame, bg=self.bg_medium, highlightbackground=self.accent, highlightthickness=0)
        conv_frame.grid(row=0, column=1, sticky='nsew')
        conv_frame.grid_rowconfigure(0, weight=1)
        conv_frame.grid_columnconfigure(0, weight=1)

        # Create a canvas for rounded corners
        canvas = tk.Canvas(conv_frame, bg=self.bg_medium, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky='nsew')
        canvas.grid_rowconfigure(0, weight=1)
        canvas.grid_columnconfigure(0, weight=1)

        # Draw rounded rectangle background
        canvas.create_rectangle(10, 10, 990, 690, fill=self.bg_dark, outline=self.accent, width=1, tags='bg')
        
        # ScrolledText inside canvas
        self.conversation_text = scrolledtext.ScrolledText(
            canvas,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg=self.bg_dark,
            fg=self.text_primary,
            insertbackground=self.accent,
            state=tk.DISABLED,
            relief=tk.FLAT,
            borderwidth=0,
            spacing1=5,
            spacing3=5
        )
        canvas.create_window(15, 15, window=self.conversation_text, anchor='nw', width=970, height=660, tags='text')

        # Text tags for colors
        self.conversation_text.tag_config('timestamp', foreground=self.text_secondary, font=('Segoe UI', 9))
        self.conversation_text.tag_config('user_label', foreground=self.accent, font=('Segoe UI', 10, 'bold'))
        self.conversation_text.tag_config('user_message', foreground=self.text_primary, font=('Segoe UI', 10))
        self.conversation_text.tag_config('assistant_label', foreground='#4f9e9e', font=('Segoe UI', 10, 'bold'))
        self.conversation_text.tag_config('assistant_message', foreground='#c0c0c0', font=('Segoe UI', 10))
        self.conversation_text.tag_config('system_label', foreground='#e06c75', font=('Segoe UI', 10, 'bold'))
        self.conversation_text.tag_config('system_message', foreground='#d19a66', font=('Segoe UI', 10, 'italic'))
        self.conversation_text.tag_config('reminder_label', foreground='#c678dd', font=('Segoe UI', 10, 'bold'))
        self.conversation_text.tag_config('reminder_message', foreground='#c678dd', font=('Segoe UI', 10))

        # Input area at bottom
        input_frame = ttk.Frame(self.root)
        input_frame.grid(row=2, column=0, sticky='ew', padx=20, pady=10)
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_var, font=('Segoe UI', 11))
        self.input_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.input_entry.bind('<Return>', self.send_message)

        send_button = ttk.Button(input_frame, text="Send", command=self.send_message, style='Accent.TButton')
        send_button.grid(row=0, column=1)

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Type your message and press Enter")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.FLAT, anchor=tk.W, font=('Segoe UI', 9))
        status_bar.grid(row=3, column=0, sticky='ew', padx=20, pady=(0, 10))

        self.input_entry.focus()
        self.add_system_message("AI Personal Assistant initialized and ready.")
        self.add_system_message("Type 'help' to see available commands or ask me anything.")

    def setup_reminder_callback(self):
        def reminder_callback(reminder_text):
            self.message_queue.put(("reminder", reminder_text))
        self.assistant.reminder_callback = reminder_callback

    def add_message(self, sender, message):
        self.conversation_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')

        if sender == "You":
            self.conversation_text.insert(tk.END, "You: ", 'user_label')
            self.conversation_text.insert(tk.END, f"{message}\n\n", 'user_message')
        elif sender == "Assistant":
            self.conversation_text.insert(tk.END, "Assistant: ", 'assistant_label')
            self.conversation_text.insert(tk.END, f"{message}\n\n", 'assistant_message')
        elif sender == "System":
            self.conversation_text.insert(tk.END, "System: ", 'system_label')
            self.conversation_text.insert(tk.END, f"{message}\n\n", 'system_message')
        elif sender == "Reminder":
            self.conversation_text.insert(tk.END, "REMINDER: ", 'reminder_label')
            self.conversation_text.insert(tk.END, f"{message}\n\n", 'reminder_message')

        self.conversation_text.config(state=tk.DISABLED)
        self.conversation_text.see(tk.END)

    def add_system_message(self, message):
        self.conversation_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation_text.insert(tk.END, f"[{timestamp}] System: ", 'system_label')
        self.conversation_text.insert(tk.END, f"{message}\n\n", 'system_message')
        self.conversation_text.config(state=tk.DISABLED)
        self.conversation_text.see(tk.END)

    def send_message(self, event=None):
        message = self.input_var.get().strip()
        if not message:
            return

        self.input_var.set("")
        self.add_message("You", message)
        self.status_var.set("Processing your request...")
        self.input_entry.config(state='disabled')

        thread = threading.Thread(target=self.process_message, args=(message,), daemon=True)
        thread.start()

    def process_message(self, message):
        try:
            lower = message.lower()
            if lower == 'exit':
                self.message_queue.put(("exit", None))
            elif lower == 'help':
                self.message_queue.put(("help", None))
            elif lower == 'clear':
                self.message_queue.put(("clear", None))
            elif lower == 'plugins':
                self.message_queue.put(("plugins", None))
            elif lower == 'stats':
                self.message_queue.put(("stats", None))
            else:
                response = self.assistant.ai_core.process_command(message)
                self.message_queue.put(("response", response))
        except Exception as e:
            self.message_queue.put(("error", str(e)))

    def toggle_voice(self):
        self.add_system_message("Voice mode requires microphone setup. Using text input.")
        messagebox.showinfo(
            "Voice Mode Information",
            "Voice input is currently in simulation mode.\n\n"
            "Type commands normally or use 'jarvis' prefix to simulate voice.\n"
            "Example: 'jarvis what time is it'\n\n"
            "To enable real voice input, install PyAudio and SpeechRecognition.",
            parent=self.root
        )

    def clear_conversation(self):
        self.conversation_text.config(state=tk.NORMAL)
        self.conversation_text.delete(1.0, tk.END)
        self.conversation_text.config(state=tk.DISABLED)
        self.add_system_message("Conversation cleared")
        self.status_var.set("Conversation cleared")

    def show_plugins(self):
        plugins_text = self.get_plugins_text()
        win = tk.Toplevel(self.root)
        win.title("Available Plugins")
        win.geometry("600x450")
        win.configure(bg=self.bg_dark)

        header = tk.Label(
            win,
            text="Available Plugins",
            font=('Segoe UI', 16, 'bold'),
            bg=self.bg_dark,
            fg=self.accent
        )
        header.pack(pady=(15, 10))

        text = scrolledtext.ScrolledText(
            win,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg=self.bg_medium,
            fg=self.text_primary,
            insertbackground=self.accent,
            width=70,
            height=20,
            relief=tk.FLAT,
            borderwidth=0
        )
        text.pack(expand=True, fill='both', padx=15, pady=10)
        text.insert(tk.END, plugins_text)
        text.config(state=tk.DISABLED)

    def show_help(self):
        help_text = self.get_help_text()
        win = tk.Toplevel(self.root)
        win.title("Assistant Help")
        win.geometry("650x500")
        win.configure(bg=self.bg_dark)

        header = tk.Label(
            win,
            text="Assistant Commands & Features",
            font=('Segoe UI', 16, 'bold'),
            bg=self.bg_dark,
            fg=self.accent
        )
        header.pack(pady=(15, 10))

        text = scrolledtext.ScrolledText(
            win,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg=self.bg_medium,
            fg=self.text_primary,
            insertbackground=self.accent,
            width=75,
            height=25,
            relief=tk.FLAT,
            borderwidth=0
        )
        text.pack(expand=True, fill='both', padx=15, pady=10)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)

    def show_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("600x500")
        win.configure(bg=self.bg_dark)
        win.resizable(False, False)

        header = tk.Label(
            win,
            text="Settings",
            font=('Segoe UI', 16, 'bold'),
            bg=self.bg_dark,
            fg=self.accent
        )
        header.pack(pady=(15, 10))

        notebook = ttk.Notebook(win)
        notebook.pack(expand=True, fill='both', padx=20, pady=10)

        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text="API Keys")

        pref_frame = ttk.Frame(notebook)
        notebook.add(pref_frame, text="Preferences")

        env_vars = self._load_env_file()

        # API Keys
        row = 0
        api_labels = [
            ("Gemini API Key", "GEMINI_API_KEY"),
            ("Weather API Key", "WEATHER_API_KEY"),
            ("News API Key", "NEWS_API_KEY"),
        ]
        self.api_entries = {}
        for label, key in api_labels:
            ttk.Label(api_frame, text=label).grid(row=row, column=0, sticky='w', padx=10, pady=5)
            entry = ttk.Entry(api_frame, width=50)
            entry.insert(0, env_vars.get(key, ''))
            entry.grid(row=row, column=1, padx=10, pady=5)
            self.api_entries[key] = entry
            row += 1

        # Preferences
        row = 0
        ttk.Label(pref_frame, text="Default City").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.default_city_entry = ttk.Entry(pref_frame, width=30)
        self.default_city_entry.insert(0, env_vars.get('DEFAULT_CITY', 'London'))
        self.default_city_entry.grid(row=row, column=1, padx=10, pady=5)
        row += 1

        ttk.Label(pref_frame, text="Default News Category").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.news_category_combo = ttk.Combobox(pref_frame, values=['general', 'technology', 'business', 'sports', 'entertainment', 'health', 'science'], width=28, state='readonly')
        self.news_category_combo.set(env_vars.get('DEFAULT_NEWS_CATEGORY', 'general'))
        self.news_category_combo.grid(row=row, column=1, padx=10, pady=5)
        row += 1

        ttk.Label(pref_frame, text="Assistant Name").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.assistant_name_entry = ttk.Entry(pref_frame, width=30)
        self.assistant_name_entry.insert(0, env_vars.get('ASSISTANT_NAME', 'Jarvis'))
        self.assistant_name_entry.grid(row=row, column=1, padx=10, pady=5)

        save_btn = ttk.Button(win, text="Save Settings", command=lambda: self._save_settings(win), style='Accent.TButton')
        save_btn.pack(pady=15)

    def _load_env_file(self):
        env_vars = {}
        env_path = '.env'
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
        return env_vars

    def _save_settings(self, win):
        updates = {}
        for key, entry in self.api_entries.items():
            value = entry.get().strip()
            if value:
                updates[key] = value
        if self.default_city_entry.get().strip():
            updates['DEFAULT_CITY'] = self.default_city_entry.get().strip()
        if self.news_category_combo.get():
            updates['DEFAULT_NEWS_CATEGORY'] = self.news_category_combo.get()
        if self.assistant_name_entry.get().strip():
            updates['ASSISTANT_NAME'] = self.assistant_name_entry.get().strip()

        env_path = '.env'
        lines = []
        updated_keys = set()
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line_strip = line.strip()
                    if line_strip and not line_strip.startswith('#') and '=' in line_strip:
                        key = line_strip.split('=', 1)[0].strip()
                        if key in updates:
                            lines.append(f"{key}={updates[key]}\n")
                            updated_keys.add(key)
                        else:
                            lines.append(line)
                    else:
                        lines.append(line)
            for key, value in updates.items():
                if key not in updated_keys:
                    lines.append(f"{key}={value}\n")
        else:
            for key, value in updates.items():
                lines.append(f"{key}={value}\n")

        with open(env_path, 'w') as f:
            f.writelines(lines)

        messagebox.showinfo("Settings Saved", "Settings saved. Restart the application for changes to take effect.", parent=win)
        win.destroy()

    def exit_app(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit the AI Assistant?", parent=self.root):
            self.root.quit()
            self.root.destroy()

    def check_queue(self):
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                if msg_type == "response":
                    self.add_message("Assistant", data)
                    self.status_var.set("Ready")
                    self.input_entry.config(state='normal')
                    self.input_entry.focus()
                elif msg_type == "error":
                    self.add_system_message(f"Error: {data}")
                    self.status_var.set(f"Error: {data}")
                    self.input_entry.config(state='normal')
                    self.input_entry.focus()
                elif msg_type == "exit":
                    self.exit_app()
                elif msg_type == "clear":
                    self.clear_conversation()
                elif msg_type == "reminder":
                    self.add_message("Reminder", data)
                    self.root.bell()
                    self.flash_window_title(f"REMINDER: {data[:40]}")
                elif msg_type == "help":
                    self.show_help()
                    self.status_var.set("Ready")
                    self.input_entry.config(state='normal')
                    self.input_entry.focus()
                elif msg_type == "plugins":
                    self.show_plugins()
                    self.status_var.set("Ready")
                    self.input_entry.config(state='normal')
                    self.input_entry.focus()
                elif msg_type == "stats":
                    stats_text = self.get_stats_text()
                    self.add_message("Assistant", stats_text)
                    self.status_var.set("Ready")
                    self.input_entry.config(state='normal')
                    self.input_entry.focus()
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def flash_window_title(self, message):
        original_title = self.root.title()
        for _ in range(3):
            self.root.title(f"REMINDER: {message}")
            self.root.update()
            time.sleep(0.3)
            self.root.title(original_title)
            self.root.update()
            time.sleep(0.3)

    def get_help_text(self):
        return """AI PERSONAL ASSISTANT - COMMAND REFERENCE
===========================================

CORE FUNCTIONALITIES:
• Natural Language Conversation
  - Ask questions in plain English
  - Get intelligent, contextual responses

• Smart Reminder System
  - Set reminders with natural language
  - Background checking for due reminders
  - Examples:
    * "remind me to call mom in 2 hours"
    * "set reminder for meeting tomorrow at 2pm"
    * "remind me to buy groceries in 30 minutes"

• Information & Tools
  - Current time and date
  - Weather forecasts for any city
  - Latest news headlines
  - Calendar event management
  - Mathematical calculations
  - System information
  - Web search
  - Notes

PLUGIN SYSTEM:
The assistant supports extensible plugins for additional functionality.
Current available plugins can be viewed using the 'Show Plugins' button.

SYSTEM COMMANDS:
• help - Show this help dialog
• clear - Clear conversation history
• plugins - List available plugins
• stats - Show usage statistics
• exit - Quit the application

QUICK START EXAMPLES:
1. "What's the weather in London?"
2. "Show me today's news"
3. "What time is it?"
4. "Remind me to water plants in 1 hour"
5. "Calculate 15 * 27 + 42"
6. "What's on my calendar today?"
7. "Save note Buy milk"
8. "Show my notes"
9. "System info"
10. "Search for Python programming"

TIPS:
• Be specific with your requests for better results
• Use natural language - the assistant understands context
• Check plugins for additional capabilities
• Reminders work in the background - no need to keep asking

For issues or feature requests, please check the documentation."""

    def get_plugins_text(self):
        if hasattr(self.assistant, 'plugin_registry'):
            plugins = self.assistant.plugin_registry.get_all_plugins()
            plugins_text = "AVAILABLE PLUGINS\n"
            plugins_text += "=================\n\n"
            if not plugins:
                plugins_text += "No plugins currently loaded.\n"
                plugins_text += "Check the plugins directory for available plugins.\n"
            else:
                for plugin in plugins:
                    plugins_text += f"🔧 {plugin.get_name().upper()}\n"
                    plugins_text += f"   {plugin.get_description()}\n"
                    params = plugin.get_parameters()
                    if params and 'properties' in params:
                        param_keys = list(params['properties'].keys())
                        if param_keys:
                            plugins_text += f"   Parameters: {', '.join(param_keys)}\n"
                    plugins_text += "\n"
                plugins_text += f"\nTotal plugins: {len(plugins)}\n"
                plugins_text += "Plugins are automatically loaded from the plugins directory."
            return plugins_text
        return "Plugin system not available or not initialized."

    def get_stats_text(self):
        if hasattr(self.assistant, 'database'):
            stats = self.assistant.database.get_plugin_stats()
            stats_text = "ASSISTANT STATISTICS\n"
            stats_text += "===================\n\n"
            stats_text += f"Total Plugins: {stats['total_plugins']}\n"
            stats_text += f"Total Executions: {stats['total_executions']}\n\n"
            if stats['plugins']:
                stats_text += "PLUGIN USAGE:\n"
                stats_text += "-------------\n"
                for plugin in stats['plugins']:
                    plugin_name = plugin['plugin_name']
                    executions = plugin['total_executions']
                    sessions = plugin['unique_sessions']
                    last_used = plugin['last_used']
                    stats_text += f"{plugin_name}:\n"
                    stats_text += f"  Executions: {executions}\n"
                    stats_text += f"  Sessions: {sessions}\n"
                    if last_used:
                        stats_text += f"  Last Used: {last_used[:19]}\n"
                    stats_text += "\n"
            else:
                stats_text += "No plugin usage data available.\n"
            return stats_text
        return "Database not available or not initialized."

    def run(self):
        self.root.after(100, self.check_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.root.mainloop()