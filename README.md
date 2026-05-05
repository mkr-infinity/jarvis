# J.A.R.V.I.S Desktop AI Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge&labelColor=0d1117&color=00ffff">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge&labelColor=0d1117&color=00ff88">
  <img src="https://img.shields.io/badge/Electron-41.5.0-blue?style=for-the-badge&labelColor=0d1117&color=00aaff">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&labelColor=0d1117&color=ffaa00">
</p>

<p align="center">
  <strong>Your Personal Iron-Man Style AI Assistant</strong><br>
  Built with Electron + FastAPI | Voice Enabled | Offline-First
</p>

---

##

<p align="center">
  <img src="https://raw.githubusercontent.com/mkr-infinity/jarvis/refs/heads/main/renderer/assets/jarvis-logo.svg" width="120" alt="J.A.R.V.I.S Logo">
</p>

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| **Iron-Man JARVIS UI** | Beautiful arc reactor inspired HUD with animated orb states (idle, listening, thinking, speaking) |
| **Voice Input** | Click the mic button and speak - automatically sends your message |
| **Voice Output (TTS)** | JARVIS speaks responses aloud like a real AI assistant |
| **Offline-First AI** | Uses local Ollama by default - works without internet |
| **Cloud AI Support** | Optional OpenAI, Anthropic, Gemini, Groq API keys |
| **Chat History** | Projects and sessions with SQLite memory |
| **Desktop Integration** | Native window, system tray, saved window position |
| **System Commands** | Open apps, URLs, control media, screenshots, and more |

---

## 📋 Requirements

### Minimum Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| **Node.js** | 18+ | LTS recommended |
| **Python** | 3.10+ | 3.11+ recommended |
| **Ollama** | Latest | For local AI (optional) |

### For Local AI (Recommended)

```bash
# Pull a model
ollama pull llama3.1
```

Or other recommended models:
- `ollama pull mistral`
- `ollama pull codellama`
- `ollama pull phi3`

---

## 🖥️ Supported Platforms

- ✅ **Debian 13** (Tested & Recommended)
- ✅ **Ubuntu 22.04+**
- ✅ **Windows 10/11**
- ✅ **macOS 12+**

---

## 🔧 Setup Guide

### Debian / Ubuntu / Linux Mint

```bash
# 1. Clone or download the project
cd ~/Downloads/Projects/jarvis

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Install Node.js dependencies
npm install

# 6. Start the application
npm start
```

### Windows

```powershell
# 1. Navigate to project directory
cd C:\Path\To\jarvis

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
.venv\Scripts\Activate.ps1

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Install Node.js dependencies
npm install

# 6. Start the application
npm start
```

### macOS

```bash
# 1. Navigate to project directory
cd ~/Downloads/Projects/jarvis

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Install Node.js dependencies
npm install

# 6. Start the application
npm start
```

---

## 🎮 How to Use

### Quick Start

1. **Run** `npm start`
2. **Onboarding** will appear first time - select your AI provider
3. **For Ollama**: Leave as default, no API key needed
4. **For Cloud AI**: Select provider and enter API key
5. Click **ACTIVATE** or **SKIP**

### Talking to JARVIS

**Method 1 - Text**
1. Type your message in the input box
2. Press **Enter** or click the send button

**Method 2 - Voice**
1. Click the **microphone button** 🎤
2. Speak your message
3. Wait for speech recognition to finish
4. Your message is automatically sent

### Voice Output

JARVIS will **speak responses aloud** when receiving AI replies. You can disable this in Settings.

### Settings

Click the **gear icon** ⚙️ to access:
- **General**: Language, Wake Mode
- **AI Core**: Provider, Model, API Keys
- **Voice**: Voice selection for TTS
- **About**: Version info

### New Session

Click **+ NEW SESSION** to start a fresh chat thread.

### Projects

Create projects to organize different conversation topics using the **+** button.

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `Shift + Enter` | New line in message |
| `Escape` | Close any modal/panel |
| `Ctrl + J` | Focus message input |

---

## 🤖 AI Providers

### Ollama (Recommended - Free & Offline)

