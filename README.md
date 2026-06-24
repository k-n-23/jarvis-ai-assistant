Here you go, just copy and paste this:
# JARVIS — Personal AI Assistant

A voice + text AI assistant for Windows powered by Claude, with real tool use.

## Features

| Skill | What it does |
|---|---|
| 🖥️ Shell commands | Run any Windows command and get the output |
| 🌐 Web search | Opens Google search in your browser |
| 📂 Open apps/files | Launch Notepad, Chrome, VS Code, Discord, etc. |
| 🌤️ Weather | Live weather for any city (OpenWeatherMap) |
| 🎙️ Voice input | Speak to it via microphone |
| 🔊 Text-to-speech | Talks back using your system voice |

## Setup

### 1. Install Python dependencies

pip install -r requirements.txt

PyAudio on Windows can be tricky. If pip install pyaudio fails, run:

pip install pipwin
pipwin install pyaudio

### 2. Set your API keys

set ANTHROPIC_API_KEY=your-claude-api-key-here
set WEATHER_API_KEY=your-openweathermap-key-here
set JARVIS_CITY=Sydney

### 3. Run it

python jarvis.py

## Usage

| Input | What happens |
|---|---|
| Type normally | Text mode (default) |
| Type `voice` | Switch to voice input |
| Type `type` | Switch back to typing |
| Type `clear` | Clear conversation history |
| Type `quit` | Exit |

## Example Commands

- "What's the weather like?"
- "Open Notepad"
- "Run ipconfig and tell me my IP address"
- "Search for Claude API pricing"
- "What time is it?"
- "List the files in my Downloads folder"

## Tech Stack

- Claude claude-sonnet-4-6 via Anthropic API (tool use / function calling)
- SpeechRecognition + Google Speech API for voice input
- pyttsx3 for offline text-to-speech
- OpenWeatherMap API for weather data
- subprocess for shell command execution
