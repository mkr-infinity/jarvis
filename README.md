<div align="center">

<img src="renderer/assets/jarvis-logo.svg" alt="J.A.R.V.I.S Logo" width="120" height="120">

# J.A.R.V.I.S - Desktop AI Assistant

[![Stars](https://img.shields.io/github/stars/mkr-infinity/jarvis?style=for-the-badge&logo=github&color=ffd700)](https://github.com/mkr-infinity/jarvis/stargazers)
[![Forks](https://img.shields.io/github/forks/mkr-infinity/jarvis?style=for-the-badge&logo=github&color=00ffff)](https://github.com/mkr-infinity/jarvis/network/members)
[![Issues](https://img.shields.io/github/issues/mkr-infinity/jarvis?style=for-the-badge&logo=github&color=ff6b6b)](https://github.com/mkr-infinity/jarvis/issues)
[![License](https://img.shields.io/github/license/mkr-infinity/jarvis?style=for-the-badge&color=4ecdc4)](https://github.com/mkr-infinity/jarvis/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green?style=for-the-badge&logo=node.js)](https://nodejs.org)
[![Electron](https://img.shields.io/badge/Electron-Desktop-47848?style=for-the-badge&logo=electron)](https://www.electronjs.org)

> Your personal AI assistant, inspired by Iron Man's J.A.R.V.I.S.

</div>

---

## Overview

J.A.R.V.I.S is a lightweight, cross-platform desktop AI assistant with voice capabilities and real-time streaming, featuring a stunning Iron Man-inspired arc reactor interface with multiple themes. Built with Electron, FastAPI, and vanilla JavaScript - no heavy frameworks, just pure performance.

## Features

| Feature | Description |
|---------|-------------|
| Arc Reactor UI | Stunning HUD interface with animated power orb |
| Real-Time Streaming | Word-by-word AI responses with typing cursor |
| Thinking States | Reactor glows orange while thinking, cyan while replying |
| Voice Mode | Click the mic for voice input with green reactor animation |
| Auto Model Detection | Automatically fetches all available models for your API key |
| Quick Model Switcher | Switch models instantly from the header AI stat |
| Multi-AI Support | Ollama (local), OpenAI, Anthropic, Gemini, Groq |
| 6 Professional Themes | JARVIS, Matrix, Sunset, Violet, Arctic, Gold |
| Text-to-Speech | JARVIS speaks responses aloud |
| Chat History | Organized projects and conversation sessions |
| API Key Validation | Checks key validity and shows clear error messages |
| Keyboard Shortcuts | Enter to send, ESC to close panels |
| System Commands | Search, open URLs, screenshots, volume control |

## Screenshots

<div align="center">
  <em>Screenshots coming soon</em>
</div>

## Requirements

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Backend API server |
| Node.js | 18+ | Electron desktop app |
| Ollama | Latest | Local AI models (optional) |
| npm | 9+ | Package management |

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mkr-infinity/jarvis.git
cd jarvis
```

### 2. Install Dependencies

**Linux/macOS:**
```bash
pip install -r requirements.txt
npm install
```

**Windows:**
```cmd
pip install -r requirements.txt
npm install
```

## Running the App

### Option 1: One-Command Start (Recommended)

**Linux/macOS:**
```bash
bash scripts/run.sh
```

**Windows:**
```cmd
scripts\run.bat
```

### Option 2: Manual Terminal Start

Open **two terminals**:

**Terminal 1 - Backend:**
```bash
npm run backend
```

**Terminal 2 - GUI:**
```bash
npm start
```

### Option 3: Development Mode

```bash
npm run dev
```

This kills any existing processes on port 8765 and restarts the backend.

## Configuration

### API Keys

1. Launch the application
2. Click the **Settings** icon
3. Enter your API key for your preferred provider:
   - **OpenAI** (GPT-4, GPT-3.5)
   - **Anthropic** (Claude)
   - **Gemini** (Google)
   - **Groq** (Fast inference)
4. JARVIS automatically validates the key and detects all available models
5. Select your preferred model from the dropdown

### Using Ollama (Free Local AI)

1. Install [Ollama](https://ollama.ai)
2. Pull a model: `ollama pull llama3.1`
3. Select "Ollama" in JARVIS settings
4. No API key required - runs 100% locally!

### Switching Models

**From Header:** Hover over the AI stat in the top bar to reveal a quick model dropdown. Click any model to switch instantly.

**From Settings:** Open Settings -> AI CORE -> Select a model from the dropdown. Click the refresh button to re-detect models.

### Themes

Open Settings -> AI CORE -> Scroll to the Theme grid. Choose from:
- **JARVIS** - Classic cyan/blue Iron Man style
- **Matrix** - Green hacker aesthetic
- **Sunset** - Warm red/orange tones
- **Violet** - Purple/magenta glow
- **Arctic** - Cool blue ice theme
- **Gold** - Warm golden accents

## Voice Commands

| Command | Action |
|---------|--------|
| `search [query]` | Search the web |
| `open [url]` | Open a URL in browser |
| `screenshot` | Capture screen |
| `volume [0-100]` | Set system volume |
| `mute` / `unmute` | Toggle audio |

Voice mode auto-retries on network errors and gracefully handles microphone issues.

## Project Structure

```
jarvis/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI server + WebSocket
│       └── services/
│           ├── ai_engine.py     # Streaming AI for all providers
│           ├── database.py      # SQLite operations
│           ├── command_engine.py # System commands
│           └── speech_engine.py # Text-to-Speech
├── electron/
│   └── main.js                  # Electron main process
├── renderer/
│   ├── index.html               # Main UI
│   ├── styles/
│   │   └── app.css              # JARVIS themes (6 total)
│   └── scripts/
│       └── app.js               # Frontend logic + voice
├── scripts/
│   ├── start.js                 # Custom launcher
│   ├── run.sh                   # Linux/Mac script
│   └── run.bat                  # Windows script
└── package.json                 # Dependencies
```

## Available NPM Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Launch Electron GUI |
| `npm run backend` | Start FastAPI backend |
| `npm run dev` | Kill port + start backend |
| `npm run kill` | Kill port 8765 |
| `npm run check:js` | Lint JavaScript |
| `npm run check:python` | Check Python syntax |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8765 in use | Run `npm run kill` or `pkill -f uvicorn` |
| Electron not launching | Requires display - won't work on headless servers |
| Ollama not working | Run `ollama pull llama3.1` |
| Buttons not working | Check browser console (Ctrl+Shift+I) for errors |
| Voice says "no internet" | Voice mode now auto-retries on network errors |
| API key not working | Check Settings for the specific error message explaining why |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <strong>Built with passion by <a href="https://github.com/mkr-infinity">mkr-infinity</a></strong>
</div>