1. Install [Ollama](https://ollama.ai)
2. Run: `ollama pull llama3.1`
3. Select "Ollama" in onboarding
4. No API key needed

### OpenAI

1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Select "OpenAI" in Settings
3. Enter your API key
4. Default model: gpt-4o-mini

### Anthropic Claude

1. Get API key from [Anthropic Console](https://console.anthropic.com)
2. Select "Anthropic" in Settings
3. Enter your API key
4. Default model: claude-3-haiku-20240307

### Google Gemini

1. Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Select "Gemini" in Settings
3. Enter your API key
4. Default model: gemini-1.5-flash

### Groq

1. Get API key from [Groq Console](https://console.groq.com)
2. Select "Groq" in Settings
3. Enter your API key
4. Default model: llama-3.1-8b-instant

---

## 🔧 Available Commands

### Direct JSON Commands

```json
{
  "action": "open_url",
  "params": { "url": "https://github.com" }
}
```

### Supported Actions

| Action | Description | Example |
|--------|-------------|---------|
| `open_url` | Open URL in browser | `{"action":"open_url","params":{"url":"https://github.com"}}` |
| `open_app` | Open application | `{"action":"open_app","params":{"name":"notepad"}}` |
| `close_app` | Close application | `{"action":"close_app","params":{"name":"notepad"}}` |
| `search_youtube` | Search YouTube | `{"action":"search_youtube","params":{"query":"JARVIS tutorial"}}` |
| `volume_control` | Control volume | `{"action":"volume_control","params":{"level":75}}` |
| `take_screenshot` | Take screenshot | `{"action":"take_screenshot"}` |
| `clipboard` | Clipboard ops | `{"action":"clipboard","params":{"op":"copy","text":"Hello"}}` |

**Note**: Dangerous commands require confirmation before execution.

---

## 📁 Project Structure

```
jarvis/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── core/            # Configuration
│   │   └── services/        # AI, Database, Commands, Speech
│   └── requirements.txt     # Python dependencies
├── electron/
│   ├── main.js            # Electron main process
│   ├── preload.js         # Preload bridge
│   └── window-state.json   # Saved window position
├── renderer/
│   ├── index.html        # Main UI
│   ├── styles/app.css   # JARVIS theme CSS
│   ├── scripts/app.js  # Frontend JavaScript
│   └── assets/      # Logo, icons
├── plugins/          # JSON plugins
├── data/             # SQLite database (runtime)
├── scripts/          # Helper scripts
├── package.json    # Node configuration
└── README.md      # This file
```

---

## 🏃 Quick Start (According to README)

### Step 1: Kill any existing process on port 8765

```bash
fuser -k 8765/tcp 2>/dev/null || pkill -f uvicorn 2>/dev/null || true
```

### Step 2: Start backend (keeps running)

```bash
# Terminal 1 - Keep this running
npm run backend
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8765
```

### Step 3: Start GUI

```bash
# Terminal 2 - Opens the JARVIS window
npm start
```

### Or use both in one command (recommended for testing):

```bash
# Start backend in background, then launch GUI
npm run backend &
sleep 3
npm start
```

### Or use run.sh script:

```bash
bash scripts/run.sh
```

---

## 🛠️ Troubleshooting

### Port 8765 Already in Use

```bash
# Kill the process
fuser -k 8765/tcp

# Or
pkill -f uvicorn
```

### Ollama Not Running

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# In another terminal, pull a model
ollama pull llama3.1
```

### Voice Not Working

- Check browser permissions for microphone access
- Use Chrome or Edge for best voice support
- Ensure microphone is not muted

### GUI Not Launching

- Ensure you have a display (X11/Wayland)
- On headless servers, use SSH with X11 forwarding or VNC

---

## 💬 Support

| Channel | Link |
|---------|------|
| **GitHub Issues** | https://github.com/mkr-infinity/jarvis/issues |
| **Donate** | https://buymeacoffee.com/mkr_infinity |
| **Website** | https://mkr-infinity.github.io/ |

---

## 📄 License

**MIT License** - See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>J.A.R.V.I.S</strong><br>
  <em>Your Personal AI Assistant</em>
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/mkr-infinity">Mohammad Kaif Raja</a>
</p>