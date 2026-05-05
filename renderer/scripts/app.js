(function() {
  'use strict';

  var state = {
    ws: null, settings: {}, projects: [], chats: [], messages: [],
    currentProjectId: null, currentChatId: null, assistantBuffer: '',
    reconnectTimer: null, isStreaming: false, recognition: null,
    connected: false, voiceMode: false
  };

  var els = {};

  function init() {
    try {
      console.log('JARVIS: Starting...');
      cacheElements();
      loadSettings();
      bindEvents();
      initSpeech();
      connect();
      startClock();
      showToast('JARVIS ready');
    } catch (e) { showError('Init error: ' + e.message); }
  }

  function $(id) { return document.getElementById(id); }

  function cacheElements() {
  var ids = [
    'connectionStatus','projectList','chatList','messages','messageInput',
    'micBtn','sendBtn','newChatBtn','newProjectBtn','settingsBtn',
    'onboardingPanel','settingsPanel','skipOnboardingBtn','finishOnboardingBtn',
    'onboardingApiKey','apiKeyField','onboardingError','providerSetting',
    'openaiKeySetting','anthropicKeySetting','geminiKeySetting','groqKeySetting',
    'voiceSetting','closeSettingsBtn','saveSettingsBtn','coreStatus','systemInfo',
    'currentTime','aiProvider','toast','statusText','chatMode','voiceMode',
    'voiceStatus','voiceCutBtn','modelStatus','modelStatusField'
  ];
    ids.forEach(function(id) { els[id] = $(id); });
  }

  function loadSettings() {
    try {
      var saved = localStorage.getItem('jarvis_settings');
      if (saved) {
        Object.assign(state.settings, JSON.parse(saved));
        console.log('Loaded settings from localStorage');
      }
    } catch (e) {}
  }

  function saveSettingsToStorage() {
    try {
      localStorage.setItem('jarvis_settings', JSON.stringify(state.settings));
    } catch (e) {}
  }

  function bindEvents() {
    if (els.sendBtn) els.sendBtn.onclick = function() { sendMessage(); };
    if (els.messageInput) {
      els.messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') sendMessage();
      });
    }
    if (els.newChatBtn) els.newChatBtn.onclick = function() {
      send('create_chat', { projectId: state.currentProjectId, title: 'New Session' });
    };
    if (els.newProjectBtn) els.newProjectBtn.onclick = function() {
      var name = prompt('Project name:');
      if (name && name.trim()) send('create_project', { name: name.trim() });
    };
    if (els.settingsBtn) els.settingsBtn.onclick = function() {
      els.settingsPanel.hidden = false;
    };
    if (els.closeSettingsBtn) els.closeSettingsBtn.onclick = function() {
      els.settingsPanel.hidden = true;
    };
    if (els.saveSettingsBtn) els.saveSettingsBtn.onclick = function() {
      saveSettings();
    };
    if (els.skipOnboardingBtn) els.skipOnboardingBtn.onclick = function() {
      completeOnboarding(true);
    };
    if (els.finishOnboardingBtn) els.finishOnboardingBtn.onclick = function() {
      completeOnboarding(false);
    };

    document.querySelectorAll('[data-provider]').forEach(function(btn) {
      btn.onclick = function() { selectProvider(this.dataset.provider); };
    });

    document.querySelectorAll('.modal-tabs .tab').forEach(function(tab) {
      tab.onclick = function() {
        var name = this.dataset.tab;
        document.querySelectorAll('.modal-tabs .tab').forEach(function(t) {
          t.classList.toggle('active', t === this);
        }.bind(this));
        document.querySelectorAll('.tab-content').forEach(function(p) {
          p.classList.toggle('active', p.dataset.page === name);
        }.bind(this));
      };
    });

    if (els.micBtn) els.micBtn.onclick = function() {
      if (state.voiceMode) stopVoiceMode();
      else startVoiceMode();
    };
    if (els.voiceCutBtn) els.voiceCutBtn.onclick = function() { stopVoiceMode(); };

    document.onkeydown = function(e) {
      if (e.key === 'Escape') {
        els.onboardingPanel.hidden = true;
        els.settingsPanel.hidden = true;
        stopVoiceMode();
      }
    };
  }

  function selectProvider(provider) {
    document.querySelectorAll('[data-provider]').forEach(function(btn) {
      btn.classList.toggle('active', btn.dataset.provider === provider);
    });
    if (els.apiKeyField) els.apiKeyField.hidden = provider === 'ollama';
  }

  function startVoiceMode() {
    console.log('Activating voice mode...');

    if (!state.recognition) {
      showError('Voice not supported in this browser');
      return;
    }

    if (state.voiceMode) {
      console.log('Voice already active');
      return;
    }

    state.voiceMode = true;

    if (els.chatMode) els.chatMode.style.display = 'none';
    if (els.voiceMode) els.voiceMode.style.display = 'flex';
    if (els.voiceStatus) els.voiceStatus.textContent = 'Listening...';

    try {
      state.recognition.start();
      console.log('Recognition started');
    } catch (e) {
      console.error('Start error:', e);
      showError('Allow microphone access');
      state.voiceMode = false;
    }
  }

  function stopVoiceMode() {
    console.log('Deactivating voice mode...');
    state.voiceMode = false;

    if (state.recognition) {
      try { state.recognition.stop(); } catch (e) {}
    }

    if (els.voiceMode) els.voiceMode.style.display = 'none';
    if (els.chatMode) els.chatMode.style.display = 'flex';
    if (els.voiceStatus) els.voiceStatus.textContent = '';
    if (els.micBtn) els.micBtn.classList.remove('active');
  }

  function processVoiceCommand(text) {
    text = text.toLowerCase().trim();
    var cmd = text.split(' ')[0];
    var arg = text.split(' ').slice(1).join(' ');

    if (cmd === 'search' || cmd === 'find') {
      executeCommand('search_youtube', { query: arg || text });
    } else if (cmd === 'open') {
      executeCommand('open_url', { url: arg });
    } else if (cmd === 'close') {
      executeCommand('close_app', { name: arg });
    } else if (cmd === 'screenshot') {
      executeCommand('take_screenshot', {});
    } else if (cmd === 'volume') {
      var level = parseInt(arg) || 50;
      executeCommand('volume_control', { level: level });
    } else if (cmd === 'stop' || cmd === 'exit' || cmd === 'cancel') {
      stopVoiceMode();
      showToast('Voice mode ended');
    } else {
      sendMessage(text);
      setTimeout(function() { stopVoiceMode(); }, 1000);
    }
  }

  function executeCommand(action, params) {
    var cmd = { action: action, params: params };
    console.log('Executing:', cmd);
    if (action === 'open_url') {
      send('user_message', {
        projectId: state.currentProjectId,
        chatId: state.currentChatId,
        text: 'Open ' + params.url
      });
    }
    showToast('Command: ' + action);
  }

  function showToast(msg, type) {
    if (!els.toast) return;
    els.toast.textContent = msg;
    els.toast.className = 'toast show';
    if (type) els.toast.classList.add(type);
    setTimeout(function() { els.toast.classList.remove('show'); }, 4000);
  }

  function showError(msg) {
    console.error(msg);
    showToast(msg, 'error');
  }

  function showSuccess(msg) {
    showToast(msg, 'success');
  }

  function connect() {
    var wsUrl = 'ws://127.0.0.1:8765/ws';
    try {
      state.ws = new WebSocket(wsUrl);
    } catch (e) {
      showError('Cannot connect to backend');
      return;
    }

    state.ws.onopen = function() {
      state.connected = true;
      if (els.connectionStatus) els.connectionStatus.textContent = 'SYSTEM ONLINE';
      if (els.coreStatus) els.coreStatus.textContent = 'NOMINAL';
      if (els.systemInfo) els.systemInfo.textContent = 'READY';
      if (els.statusText) els.statusText.textContent = 'Online. Ready.';
      showToast('Connected to JARVIS');
    };

    state.ws.onmessage = function(e) {
      try {
        var m = JSON.parse(e.data);
        handleMessage(m.type, m.payload || {});
      } catch (err) {}
    };

    state.ws.onclose = function() {
      state.connected = false;
      if (els.connectionStatus) els.connectionStatus.textContent = 'DISCONNECTED';
      reconnect();
    };

    state.ws.onerror = function() { showError('Connection error'); };
  }

  function reconnect() {
    if (state.reconnectTimer) clearTimeout(state.reconnectTimer);
    state.reconnectTimer = setTimeout(function() {
      if (!state.connected) connect();
    }, 3000);
  }

  function handleMessage(type, payload) {
    switch (type) {
      case 'bootstrap': loadBootstrap(payload); break;
      case 'project_created':
        state.projects.unshift(payload.project);
        state.chats = [payload.chat];
        state.messages = [];
        state.currentProjectId = payload.project.id;
        state.currentChatId = payload.chat.id;
        renderAll();
        showSuccess('New project created');
        break;
      case 'chat_created':
        state.chats.unshift(payload);
        state.currentChatId = payload.id;
        state.messages = [];
        renderAll();
        break;
      case 'chat_loaded':
        state.currentProjectId = payload.projectId;
        state.currentChatId = payload.chatId;
        state.chats = payload.chats || [];
        state.messages = payload.messages || [];
        renderAll();
        break;
      case 'settings':
        state.settings = Object.assign(state.settings, payload);
        applySettings();
        saveSettingsToStorage();
        break;
      case 'assistant_start': startStream(); break;
      case 'assistant_token': addToken(payload.token || ''); break;
      case 'assistant_end': endStream(payload); break;
      case 'message_saved':
        state.chats = payload.chats || state.chats;
        state.messages = payload.messages || state.messages;
        renderAll();
        break;
      case 'models_detected':
        handleModelsDetected(payload);
        break;
      case 'error': showError(payload.message || 'Error'); break;
    }
  }

  function loadBootstrap(payload) {
    if (payload.settings) {
      state.settings = Object.assign({}, state.settings, payload.settings);
      console.log('Bootstrap settings:', state.settings);
    }
    state.projects = payload.projects || [];
    state.chats = payload.chats || [];
    state.messages = payload.messages || [];
    state.currentProjectId = payload.currentProjectId;
    state.currentChatId = payload.currentChatId;
    applySettings();
    renderAll();

    if (state.settings.onboarding_completed !== 'true') {
      if (els.onboardingPanel) els.onboardingPanel.hidden = false;
    }
  }

  function applySettings() {
    var p = state.settings.provider || 'ollama';
    if (els.providerSetting) els.providerSetting.value = p;
    if (els.aiProvider) {
      var model = state.settings.model || '';
      var label = p === 'ollama' ? 'LOCAL' : p.toUpperCase();
      els.aiProvider.textContent = model ? label + ' (' + model.split('-').slice(-2).join('-') + ')' : label;
    }
    if (els.voiceSetting) els.voiceSetting.value = state.settings.voice || 'en-US-GuyNeural';

    if (els.openaiKeySetting) els.openaiKeySetting.value = state.settings.openai_key || '';
    if (els.anthropicKeySetting) els.anthropicKeySetting.value = state.settings.anthropic_key || '';
    if (els.geminiKeySetting) els.geminiKeySetting.value = state.settings.gemini_key || '';
    if (els.groqKeySetting) els.groqKeySetting.value = state.settings.groq_key || '';
  }

  function renderAll() { renderProjects(); renderChats(); renderMessages(); }

  function renderProjects() {
    if (!els.projectList) return;
    els.projectList.innerHTML = '';
    state.projects.forEach(function(p) {
      var b = document.createElement('button');
      b.textContent = p.name;
      b.className = p.id === state.currentProjectId ? 'active' : '';
      b.onclick = function() { send('load_project', { projectId: p.id }); };
      els.projectList.appendChild(b);
    });
  }

  function renderChats() {
    if (!els.chatList) return;
    els.chatList.innerHTML = '';
    state.chats.slice(0, 50).forEach(function(c) {
      var b = document.createElement('button');
      b.textContent = c.title || 'Session';
      b.className = c.id === state.currentChatId ? 'active' : '';
      b.onclick = function() { send('load_chat', { projectId: c.project_id, chatId: c.id }); };
      els.chatList.appendChild(b);
    });
  }

  function renderMessages() {
    if (!els.messages) return;
    els.messages.innerHTML = '';
    state.messages.slice(-50).forEach(function(m) {
      var d = document.createElement('div');
      d.className = 'message ' + m.role;
      d.innerHTML = m.content
        ? m.content.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>')
        : '';
      els.messages.appendChild(d);
    });
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  function sendMessage(text) {
    var input = text || (els.messageInput ? els.messageInput.value.trim() : '');
    if (!input || state.isStreaming) return;
    if (!text && els.messageInput) els.messageInput.value = '';
    state.messages.push({ role: 'user', content: input });
    renderMessages();
    send('user_message', {
      projectId: state.currentProjectId,
      chatId: state.currentChatId,
      text: input
    });
  }

  function startStream() {
    state.isStreaming = true;
    state.assistantBuffer = '';
    if (els.statusText) els.statusText.textContent = 'Processing...';
    var d = document.createElement('div');
    d.className = 'message assistant';
    d.textContent = 'Processing...';
    d.dataset.streaming = 'true';
    els.messages.appendChild(d);
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  function addToken(t) {
    state.assistantBuffer += t;
    var s = els.messages ? els.messages.querySelector('[data-streaming="true"]') : null;
    if (s) s.innerHTML = state.assistantBuffer.replace(/\n/g, '<br>');
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  function endStream(payload) {
    state.isStreaming = false;
    if (els.statusText) els.statusText.textContent = 'Online. Ready.';
    state.chats = payload.chats || state.chats;
    state.messages = payload.messages || state.messages;
    renderAll();
    speakResponse();
  }

  function speakResponse() {
    if (!window.speechSynthesis) return;
    var last = state.messages[state.messages.length - 1];
    if (!last || last.role !== 'assistant') return;
    var text = last.content.substring(0, 500);
    var utt = new SpeechSynthesisUtterance(text);
    utt.rate = 1.1;
    window.speechSynthesis.speak(utt);
  }

  function send(type, payload) {
    if (!state.ws || state.ws.readyState !== WebSocket.OPEN) return false;
    try {
      state.ws.send(JSON.stringify({ type: type, payload: payload || {} }));
      return true;
    } catch (e) { return false; }
  }

  function completeOnboarding(force) {
    var provider = force ? 'ollama' :
      (document.querySelector('[data-provider].active') || {}).dataset.provider || 'ollama';
    var key = els.onboardingApiKey ? els.onboardingApiKey.value.trim() : '';
    if (provider !== 'ollama' && !key) {
      if (els.onboardingError) els.onboardingError.textContent = 'API key required';
      return;
    }
    if (els.onboardingError) els.onboardingError.textContent = '';

    if (provider === 'ollama') {
      finishOnboarding({ provider: 'ollama', model: 'llama3.1' });
      return;
    }

    if (!key) {
      finishOnboarding({ provider: provider, model: getDefaultModel(provider) });
      return;
    }

    els.onboardingError.textContent = 'Checking API key...';
    send('detect_models', { provider: provider, api_key: key });

    state.pendingOnboarding = { provider: provider };
    var keyField = { openai: 'openai_key', anthropic: 'anthropic_key', gemini: 'gemini_key', groq: 'groq_key' };
    state.pendingOnboarding[keyField[provider]] = key;
  }

  function finishOnboarding(patch) {
    var finalPatch = Object.assign({
      language: 'auto',
      voice: 'en-US-GuyNeural',
      onboarding_completed: 'true'
    }, patch);
    send('settings_update', finalPatch);
    els.onboardingPanel.hidden = true;
    showSuccess('JARVIS activated with ' + finalPatch.provider.toUpperCase());
    applySettings();
  }

  function saveSettings() {
    var p = els.providerSetting ? els.providerSetting.value : 'ollama';
    var ok = els.openaiKeySetting ? els.openaiKeySetting.value.trim() : '';
    var ak = els.anthropicKeySetting ? els.anthropicKeySetting.value.trim() : '';
    var gk = els.geminiKeySetting ? els.geminiKeySetting.value.trim() : '';
    var rk = els.groqKeySetting ? els.groqKeySetting.value.trim() : '';
    var voice = els.voiceSetting ? els.voiceSetting.value : 'en-US-GuyNeural';

    var patch = {
      provider: p,
      language: 'auto',
      voice: voice,
      openai_key: ok,
      anthropic_key: ak,
      gemini_key: gk,
      groq_key: rk,
      onboarding_completed: 'true'
    };

    if (p === 'ollama') {
      patch.model = 'llama3.1';
      commitSettings(patch);
      return;
    }

    var keyMap = { openai: ok, anthropic: ak, gemini: gk, groq: rk };
    var apiKey = keyMap[p] || '';

    if (!apiKey) {
      patch.model = getDefaultModel(p);
      commitSettings(patch);
      return;
    }

    showModelStatus('checking', 'Checking API key and detecting models...');

    var detectPayload = { provider: p, api_key: apiKey };
    send('detect_models', detectPayload);

    state.pendingSettings = patch;
  }

  function getDefaultModel(provider) {
    var defaults = {
      openai: 'gpt-4o-mini',
      anthropic: 'claude-3-haiku-20240307',
      gemini: 'gemini-1.5-flash',
      groq: 'llama-3.1-8b-instant',
      ollama: 'llama3.1'
    };
    return defaults[provider] || 'gpt-4o-mini';
  }

  function showModelStatus(type, msg) {
    if (!els.modelStatusField) return;
    els.modelStatusField.hidden = false;
    if (!els.modelStatus) return;
    els.modelStatus.className = 'model-status ' + type;
    els.modelStatus.textContent = msg;
  }

  function commitSettings(patch) {
    console.log('Committing settings:', patch);
    state.settings = patch;
    saveSettingsToStorage();
    send('settings_update', patch);
    els.settingsPanel.hidden = true;
    if (els.modelStatusField) els.modelStatusField.hidden = true;
    showToast('Settings saved: ' + patch.provider.toUpperCase());
    applySettings();
  }

  function handleModelsDetected(payload) {
    if (state.pendingOnboarding) {
      if (payload.ok) {
        var models = payload.models || [];
        if (models.length > 0) {
          state.pendingOnboarding.model = models[0];
          els.onboardingError.textContent = 'Found ' + models.length + ' models. Activating...';
          setTimeout(function() { finishOnboarding(state.pendingOnboarding); }, 600);
        } else {
          els.onboardingError.textContent = 'No models available for this key. Try a different API key.';
        }
      } else {
        els.onboardingError.textContent = payload.error || 'Key validation failed.';
      }
      state.pendingOnboarding = null;
      return;
    }

    if (payload.ok) {
      var models = payload.models || [];
      if (models.length > 0) {
        var firstModel = models[0];
        state.settings.model = firstModel;
        state.pendingSettings.model = firstModel;

        var msg = 'Found ' + models.length + ' models. Using: ' + firstModel;
        showModelStatus('success', msg);

        setTimeout(function() { commitSettings(state.pendingSettings); }, 800);
      } else {
        showModelStatus('error', 'No models found for this key. The key may not have access to any models.');
      }
    } else {
      var error = payload.error || 'Unknown error';
      showModelStatus('error', error);
    }
  }

  function initSpeech() {
    console.log('Initializing speech recognition...');
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      console.log('Speech API not available');
      return;
    }
    try {
      state.recognition = new SR();
      state.recognition.continuous = false;
      state.recognition.interimResults = true;
      state.recognition.lang = 'en-US';

      state.recognition.onstart = function() {
        console.log('Speech started');
        if (els.micBtn) els.micBtn.classList.add('active');
      };

      state.recognition.onresult = function(e) {
        console.log('Speech result received');
        var result = e.results[e.results.length - 1];
        if (result.isFinal) {
          var text = result[0].transcript.trim();
          console.log('Heard:', text);
          if (text) {
            if (state.voiceMode && els.voiceStatus) {
              els.voiceStatus.textContent = 'Got: ' + text;
              processVoiceCommand(text);
            } else if (els.messageInput) {
              els.messageInput.value = text;
            }
          }
        }
      };

      state.recognition.onend = function() {
        console.log('Speech ended');
        if (els.micBtn) els.micBtn.classList.remove('active');

        if (state.voiceMode) {
          setTimeout(function() {
            stopVoiceMode();
          }, 1500);
        }
      };

      state.recognition.onerror = function(e) {
        console.log('Speech error:', e.error);
        if (e.error !== 'no-speech' && e.error !== 'aborted') {
          showError('Voice error: ' + e.error);
        }
      };

      console.log('Speech recognition ready');
    } catch (e) {
      console.log('Speech init error:', e);
    }
  }

  function startClock() {
    function update() {
      if (els.currentTime) {
        var now = new Date();
        els.currentTime.textContent = now.toLocaleTimeString('en-US', { hour12: false });
      }
    }
    update();
    setInterval(update, 1000);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
