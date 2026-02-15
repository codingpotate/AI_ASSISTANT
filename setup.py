#!/usr/bin/env python3
"""
Setup script for AI Personal Assistant
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(text)
    print("="*60)

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_requirements():
    """Install required packages"""
    print_header("Installing Requirements")
    
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print("Error: requirements.txt not found")
        return False
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("Requirements installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to install requirements")
        return False

def setup_environment():
    """Setup environment variables"""
    print_header("Environment Setup")
    
    env_example = ".env.example"
    env_file = ".env"
    
    if not os.path.exists(env_example):
        print("Error: .env.example not found")
        return False
    
    if not os.path.exists(env_file):
        shutil.copy(env_example, env_file)
        print(f"Created {env_file} from template")
        print("Please edit .env file to add your API keys")
    else:
        print(f"{env_file} already exists")
    
    return True

def check_directories():
    """Check and create necessary directories"""
    print_header("Checking Directories")
    
    directories = [
        "gui",
        "assistant/plugins",
        "logs",
        "data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created/verified directory: {directory}")
    
    return True

def run_tests():
    """Run basic tests"""
    print_header("Running Basic Tests")
    
    test_commands = [
        [sys.executable, "-c", "import tkinter; print('Tkinter: OK')"],
        [sys.executable, "-c", "import requests; print('Requests: OK')"],
        [sys.executable, "-c", "import sqlite3; print('SQLite3: OK')"],
    ]
    
    all_passed = True
    for cmd in test_commands:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Test passed: {cmd[2]}")
        except subprocess.CalledProcessError:
            print(f"Test failed: {cmd[2]}")
            all_passed = False
    
    return all_passed

def main():
    """Main setup function"""
    print_header("AI Personal Assistant Setup")
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing requirements", install_requirements),
        ("Setting up environment", setup_environment),
        ("Creating directories", check_directories),
        ("Running tests", run_tests)
    ]
    
    all_passed = True
    for step_name, step_func in steps:
        print(f"\nStep: {step_name}")
        try:
            if not step_func():
                all_passed = False
                print(f"Step failed: {step_name}")
        except Exception as e:
            print(f"Error in {step_name}: {e}")
            all_passed = False
    
    if all_passed:
        print_header("Setup Completed Successfully")
        print("\nNext steps:")
        print("1. Edit .env file and add your API keys")
        print("2. Run: python app.py --gui (for GUI mode)")
        print("3. Run: python app.py --voice (for voice mode)")
        print("4. Run: python app.py --text (for text mode)")
    else:
        print_header("Setup Failed")
        print("\nSome steps failed. Please check the errors above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())