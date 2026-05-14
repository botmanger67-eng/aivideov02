let currentJobId = null;
let pollInterval = null;

const generateBtn = document.getElementById('generateBtn');
const promptTextarea = document.getElementById('prompt');
const progressArea = document.getElementById('progressArea');
const progressBar = document.getElementById('progressBar');
const statusMsg = document.getElementById('statusMessage');
const resultArea = document.getElementById('resultArea');
const previewVideo = document.getElementById('previewVideo');
const downloadLink = document.getElementById('downloadLink');
const errorArea = document.getElementById('errorArea');
const newVideoBtn = document.getElementById('newVideoBtn');
const retryBtn = document.getElementById('retryBtn');

// Hide all result/error panels initially
function resetUI() {
    progressArea.classList.add('hidden');
    resultArea.classList.add('hidden');
    errorArea.classList.add('hidden');
    if (pollInterval) clearInterval(pollInterval);
    currentJobId = null;
}

// Start generation
generateBtn.addEventListener('click', async () => {
    const prompt = promptTextarea.value.trim();
    if (!prompt) {
        alert('Please describe what video you want.');
        return;
    }
    resetUI();
    generateBtn.disabled = true;
    generateBtn.textContent = '⏳ Generating...';
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        currentJobId = data.job_id;
        startPolling();
    } catch (err) {
        showError(err.message);
        generateBtn.disabled = false;
        generateBtn.textContent = '✨ Generate Video';
    }
});

function startPolling() {
    progressArea.classList.remove('hidden');
    pollInterval = setInterval(async () => {
        if (!currentJobId) return;
        try {
            const res = await fetch(`/api/status/${currentJobId}`);
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            
            // Update progress bar
            const progress = data.progress || 0;
            progressBar.style.width = `${progress}%`;
            statusMsg.textContent = getStatusMessage(data.status, progress);
            
            if (data.status === 'completed') {
                clearInterval(pollInterval);
                const videoPath = data.result.video_path;
                const downloadUrl = `/api/download/${currentJobId}`;
                previewVideo.src = downloadUrl;
                downloadLink.href = downloadUrl;
                resultArea.classList.remove('hidden');
                progressArea.classList.add('hidden');
                generateBtn.disabled = false;
                generateBtn.textContent = '✨ Generate Video';
                currentJobId = null;
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                showError(data.result?.error || 'Unknown failure');
                generateBtn.disabled = false;
                generateBtn.textContent = '✨ Generate Video';
            }
        } catch (err) {
            clearInterval(pollInterval);
            showError(err.message);
            generateBtn.disabled = false;
            generateBtn.textContent = '✨ Generate Video';
        }
    }, 2000);
}

function getStatusMessage(status, progress) {
    if (status === 'processing') {
        if (progress < 20) return '📝 Writing script with AI...';
        if (progress < 50) return '🎨 Fetching visuals...';
        if (progress < 80) return '🎙️ Generating voiceover...';
        return '✂️ Assembling final video...';
    }
    return 'Processing...';
}

function showError(msg) {
    errorArea.classList.remove('hidden');
    errorArea.querySelector('p').innerText = `❌ Error: ${msg}`;
    progressArea.classList.add('hidden');
    resultArea.classList.add('hidden');
    generateBtn.disabled = false;
    generateBtn.textContent = '✨ Generate Video';
}

// Reset for new video
newVideoBtn.addEventListener('click', () => {
    resetUI();
    promptTextarea.value = '';
    resultArea.classList.add('hidden');
});

retryBtn.addEventListener('click', () => {
    errorArea.classList.add('hidden');
    generateBtn.click();
});