import platform
import os
from assistant.plugin_base import AssistantPlugin

class SystemInfoPlugin(AssistantPlugin):
    def get_name(self):
        return "system_info"

    def get_description(self):
        return "Get information about the system (OS, processor, memory, etc.)"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {}
        }

    def execute(self):
        info = []
        info.append(f"System: {platform.system()} {platform.release()}")
        info.append(f"Node: {platform.node()}")
        info.append(f"Processor: {platform.processor()}")
        info.append(f"Machine: {platform.machine()}")
        try:
            import psutil
            mem = psutil.virtual_memory()
            info.append(f"Memory: {mem.total / (1024**3):.1f} GB total, {mem.available / (1024**3):.1f} GB available")
            cpu_percent = psutil.cpu_percent(interval=1)
            info.append(f"CPU Usage: {cpu_percent}%")
        except ImportError:
            pass
        return "\n".join(info)