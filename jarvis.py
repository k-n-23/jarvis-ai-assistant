import os
import json
import subprocess
import webbro wser
import anthropic
import requests
import sys

# Optional voice imports — gracefully skipped if not installed
try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# --- Config ---
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
DEFAULT_CITY = os.environ.get("JARVIS_CITY", "New York")

# --- TTS setup ---
tts_engine = None
if TTS_AVAILABLE:
    try:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty("rate", 170)
        voices = tts_engine.getProperty("voices")
        if voices:
            tts_engine.setProperty("voice", voices[0].id)
    except Exception:
        tts_engine = None


def speak(text: str) -> None:
    print(f"\nJarvis: {text}")
    if tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception:
            pass


def listen() -> str | None:
    if not VOICE_AVAILABLE:
        return None
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening... (speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=12)
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        speak("I didn't catch that. Could you repeat?")
        return None
    except Exception as e:
        print(f"Voice error: {e}")
        return None


# --- Tool implementations ---

def run_shell_command(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = (result.stdout + result.stderr).strip()
        return output if output else "Command ran successfully (no output)."
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def search_web(query: str) -> str:
    encoded = requests.utils.quote(query)
    webbrowser.open(f"https://www.google.com/search?q={encoded}")
    return f"Opened browser: searching for '{query}'"


def open_application(target: str) -> str:
    try:
        subprocess.Popen(f'start "" "{target}"', shell=True)
        return f"Opened: {target}"
    except Exception as e:
        return f"Failed to open '{target}': {e}"


def get_weather(city: str = "") -> str:
    target = city.strip() or DEFAULT_CITY
    if not WEATHER_API_KEY:
        return (
            "Weather API key not set. "
            "Get a free key at openweathermap.org and set WEATHER_API_KEY."
        )
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": target, "appid": WEATHER_API_KEY, "units": "metric"},
            timeout=10,
        )
        data = resp.json()
        if resp.status_code == 200:
            t = data["main"]["temp"]
            fl = data["main"]["feels_like"]
            desc = data["weather"][0]["description"]
            hum = data["main"]["humidity"]
            return (
                f"{target}: {desc}, {t:.1f}°C (feels like {fl:.1f}°C), "
                f"humidity {hum}%"
            )
        return f"Could not get weather for '{target}': {data.get('message', 'unknown error')}"
    except Exception as e:
        return f"Weather lookup failed: {e}"


# --- Claude tool definitions ---

TOOLS = [
    {
        "name": "run_shell_command",
        "description": (
            "Run a Windows shell command (cmd.exe). Use for file operations, "
            "system info, running scripts, checking processes, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The Windows shell command to execute.",
                }
            },
            "required": ["command"],
        },
    },
    {
        "name": "search_web",
        "description": (
            "Search the web by opening a browser window. "
            "Use when the user wants to look something up online."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "open_application",
        "description": (
            "Open an application, file, or URL on Windows. "
            "Examples: 'notepad', 'calc', 'https://youtube.com', 'C:/path/to/file.pdf'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "App name, file path, or URL to open.",
                }
            },
            "required": ["target"],
        },
    },
    {
        "name": "get_weather",
        "description": (
            "Get current weather for a city. "
            "If no city is given, uses the default city."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name. Leave blank for the default city.",
                }
            },
            "required": [],
        },
    },
]

TOOL_MAP = {
    "run_shell_command": lambda inp: run_shell_command(inp["command"]),
    "search_web": lambda inp: search_web(inp["query"]),
    "open_application": lambda inp: open_application(inp["target"]),
    "get_weather": lambda inp: get_weather(inp.get("city", "")),
}

SYSTEM_PROMPT = (
    "You are Jarvis, a sharp and capable AI assistant running on Windows. "
    "You have tools to run shell commands, search the web, open apps or files, "
    "and check the weather. "
    "Be concise — one or two sentences unless the user asks for more detail. "
    "When you use a tool, briefly say what you're about to do."
)


def chat(user_message: str, history: list) -> str:
    history.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=history,
        )

        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return " ".join(
                b.text for b in response.content if hasattr(b, "text")
            )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    fn = TOOL_MAP.get(block.name)
                    if fn is None:
                        result = f"Unknown tool: {block.name}"
                    else:
                        print(f"  → {block.name}({json.dumps(block.input, ensure_ascii=False)})")
                        result = fn(block.input)
                        preview = result[:120] + ("…" if len(result) > 120 else "")
                        print(f"  ← {preview}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            history.append({"role": "user", "content": tool_results})
        else:
            # Unexpected stop — return whatever text we have
            return " ".join(
                b.text for b in response.content if hasattr(b, "text")
            ) or "(no response)"


def main() -> None:
    print("=" * 52)
    print("  J A R V I S  —  AI Assistant")
    print("=" * 52)
    print(f"  Voice input : {'[OK] ready' if VOICE_AVAILABLE else '[--] install SpeechRecognition + PyAudio'}")
    print(f"  Speech out  : {'[OK] ready' if TTS_AVAILABLE else '[--] install pyttsx3'}")
    print(f"  Default city: {DEFAULT_CITY}")
    print()
    print("  Commands: 'voice' — switch to voice input")
    print("            'clear' — reset conversation")
    print("            'quit'  — exit")
    print("=" * 52)

    history: list = []
    voice_mode = False

    speak("Hello! I'm Jarvis. What can I do for you?")

    while True:
        try:
            if voice_mode and VOICE_AVAILABLE:
                print("\n[Voice mode — say 'text mode' to switch back]")
                user_input = listen()
                if not user_input:
                    continue
                if "text mode" in user_input.lower():
                    voice_mode = False
                    speak("Switched to text mode.")
                    continue
            else:
                user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            low = user_input.lower()

            if low in ("quit", "exit", "bye", "goodbye"):
                speak("Goodbye! Have a great day.")
                break

            if low == "voice":
                if VOICE_AVAILABLE:
                    voice_mode = True
                    speak("Switched to voice mode.")
                else:
                    print("Voice not available — install SpeechRecognition and PyAudio.")
                continue

            if low == "clear":
                history.clear()
                print("Conversation cleared.")
                continue

            reply = chat(user_input, history)
            speak(reply)

        except KeyboardInterrupt:
            speak("Goodbye!")
            sys.exit(0)
        except anthropic.AuthenticationError:
            print("\nError: Invalid ANTHROPIC_API_KEY. Check your environment variable.")
            sys.exit(1)
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
