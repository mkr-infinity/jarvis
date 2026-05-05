const { spawn, execSync } = require('child_process');
const path = require('path');

console.log('🤖 Starting J.A.R.V.I.S...\n');

// Get project root
const projectRoot = path.join(__dirname, '..');
console.log('Project:', projectRoot);

// Kill any existing backend processes
try {
  execSync('pkill -f uvicorn', { stdio: 'ignore' });
  console.log('✅ Cleaned up old processes');
} catch(e) {
  // No processes to kill - this is fine
}

// Wait for cleanup
setTimeout(() => {
  console.log('🚀 Starting backend server...');
  
  // Start backend in background
  const backend = spawn('python', [
    '-m', 'uvicorn', 
    'backend.app.main:app', 
    '--host', '127.0.0.1', 
    '--port', '8765'
  ], {
    cwd: projectRoot,
    detached: true,
    stdio: 'ignore'
  });
  
  backend.unref();
  
  // Wait for backend to start, then launch Electron
  setTimeout(() => {
    console.log('🖥️  Launching JARVIS GUI...\n');
    
    const electron = spawn('npx', ['electron', '.'], {
      cwd: projectRoot,
      stdio: 'inherit'
    });
    
    electron.on('close', (code) => {
      console.log('\n👋 Shutting down...');
      try { execSync('pkill -f uvicorn', { stdio: 'ignore' }); } catch(e) {}
      process.exit(code || 0);
    });
    
  }, 2500); // Wait 2.5 seconds for backend
  
}, 500);