# AGENTS.md - JARVIS Development Guide

This file contains development notes and context for AI assistants working on the JARVIS project.

## Project Overview

- **Name**: J.A.R.V.I.S - Desktop AI Assistant
- **Stack**: Electron (GUI) + FastAPI (Backend) + Vanilla JavaScript
- **Database**: SQLite
- **UI Theme**: Iron-Man JARVIS style with arc reactor HUD

## Key Files

```
jarvis/
├── backend/app/main.py           # FastAPI backend - handles all API endpoints
├── backend/app/services/
│   ├── ai_engine.py           # AI providers (Ollama, OpenAI, Anthropic, Gemini, Groq)
│   ├── database.py           # SQLite database operations
│   └── command_engine.py  # System command execution
├── electron/main.js          # Electron main process
├── renderer/
│   ├── index.html          # Main UI
│   ├── styles/app.css      # JARVIS theme styling
│   └── scripts/app.js     # Frontend JavaScript
├── package.json            # npm scripts
└── scripts/
    ├── start.js          # Custom launcher
    ├── run.sh           # Linux launcher
    └── run.bat          # Windows launcher
```

## Important URL Endpoints

- `GET /health` - Health check
- `WS /ws` - WebSocket for real-time chat
- `GET /api/chat` - Chat API (if needed)

## Running the App

### Recommended:
```bash
# Terminal 1 - Start backend
npm run backend

# Terminal 2 - Start GUI
npm start
```

### Or use the script:
```bash
# Linux/Mac
bash scripts/run.sh

# Windows
scripts\run.bat
```

## Development Notes

- WebSocket runs on port 8765
- Frontend connects via `ws://127.0.0.1:8765/ws`
- Backend auto-detects Ollama models
- TTS uses Web Speech API (browser built-in)
- Voice input uses Web Speech Recognition API
- SQLite database stored in `data/` at runtime

## Common Issues

1. **Port 8765 in use**: Run `pkill -f uvicorn` or `fuser -k 8765/tcp`
2. **Electron not launching**: Need display - won't work on headless servers
3. **Ollama not working**: Install Ollama and run `ollama pull llama3.1`
4. **Buttons not working**: Check browser console for errors

## UI States

The power orb shows different states:
- `idle` - Blue glow, waiting for input
- `listening` - Green, when voice input active
- `thinking` - Orange, when AI processing
- `speaking` - Blue with waves, when TTS active

## CSS Variables (app.css)

Key colors:
- `--cyan`: #00ffff (primary)
- `--cyan-dim`: #00aaff
- `--orange`: #ffaa00 (thinking)
- `--green`: #00ff88 (listening)
- `--bg-deep`: #030608 (background)
- `--bg-panel`: #080d14 (panels)

## Key npm Scripts

- `npm start` - Launch Electron GUI (requires backend running)
- `npm run backend` - Start FastAPI backend only
- `npm run dev` - Kill port and start backend
- `npm run kill` - Kill port 8765
- `npm run check:js` - Lint JavaScript
- `npm run check:python` - Check Python syntax