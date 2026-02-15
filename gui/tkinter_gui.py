"""
Tkinter GUI for the AI Personal Assistant
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
from datetime import datetime
import time

class AssistantGUI:
    def __init__(self, assistant):
        self.assistant = assistant
        self.root = tk.Tk()
        self.setup_window()
        self.setup_widgets()
        self.message_queue = queue.Queue()
        
        self.setup_reminder_callback()
        self.start_reminder_checker()
        
    def setup_window(self):
        self.root.title("AI Personal Assistant")
        self.root.geometry("900x750")
        self.root.configure(bg='#f8f9fa')
        self.root.resizable(True, True)
        
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def setup_widgets(self):
        header_frame = tk.Frame(self.root, bg='#1a237e', height=120)
        header_frame.grid(row=0, column=0, sticky='ew', padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = tk.Label(
            header_frame,
            text="AI Personal Assistant",
            font=('Segoe UI', 28, 'bold'),
            fg='white',
            bg='#1a237e'
        )
        title_label.grid(row=0, column=0, pady=(20, 5))
        
        subtitle_label = tk.Label(
            header_frame,
            text="Your intelligent companion for daily tasks",
            font=('Segoe UI', 11),
            fg='#bbdefb',
            bg='#1a237e'
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 20))
        
        main_frame = tk.Frame(self.root, bg='#ffffff')
        main_frame.grid(row=1, column=0, sticky='nsew', padx=15, pady=15)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        conversation_container = tk.Frame(main_frame, bg='#ffffff')
        conversation_container.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        conversation_container.grid_rowconfigure(0, weight=1)
        conversation_container.grid_columnconfigure(0, weight=1)
        
        self.conversation_text = scrolledtext.ScrolledText(
            conversation_container,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg='#ffffff',
            fg='#2c3e50',
            state=tk.DISABLED,
            height=25,
            width=80,
            relief=tk.FLAT,
            borderwidth=0,
            spacing1=5,
            spacing3=5
        )
        self.conversation_text.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)
        
        self.conversation_text.tag_config('timestamp', foreground='#7f8c8d', font=('Segoe UI', 9))
        self.conversation_text.tag_config('user_label', foreground='#1565c0', font=('Segoe UI', 10, 'bold'))
        self.conversation_text.tag_config('user_message', foreground='#0d47a1', font=('Segoe UI', 10))
        self.conversation_text.tag_config('assistant_label', foreground='#2e7d32', font=('Segoe UI', 10, 'bold'))
        self.conversation_text.tag_config('assistant_message', foreground='#1b5e20', font=('Segoe UI', 10))
        self.conversation_text.tag_config('system_label', foreground='#c62828', font=('Segoe UI', 10, 'bold'))
        self.conversation_text.tag_config('system_message', foreground='#b71c1c', font=('Segoe UI', 10, 'italic'))
        self.conversation_text.tag_config('reminder_label', foreground='#6a1b9a', font=('Segoe UI', 10, 'bold'))
        self.conversation_text.tag_config('reminder_message', foreground='#4a148c', font=('Segoe UI', 10))
        
        input_frame = tk.Frame(main_frame, bg='#f5f5f5', relief=tk.RAISED, borderwidth=1)
        input_frame.grid(row=1, column=0, sticky='ew', padx=0, pady=(15, 0))
        input_frame.grid_columnconfigure(0, weight=1)
        
        input_container = tk.Frame(input_frame, bg='#ffffff')
        input_container.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        input_container.grid_columnconfigure(0, weight=1)
        
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            input_container,
            textvariable=self.input_var,
            font=('Segoe UI', 11)
        )
        self.input_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10), pady=0)
        self.input_entry.bind('<Return>', self.send_message)
        
        send_button = tk.Button(
            input_container,
            text="Send",
            command=self.send_message,
            bg='#1a237e',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            borderwidth=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        send_button.grid(row=0, column=1, padx=0, pady=0)
        
        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.grid(row=2, column=0, sticky='ew', padx=0, pady=(15, 0))
        
        buttons = [
            ("Voice Mode", self.toggle_voice, '#3949ab'),
            ("Clear Chat", self.clear_conversation, '#546e7a'),
            ("Show Plugins", self.show_plugins, '#5e35b1'),
            ("Show Help", self.show_help, '#00897b'),
            ("Settings", self.show_settings, '#455a64'),
            ("Exit", self.exit_app, '#c62828')
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                bg=color,
                fg='white',
                font=('Segoe UI', 9, 'bold'),
                relief=tk.FLAT,
                borderwidth=0,
                padx=12,
                pady=6,
                cursor='hand2'
            )
            btn.grid(row=0, column=i, padx=2, pady=0, sticky='ew')
            button_frame.grid_columnconfigure(i, weight=1)
        
        self.status_var = tk.StringVar(value="Ready - Type your message and press Enter")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=('Segoe UI', 9),
            background='#e8eaf6',
            foreground='#1a237e'
        )
        status_bar.grid(row=2, column=0, sticky='ew', padx=0, pady=0)
        
        self.input_entry.focus()
        
        self.add_system_message("AI Personal Assistant initialized and ready.")
        self.add_system_message("Type 'help' to see available commands or ask me anything.")
        
    def setup_reminder_callback(self):
        def reminder_callback(reminder_text):
            self.message_queue.put(("reminder", reminder_text))
        
        self.assistant.reminder_callback = reminder_callback
        
    def start_reminder_checker(self):
        def check_reminders_periodically():
            while True:
                try:
                    if (hasattr(self.assistant, 'skills') and 
                        self.assistant.skills and 
                        hasattr(self.assistant.skills, 'database') and 
                        self.assistant.skills.database):
                        
                        session_id = getattr(self.assistant.skills, 'session_id', 'default_session')
                        overdue = self.assistant.skills.database.get_due_reminders(session_id)
                        
                        if overdue:
                            for reminder in overdue:
                                reminder_text = reminder.get('reminder_text', 'Unknown reminder')
                                self.message_queue.put(("reminder", reminder_text))
                                
                                if 'id' in reminder:
                                    self.assistant.skills.database.mark_reminder_completed(reminder['id'])
                    
                    time.sleep(5)
                    
                except Exception:
                    time.sleep(10)
        
        thread = threading.Thread(target=check_reminders_periodically, daemon=True)
        thread.start()
        
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
            if message.lower() == 'exit':
                self.message_queue.put(("exit", None))
                return
            elif message.lower() == 'help':
                self.message_queue.put(("help", None))
                return
            elif message.lower() == 'clear':
                self.message_queue.put(("clear", None))
                return
            elif message.lower() == 'plugins':
                self.message_queue.put(("plugins", None))
                return
            elif message.lower() == 'stats':
                self.message_queue.put(("stats", None))
                return
            
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
            "To enable real voice input, install PyAudio and SpeechRecognition."
        )
        
    def clear_conversation(self):
        self.conversation_text.config(state=tk.NORMAL)
        self.conversation_text.delete(1.0, tk.END)
        self.conversation_text.config(state=tk.DISABLED)
        self.add_system_message("Conversation cleared")
        self.status_var.set("Conversation cleared")
        
    def show_plugins(self):
        plugins_text = self.get_plugins_text()
        
        plugins_window = tk.Toplevel(self.root)
        plugins_window.title("Available Plugins")
        plugins_window.geometry("600x450")
        plugins_window.configure(bg='#ffffff')
        
        header_label = tk.Label(
            plugins_window,
            text="Available Plugins",
            font=('Segoe UI', 16, 'bold'),
            bg='#ffffff',
            fg='#1a237e'
        )
        header_label.pack(pady=(15, 10))
        
        text_widget = scrolledtext.ScrolledText(
            plugins_window,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg='#ffffff',
            fg='#2c3e50',
            width=70,
            height=20
        )
        text_widget.pack(expand=True, fill='both', padx=15, pady=10)
        text_widget.insert(tk.END, plugins_text)
        text_widget.config(state=tk.DISABLED)
        
    def show_help(self):
        help_text = self.get_help_text()
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Assistant Help")
        help_window.geometry("650x500")
        help_window.configure(bg='#ffffff')
        
        header_label = tk.Label(
            help_window,
            text="Assistant Commands & Features",
            font=('Segoe UI', 16, 'bold'),
            bg='#ffffff',
            fg='#1a237e'
        )
        header_label.pack(pady=(15, 10))
        
        text_widget = scrolledtext.ScrolledText(
            help_window,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            bg='#ffffff',
            fg='#2c3e50',
            width=75,
            height=25
        )
        text_widget.pack(expand=True, fill='both', padx=15, pady=10)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Assistant Settings")
        settings_window.geometry("500x400")
        settings_window.configure(bg='#ffffff')
        
        header_label = tk.Label(
            settings_window,
            text="Assistant Settings",
            font=('Segoe UI', 16, 'bold'),
            bg='#ffffff',
            fg='#1a237e'
        )
        header_label.pack(pady=(15, 10))
        
        settings_frame = tk.Frame(settings_window, bg='#ffffff')
        settings_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        tk.Label(
            settings_frame,
            text="Settings functionality coming soon",
            font=('Segoe UI', 11),
            bg='#ffffff',
            fg='#546e7a'
        ).pack(pady=20)
        
        tk.Label(
            settings_frame,
            text="Future settings will include:",
            font=('Segoe UI', 10, 'bold'),
            bg='#ffffff',
            fg='#1a237e'
        ).pack(anchor='w', pady=(10, 5))
        
        features = [
            "• API key configuration",
            "• Voice settings",
            "• Theme selection",
            "• Notification preferences",
            "• Default city for weather"
        ]
        
        for feature in features:
            tk.Label(
                settings_frame,
                text=feature,
                font=('Segoe UI', 9),
                bg='#ffffff',
                fg='#546e7a'
            ).pack(anchor='w', padx=20, pady=2)
        
    def exit_app(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit the AI Assistant?"):
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