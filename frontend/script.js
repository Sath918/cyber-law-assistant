// Cyber Law Assistant - Premium Frontend Logic

const API_BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.origin === "file://" 
    ? "http://127.0.0.1:5001" 
    : window.location.origin;
// Files will be uploaded and processed directly

// Shared Functions
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.style.borderLeftColor = isError ? '#ef4444' : '#fbbf24';
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Authentication Logic
if (window.location.pathname.includes('login.html')) {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        // [Existing login logic...]
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('login-error');
            const submitBtn = loginForm.querySelector('button');

            try {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Logging in...';

                const response = await fetch(`${API_BASE_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await response.json();
                if (response.ok) {
                    localStorage.setItem('user_id', data.user_id);
                    localStorage.setItem('username', data.username);
                    if (data.profile_pic) localStorage.setItem('profile_pic', data.profile_pic);
                    window.location.href = 'index.html';
                } else {
                    errorDiv.textContent = data.error || 'Login failed';
                    errorDiv.classList.remove('hidden');
                }
            } catch (err) {
                errorDiv.textContent = 'Connection error. Is the server running?';
                errorDiv.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Login';
            }
        });
    }
}

if (window.location.pathname.includes('register.html')) {
    // [Existing register logic...]
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('reg-username').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            const errorDiv = document.getElementById('register-error');
            const submitBtn = registerForm.querySelector('button');

            try {
                submitBtn.disabled = true;
                const response = await fetch(`${API_BASE_URL}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });
                const data = await response.json();
                if (response.ok) {
                    showToast('Registration successful! Please login.');
                    setTimeout(() => window.location.href = 'login.html', 1500);
                } else {
                    errorDiv.textContent = data.error || 'Registration failed';
                    errorDiv.classList.remove('hidden');
                }
            } catch (err) {
                errorDiv.textContent = 'Connection error.';
                errorDiv.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Register';
            }
        });
    }
}

// Main Chat Logic
if (window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname === '') {
    let userId = localStorage.getItem('user_id');
    if (userId === "null" || userId === "undefined") userId = null;
    
    const username = localStorage.getItem('username');
    const profilePic = localStorage.getItem('profile_pic');

    if (!userId) {
        // Unauthenticated mode: No redirect. Just set Guest profile and show Login button.
        const headerImg = document.getElementById('user-avatar-img');
        if (headerImg) {
            headerImg.src = `https://ui-avatars.com/api/?name=Guest&background=64748b&color=fff`;
        }
        
        const dropdownMenu = document.getElementById('dropdown-menu');
        if (dropdownMenu) {
            dropdownMenu.innerHTML = `<a href="login.html"><i class="fas fa-sign-in-alt"></i> Login / Register</a>`;
        }

        // Hide sidebar
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.style.display = 'none';

        // Show login prompt above input
        const loginPrompt = document.getElementById('guest-login-prompt');
        if (loginPrompt) loginPrompt.style.display = 'block';
        
        // Clear any stale local data except language preference
        const lang = localStorage.getItem('ui_lang');
        localStorage.clear();
        if (lang) localStorage.setItem('ui_lang', lang);
        
    } else {
        // Load custom profile in header if exists
        const headerImg = document.getElementById('user-avatar-img');
        if (headerImg) {
            if (profilePic && profilePic !== "null" && profilePic !== "default.png") {
                headerImg.src = `${API_BASE_URL}/uploads/profiles/${profilePic}`;
            } else {
                headerImg.src = `https://ui-avatars.com/api/?name=${username}&background=3b82f6&color=fff`;
            }
        }
    }

    // Elements
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const logoutBtn = document.getElementById('logout-btn');
    const fileUpload = document.getElementById('file-upload');
    const voiceBtn = document.getElementById('voice-btn');
    const langSelect = document.getElementById('ui-language-select');
    
    // UI Translations
    const translations = {
        en: {
            placeholder: 'Type your cyber law question...',
            thinking: '<div class="typing-indicator"><span></span><span></span><span></span></div>',
            welcome: 'Hello! How can I assist you with cyber law today? <i class="fas fa-scale-balanced" style="color:#fbbf24;"></i>',
            errorServer: 'The server encountered an issue processing your request.',
            errorNet: 'Network error. Make sure your local Python server and Ollama are properly running.',
            listening: 'Listening...',
            clearChatMsg: 'All chats cleared from UI'
        },
        ta: {
            placeholder: 'உங்கள் சைபர் சட்ட கேள்வியைத் தட்டச்சு செய்க...',
            thinking: '<div class="typing-indicator"><span></span><span></span><span></span></div>',
            welcome: 'வணக்கம்! இன்று சைபர் சட்டம் குறித்து நான் உங்களுக்கு எவ்வாறு உதவ முடியும்? <i class="fas fa-scale-balanced" style="color:#fbbf24;"></i>',
            errorServer: 'உங்கள் கோரிக்கையைச் செயலாக்குவதில் சேவையகம் சிக்கலை எதிர்கொண்டது.',
            errorNet: 'நெட்வொர்க் பிழை. உங்கள் உள்ளூர் பைதான் சர்வர் மற்றும் ஒல்லாமா இயங்குகிறதா என்பதை உறுதிப்படுத்தவும்.',
            listening: 'கவனிக்கிறது...',
            clearChatMsg: 'நீங்கள் அனைத்து அரட்டைகளையும் நீக்கிவிட்டீர்கள்'
        },
        tg: {
            placeholder: 'Unga cyber law kelviya type pannunga...',
            thinking: '<div class="typing-indicator"><span></span><span></span><span></span></div>',
            welcome: 'Vanakkam! Inniku cyber law pathi naan eppadi help panna mudiyum? <i class="fas fa-scale-balanced" style="color:#fbbf24;"></i>',
            errorServer: 'Server-la oru prechana.',
            errorNet: 'Network error. Python server/Ollama run aagutha nu check pannunga.',
            listening: 'Kekkuthu...',
            clearChatMsg: 'Chat list clear panniyachu'
        }
    };

    let currentLang = langSelect ? langSelect.value : 'en';

    if (langSelect) {
        // Restore saved preference
        const savedLang = localStorage.getItem('ui_lang') || 'en';
        langSelect.value = savedLang;
        currentLang = savedLang;
        updateUITexts(currentLang);

        langSelect.addEventListener('change', (e) => {
            currentLang = e.target.value;
            localStorage.setItem('ui_lang', currentLang);
            updateUITexts(currentLang);
        });
    }

    function updateUITexts(lang) {
        const tr = translations[lang];
        if(messageInput) messageInput.placeholder = tr.placeholder;
        // Welcome message update if it's currently on screen? We can handle it on 'new-chat'
    }
    
    // File Preview Elements
    const attachmentPreview = document.getElementById('attachment-preview');
    const userProfile = document.getElementById('user-info');
    const dropdownMenu = document.getElementById('dropdown-menu');

    // Toggle dropdown on click
    if (userProfile && dropdownMenu) {
        userProfile.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });
        
        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!userProfile.contains(e.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
    }

    // Logout
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            const lang = localStorage.getItem('ui_lang');
            localStorage.clear();
            if (lang) localStorage.setItem('ui_lang', lang);
            window.location.href = 'login.html';
        });
    }

    // Enter to send
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSend();
        }
    });

    sendBtn.addEventListener('click', handleSend);

    let currentSessionId = localStorage.getItem('current_session_id') || Date.now().toString();

    // Chat History Load
    async function loadSessions() {
        if (!userId) return; // Unauthenticated users don't have saved history
        
        try {
            const response = await fetch(`${API_BASE_URL}/sessions?user_id=${userId}`);
            const data = await response.json();
            
            if (response.ok) {
                const historyList = document.getElementById('chat-history-list');
                if (historyList) historyList.innerHTML = '';
                
                if (data.sessions.length > 0) {
                    let sessionFound = false;
                    data.sessions.forEach((session, index) => {
                        const isActive = session.session_id === currentSessionId;
                        if (isActive) sessionFound = true;
                        addSessionToSidebar(session.session_id, session.first_message, isActive);
                    });
                    
                    // If currentSessionId isn't in history, defaults to the latest or stays new
                    if (!sessionFound && data.sessions.length > 0) {
                        currentSessionId = data.sessions[0].session_id;
                        localStorage.setItem('current_session_id', currentSessionId);
                        // Make it active in sidebar visually
                        const firstItem = historyList.querySelector('.history-item');
                        if (firstItem) firstItem.classList.add('active');
                    }
                    
                    loadSessionChat(currentSessionId);
                } else {
                    currentSessionId = Date.now().toString();
                    localStorage.setItem('current_session_id', currentSessionId);
                }
            }
        } catch (err) {
            console.error("Failed to load sessions:", err);
        }
    }

    async function loadSessionChat(sessionId) {
        if (!userId) return;
        chatMessages.innerHTML = ''; // Clear current messages
        
        try {
            const response = await fetch(`${API_BASE_URL}/history?user_id=${userId}&session_id=${sessionId}`);
            const data = await response.json();
            
            if (response.ok && data.history.length > 0) {
                data.history.forEach((chat) => {
                    const uDiv = appendMessage('user', chat.message, false);
                    if (chat.response) {
                        appendMessage('bot', chat.response, false);
                    }
                });
                scrollToBottom();
            } else {
                appendMessage('bot', translations[currentLang].welcome);
            }
        } catch(err) {
            console.error(err);
        }
    }

    function addSessionToSidebar(sessionId, text, active=false) {
        const historyList = document.getElementById('chat-history-list');
        if (!historyList) return;
        
        // Don't add if it already exists
        const existing = historyList.querySelector(`[data-session-id="${sessionId}"]`);
        if (existing) return;
        
        const li = document.createElement('li');
        li.className = 'history-item' + (active ? ' active' : '');
        li.dataset.sessionId = sessionId;
        
        li.innerHTML = `
            <div class="history-item-content">
                <div class="chat-dot"></div>
                <span>${text.substring(0, 20)}${text.length > 20 ? '...' : ''}</span>
            </div>
            <div class="history-item-actions">
                <button class="delete-history-btn" title="Delete Chat"><i class="fas fa-trash"></i></button>
            </div>
        `;
        
        // Setup click handler to load session
        li.addEventListener('click', () => {
             document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
             li.classList.add('active');
             currentSessionId = sessionId;
             localStorage.setItem('current_session_id', currentSessionId);
             loadSessionChat(currentSessionId);
             
             // On mobile, maybe hide sidebar after selection
             if (window.innerWidth <= 768) {
                 const sidebar = document.getElementById('sidebar');
                 if(sidebar) sidebar.classList.remove('open');
             }
        });

        // Setup delete handler
        const deleteBtn = li.querySelector('.delete-history-btn');
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm('Delete this chat session?')) {
                try {
                    const response = await fetch(`${API_BASE_URL}/history/${sessionId}?user_id=${userId}`, { method: 'DELETE' });
                    if (response.ok) {
                        li.remove();
                        if (currentSessionId === sessionId) {
                            chatMessages.innerHTML = '';
                            currentSessionId = Date.now().toString();
                            localStorage.setItem('current_session_id', currentSessionId);
                            appendMessage('bot', translations[currentLang].welcome);
                        }
                        showToast('Session deleted');
                    }
                } catch (err) {
                    showToast('Failed to delete session', true);
                }
            }
        });
        
        historyList.prepend(li);
    }

    function formatBytes(bytes, decimals = 2) {
        if (!+bytes) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
    }

    // Append Message to UI
    function postProcessMarkdown(elem) {
        if (!elem) return;
        const bqs = elem.querySelectorAll('blockquote');
        bqs.forEach(bq => {
            let html = bq.innerHTML;
            const p = bq.querySelector('p');
            if (p) html = p.innerHTML;
            
            if (html.includes('[!NOTE]')) {
                bq.className = 'callout callout-note';
                bq.innerHTML = html.replace('[!NOTE]', '<strong style="color: #60a5fa;"><i class="fas fa-info-circle"></i> Note</strong><br>');
            } else if (html.includes('[!TIP]')) {
                bq.className = 'callout callout-tip';
                bq.innerHTML = html.replace('[!TIP]', '<strong style="color: #34d399;"><i class="fas fa-lightbulb"></i> Tip</strong><br>');
            } else if (html.includes('[!WARNING]')) {
                bq.className = 'callout callout-warning';
                bq.innerHTML = html.replace('[!WARNING]', '<strong style="color: #fbbf24;"><i class="fas fa-exclamation-triangle"></i> Warning</strong><br>');
            } else if (html.includes('[!IMPORTANT]')) {
                bq.className = 'callout callout-warning';
                bq.innerHTML = html.replace('[!IMPORTANT]', '<strong style="color: #f59e0b;"><i class="fas fa-circle-exclamation"></i> Important</strong><br>');
            } else if (html.includes('[!CAUTION]')) {
                bq.className = 'callout callout-danger';
                bq.innerHTML = html.replace('[!CAUTION]', '<strong style="color: #f87171;"><i class="fas fa-radiation"></i> Caution</strong><br>');
            }
        });
    }

    // Append Message to UI
    function appendMessage(role, content, animate = true) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        if (role === 'user') {
            const userMsgCount = chatMessages.querySelectorAll('.message.user').length;
            msgDiv.dataset.index = userMsgCount;
        }
        
        const avatarClass = role === 'user' ? 'user-avatar' : 'bot-avatar';
        let loadedPicHtml = '';
        if (role === 'user') {
            const userId = localStorage.getItem('user_id');
            const storedPic = localStorage.getItem('profile_pic');
            const uName = localStorage.getItem('username') || 'Guest';
            
            if (userId && storedPic && storedPic !== "null" && storedPic !== "default.png") {
                loadedPicHtml = `<img src="${API_BASE_URL}/uploads/profiles/${storedPic}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">`;
            } else {
                const bgColor = userId ? "3b82f6" : "64748b";
                loadedPicHtml = `<img src="https://ui-avatars.com/api/?name=${uName}&background=${bgColor}&color=fff" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">`;
            }
        }
        
        const avatarIcon = role === 'user' ? loadedPicHtml : '<i class="fas fa-robot text-white"></i>';
        
        let actionsHtml = '';
        if (role === 'bot') {
            actionsHtml = `
            <div class="message-actions">
                <button class="copy-btn" title="Copy"><i class="far fa-copy"></i></button>
                <button class="share-btn" title="Share"><i class="fas fa-share-nodes"></i></button>
            </div>
            `;
        } else if (role === 'user') {
            actionsHtml = `
            <div class="message-actions">
                <button class="edit-btn" title="Edit"><i class="fas fa-edit"></i></button>
                <button class="copy-btn" title="Copy"><i class="far fa-copy"></i></button>
            </div>
            `;
        }

        let contentHtml = '';
        if (content.startsWith('FILE_ATTACHMENT:')) {
            const parts = content.split(':|:');
            const fname = parts[1];
            const fsize = parts[2] || 'Ready';
            
            const ext = fname.split('.').pop().toLowerCase();
            let iconClass = 'fa-file-alt';
            let iconColor = '#94a3b8';
            
            if (ext === 'pdf') {
                iconClass = 'fa-file-pdf';
                iconColor = '#ef4444';
            } else if (ext === 'docx') {
                iconClass = 'fa-file-word';
                iconColor = '#3b82f6';
            } else if (ext === 'txt') {
                iconClass = 'fa-file-lines';
                iconColor = '#10b981';
            }
            
            contentHtml = `
            <div class="file-attachment-bubble" style="display: flex; align-items: center; gap: 12px; background-color: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px 14px; width: fit-content; max-width: 300px;">
                <i class="fas ${iconClass} file-icon" style="color:${iconColor}; font-size:24px;"></i>
                <div class="file-details" style="display: flex; flex-direction: column; overflow: hidden;">
                    <span class="file-name" style="font-weight:500; font-size:13px; color:white; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${fname}">${fname}</span>
                    <span class="file-size" style="font-size:11px; color:#94a3b8;">${fsize}</span>
                </div>
            </div>`;
        } else {
            if (typeof marked !== 'undefined') {
                contentHtml = marked.parse(content);
            } else {
                contentHtml = content.replace(/\n/g, '<br>');
            }
        }

        const statusBoxHtml = role === 'bot' ? `
        <div class="status-tracker-box hidden">
            <span class="status-tracker-spinner"><i class="fas fa-circle-notch fa-spin"></i></span>
            <span class="status-tracker-text">Analyzing query...</span>
        </div>` : '';

        msgDiv.innerHTML = `
            <div class="message-inner">
                <div class="avatar ${avatarClass}">${avatarIcon}</div>
                <div class="message-content">
                    ${statusBoxHtml}
                    <div class="message-text"></div>
                    ${actionsHtml}
                </div>
            </div>
        `;
        
        chatMessages.appendChild(msgDiv);
        const textContainer = msgDiv.querySelector('.message-text');

        if (role === 'bot' && !content.startsWith('FILE_ATTACHMENT:') && animate && content !== "") {
             let i = 0;
             const rawText = content;
             const cursorHtml = '<span class="typing-cursor"></span>';
             const interval = setInterval(() => {
                 if (i < rawText.length) {
                     i++;
                     const currentText = rawText.slice(0, i);
                     if (typeof marked !== 'undefined') {
                         textContainer.innerHTML = marked.parse(currentText) + cursorHtml;
                     } else {
                         textContainer.innerHTML = currentText.replace(/\n/g, '<br>') + cursorHtml;
                     }
                     postProcessMarkdown(textContainer);
                     scrollToBottom();
                 } else {
                     clearInterval(interval);
                     if (typeof marked !== 'undefined') {
                         textContainer.innerHTML = marked.parse(rawText);
                     } else {
                         textContainer.innerHTML = rawText.replace(/\n/g, '<br>');
                     }
                     postProcessMarkdown(textContainer);
                 }
             }, 15);
        } else {
             textContainer.innerHTML = contentHtml;
             postProcessMarkdown(textContainer);
             scrollToBottom();
        }
        
        if (content !== "" && !content.startsWith('FILE_ATTACHMENT:')) {
            const copyBtn = msgDiv.querySelector('.copy-btn');
            if (copyBtn) {
                copyBtn.addEventListener('click', () => {
                    const textToCopy = textContainer.innerText;
                    navigator.clipboard.writeText(textToCopy).then(() => {
                        showToast('Copied to clipboard!');
                    });
                });
            }

            const shareBtn = msgDiv.querySelector('.share-btn');
            if (shareBtn) {
                shareBtn.addEventListener('click', () => {
                    const textToShare = textContainer.innerText;
                    if (navigator.share) {
                        navigator.share({
                            title: 'Cyber Law Assistant',
                            text: textToShare
                        }).catch((err) => console.log('Error sharing:', err));
                    } else {
                        showToast('Sharing not supported on this browser', true);
                    }
                });
            }

            if (role === 'user') {
                const editBtn = msgDiv.querySelector('.edit-btn');
                if (editBtn) {
                    editBtn.addEventListener('click', () => {
                        const originalText = textContainer.innerText;
                        
                        textContainer.style.display = 'none';
                        const actions = msgDiv.querySelector('.message-actions');
                        if (actions) actions.style.display = 'none';
                        
                        const editDiv = document.createElement('div');
                        editDiv.className = 'edit-ui';
                        editDiv.innerHTML = `
                            <textarea class="edit-textarea">${originalText}</textarea>
                            <div class="edit-controls" style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 10px;">
                                <button class="edit-save-btn success-btn" style="padding: 6px 12px; width: auto; font-size: 13px;"><i class="fas fa-paper-plane"></i> Save & Submit</button>
                                <button class="edit-cancel-btn primary-btn" style="padding: 6px 12px; width: auto; font-size: 13px; background-color: var(--sidebar-bg); border: 1px solid var(--border-color);"><i class="fas fa-times"></i> Cancel</button>
                            </div>
                        `;
                        msgDiv.querySelector('.message-content').appendChild(editDiv);
                        
                        const textarea = editDiv.querySelector('textarea');
                        textarea.style.width = '100%';
                        textarea.style.minHeight = '80px';
                        textarea.style.background = 'rgba(0,0,0,0.2)';
                        textarea.style.border = '1px solid rgba(255,255,255,0.1)';
                        textarea.style.color = 'white';
                        textarea.style.padding = '10px';
                        textarea.style.borderRadius = '8px';
                        textarea.style.fontFamily = 'inherit';
                        textarea.style.resize = 'vertical';
                        textarea.style.outline = 'none';
                        textarea.focus();
                        
                        editDiv.querySelector('.edit-cancel-btn').onclick = () => {
                            editDiv.remove();
                            textContainer.style.display = 'block';
                            if (actions) actions.style.display = 'flex';
                        };
                        
                        editDiv.querySelector('.edit-save-btn').onclick = async () => {
                            const newText = textarea.value.trim();
                            if (!newText) return;
                            
                            const idx = msgDiv.dataset.index;
                            
                            if (userId && idx !== undefined) {
                                try {
                                    await fetch(`${API_BASE_URL}/history/trim/${currentSessionId}`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ user_id: userId, index: parseInt(idx) })
                                    });
                                } catch (e) { console.error("Trim failed", e); }
                            }
                            
                            while (msgDiv.nextElementSibling) {
                                msgDiv.nextElementSibling.remove();
                            }
                            msgDiv.remove();
                            
                            const messageInput = document.getElementById('message-input');
                            if (messageInput) {
                                messageInput.value = newText;
                                handleSend();
                            }
                        };
                    });
                }
            }
        }
        return msgDiv;
    }

    async function streamTypewriter(reader, container) {
        const decoder = new TextDecoder();
        let cleanResponseText = "";
        let isDone = false;
        
        const cursorHtml = '<span class="typing-cursor"></span>';
        
        const statusTracker = container.closest('.message-content').querySelector('.status-tracker-box');
        
        const updateStatusUI = (statusText) => {
            if (statusTracker) {
                statusTracker.classList.remove('hidden');
                const textSpan = statusTracker.querySelector('.status-tracker-text');
                if (textSpan) {
                    textSpan.textContent = statusText;
                }
            }
        };
        
        const resolveStatusUI = () => {
            if (statusTracker && !statusTracker.classList.contains('done')) {
                statusTracker.classList.add('done');
                const spinner = statusTracker.querySelector('.status-tracker-spinner');
                if (spinner) {
                    spinner.innerHTML = '<i class="fas fa-circle-check"></i>';
                }
                const textSpan = statusTracker.querySelector('.status-tracker-text');
                if (textSpan) {
                    textSpan.textContent = "Response Generated";
                }
                setTimeout(() => {
                    statusTracker.style.opacity = '0';
                    setTimeout(() => {
                        statusTracker.style.display = 'none';
                    }, 300);
                }, 1000);
            }
        };

        // Process stream and parse status updates
        const readStream = async () => {
            let streamBuffer = "";
            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        isDone = true;
                        break;
                    }
                    const chunk = decoder.decode(value, { stream: true });
                    streamBuffer += chunk;
                    
                    // Parse streamBuffer for status updates
                    while (true) {
                        const statusStart = streamBuffer.indexOf('$$status:');
                        if (statusStart !== -1) {
                            if (statusStart > 0) {
                                cleanResponseText += streamBuffer.slice(0, statusStart);
                                streamBuffer = streamBuffer.slice(statusStart);
                            }
                            
                            const statusEnd = streamBuffer.indexOf('$$', 9);
                            if (statusEnd !== -1) {
                                const statusLine = streamBuffer.slice(9, statusEnd).trim();
                                updateStatusUI(statusLine);
                                streamBuffer = streamBuffer.slice(statusEnd + 2);
                                if (streamBuffer.startsWith('\n')) {
                                    streamBuffer = streamBuffer.slice(1);
                                }
                            } else {
                                break;
                            }
                        } else {
                            const partialIndex = streamBuffer.indexOf('$$');
                            if (partialIndex !== -1 && (partialIndex === streamBuffer.length - 1 || streamBuffer.substring(partialIndex).startsWith('$$s'))) {
                                break;
                            } else {
                                cleanResponseText += streamBuffer;
                                streamBuffer = "";
                                break;
                            }
                        }
                    }
                }
            } catch (err) {
                console.error("Stream reading error:", err);
                isDone = true;
            }
        };
        readStream();

        // Animation typewriter loop
        const animate = async () => {
            let lastLength = 0;
            while (!isDone || lastLength < cleanResponseText.length) {
                if (lastLength < cleanResponseText.length) {
                    // Resolve status tracker when actual text starts streaming
                    resolveStatusUI();
                    
                    const remaining = cleanResponseText.slice(lastLength);
                    const words = remaining.split(/(\s+)/);
                    
                    for (const word of words) {
                        if (word === "") continue;
                        lastLength += word.length;
                        
                        const currentText = cleanResponseText.slice(0, lastLength);
                        if (typeof marked !== 'undefined') {
                            container.innerHTML = marked.parse(currentText) + cursorHtml;
                        } else {
                            container.innerHTML = currentText.replace(/\n/g, '<br>') + cursorHtml;
                        }
                        postProcessMarkdown(container);
                        scrollToBottom();
                        
                        await new Promise(r => setTimeout(r, 12)); 
                    }
                } else {
                    await new Promise(r => setTimeout(r, 50));
                }
            }
            
            // Clean up and finalize
            resolveStatusUI();
            if (typeof marked !== 'undefined') {
                container.innerHTML = marked.parse(cleanResponseText);
            } else {
                container.innerHTML = cleanResponseText.replace(/\n/g, '<br>');
            }
            postProcessMarkdown(container);
            
            // Re-setup copy / share click events on the correct clean text
            const copyBtn = container.closest('.message-content').querySelector('.copy-btn');
            if (copyBtn) {
                copyBtn.onclick = () => {
                    navigator.clipboard.writeText(cleanResponseText).then(() => {
                        showToast('Copied to clipboard!');
                    });
                };
            }
            const shareBtn = container.closest('.message-content').querySelector('.share-btn');
            if (shareBtn) {
                shareBtn.onclick = () => {
                    if (navigator.share) {
                        navigator.share({
                            title: 'Cyber Law Assistant',
                            text: cleanResponseText
                        }).catch(console.error);
                    } else {
                        navigator.clipboard.writeText(cleanResponseText).then(() => {
                            showToast('Copied text link!');
                        });
                    }
                };
            }
        };
        await animate();
    }

    function scrollToBottom() {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }

    async function handleSend() {
        const message = messageInput.value.trim();
        
        // Check for files still loading
        const previewContainer = document.getElementById('attachment-preview');
        if (previewContainer) {
            const loadingCards = previewContainer.querySelectorAll('.file-preview-card.loading');
            if (loadingCards.length > 0) {
                showToast("Please wait for files to finish processing.", true);
                return;
            }
        }
        
        // Collect attached files that are ready
        const attachedFiles = [];
        if (previewContainer) {
            const readyCards = previewContainer.querySelectorAll('.file-preview-card:not(.loading)');
            readyCards.forEach(card => {
                const filenameSpan = card.querySelector('.file-name');
                const fileStatusSpan = card.querySelector('.file-status');
                if (filenameSpan && fileStatusSpan && fileStatusSpan.classList.contains('ready')) {
                    const filename = filenameSpan.textContent;
                    attachedFiles.push(filename);
                    
                    // Render in the chat conversation list visually
                    appendMessage('user', `FILE_ATTACHMENT:|:${filename}:|:Ready`);
                    
                    // Remove card from preview area
                    card.remove();
                }
            });
            checkPreviewContainerEmpty();
        }
        
        if (!message && attachedFiles.length === 0) return;
        
        // Set a default prompt if query is empty but files were attached
        let finalMsg = message;
        if (!finalMsg && attachedFiles.length > 0) {
            finalMsg = "Explain this document.";
        }
        
        if (finalMsg) {
            appendMessage('user', finalMsg);
        }
        messageInput.value = '';
        
        const tr = translations[currentLang];
        const typingMsg = document.createElement('div');
        typingMsg.className = 'message bot';
        typingMsg.innerHTML = `
            <div class="message-inner">
                <div class="avatar bot-avatar"><i class="fas fa-robot text-white"></i></div>
                <div class="message-content">${tr.thinking}</div>
            </div>
        `;
        chatMessages.appendChild(typingMsg);
        scrollToBottom();
        
        try {
            const response = await fetch(`${API_BASE_URL}/chat_stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    user_id: userId, 
                    message: finalMsg, 
                    session_id: currentSessionId, 
                    language: currentLang,
                    attached_files: attachedFiles
                })
            });
            
            typingMsg.remove();
            
            if (!response.ok) {
                const errText = await response.text();
                appendMessage('bot', tr.errorServer + " Error Code: " + response.status);
                return;
            }
            
            document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
            addSessionToSidebar(currentSessionId, finalMsg, true);
            
            const botMsgDiv = appendMessage('bot', "", false); 
            const textContainer = botMsgDiv.querySelector('.message-text');
            
            const reader = response.body.getReader();
            await streamTypewriter(reader, textContainer);
            
        } catch (err) {
            typingMsg.remove();
            appendMessage('bot', tr.errorNet);
        }
    }

    // Load and render session files
    async function loadSessionFiles(sessionId) {
        const previewContainer = document.getElementById('attachment-preview');
        if (!previewContainer) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/files`);
            if (response.ok) {
                const data = await response.json();
                previewContainer.innerHTML = '';
                
                if (data.files && data.files.length > 0) {
                    previewContainer.classList.remove('hidden');
                    data.files.forEach(file => {
                        renderFileCard(file.id, file.filename, file.status);
                    });
                } else {
                    previewContainer.classList.add('hidden');
                }
            }
        } catch (err) {
            console.error("Error loading session files:", err);
        }
    }

    // Render a file card in the container
    function renderFileCard(fileId, filename, status) {
        const previewContainer = document.getElementById('attachment-preview');
        if (!previewContainer) return;
        
        // Check if card already exists
        let card = previewContainer.querySelector(`[data-file-id="${fileId}"]`);
        if (!card) {
            card = document.createElement('div');
            card.className = 'file-preview-card';
            card.dataset.fileId = fileId;
            previewContainer.appendChild(card);
        }
        
        const ext = filename.split('.').pop().toLowerCase();
        let iconClass = 'fa-file-alt';
        let iconColor = '#94a3b8';
        
        if (ext === 'pdf') {
            iconClass = 'fa-file-pdf';
            iconColor = '#ef4444';
        } else if (ext === 'docx') {
            iconClass = 'fa-file-word';
            iconColor = '#3b82f6';
        } else if (ext === 'txt') {
            iconClass = 'fa-file-lines';
            iconColor = '#10b981';
        }
        
        let statusText = 'Ready';
        let statusClass = 'ready';
        let showSpinner = false;
        
        if (status === 'uploading') {
            statusText = 'Uploading...';
            statusClass = 'uploading';
            showSpinner = true;
            card.classList.add('loading');
        } else if (status === 'extracting') {
            statusText = 'Extracting...';
            statusClass = 'extracting';
            showSpinner = true;
            card.classList.add('loading');
        } else if (status === 'indexing') {
            statusText = 'Indexing...';
            statusClass = 'indexing';
            showSpinner = true;
            card.classList.add('loading');
        } else if (status === 'ready') {
            statusText = 'Ready for questions';
            statusClass = 'ready';
            card.classList.remove('loading');
        } else if (status === 'error') {
            statusText = 'Error processing';
            statusClass = 'error';
            card.classList.remove('loading');
        }
        
        card.innerHTML = `
            <div class="file-info-preview">
                <i class="fas ${iconClass} file-icon" style="color: ${iconColor}; font-size: 24px;"></i>
                <div class="file-details">
                    <span class="file-name" title="${filename}">${filename}</span>
                    <span class="file-status ${statusClass}">${statusText}</span>
                </div>
            </div>
            <div class="file-actions-wrapper">
                ${showSpinner ? `<span class="file-loader-spinner"><i class="fas fa-circle-notch fa-spin"></i></span>` : ''}
                <button class="remove-file-btn" title="Remove File"><i class="fas fa-times"></i></button>
            </div>
        `;
        
        // Remove handler
        const removeBtn = card.querySelector('.remove-file-btn');
        removeBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (fileId.toString().startsWith('temp')) {
                card.remove();
                checkPreviewContainerEmpty();
                return;
            }
            
            if (confirm(`Remove "${filename}" from this session?`)) {
                try {
                    const response = await fetch(`${API_BASE_URL}/files/${fileId}`, { method: 'DELETE' });
                    if (response.ok) {
                        card.remove();
                        showToast('File removed');
                        checkPreviewContainerEmpty();
                    } else {
                        showToast('Failed to remove file', true);
                    }
                } catch (err) {
                    showToast('Network error removing file', true);
                }
            }
        });
    }

    function checkPreviewContainerEmpty() {
        const previewContainer = document.getElementById('attachment-preview');
        if (previewContainer && previewContainer.children.length === 0) {
            previewContainer.classList.add('hidden');
        }
    }

    // Process file uploading stream
    async function uploadFile(file) {
        if (!userId) {
            showToast("Please login to upload documents.", true);
            return;
        }
        
        // Render a temporary loading card
        const tempId = 'temp-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
        renderFileCard(tempId, file.name, 'uploading');
        
        const previewContainer = document.getElementById('attachment-preview');
        previewContainer.classList.remove('hidden');
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', userId);
        formData.append('session_id', currentSessionId);
        
        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                const errMsg = errData.error || 'Upload failed';
                updateCardToError(tempId, file.name, errMsg);
                return;
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep partial line in buffer
                
                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);
                            if (data.status && data.id) {
                                const card = previewContainer.querySelector(`[data-file-id="${tempId}"]`);
                                if (card) {
                                    card.dataset.fileId = data.id;
                                    renderFileCard(data.id, file.name, data.status);
                                } else {
                                    renderFileCard(data.id, file.name, data.status);
                                }
                            }
                        } catch (e) {
                            console.error("Line parse error:", e, line);
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Upload error:", err);
            updateCardToError(tempId, file.name, 'Connection error');
        }
    }

    function updateCardToError(cardId, filename, errMsg) {
        renderFileCard(cardId, filename, 'error');
        showToast(`Failed to upload ${filename}: ${errMsg}`, true);
    }

    // File Selection Handler
    fileUpload.addEventListener('change', (e) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;
        
        for (let i = 0; i < files.length; i++) {
            uploadFile(files[i]);
        }
        
        fileUpload.value = '';
    });

    // Voice Input Handler
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.onstart = function() {
            voiceBtn.classList.add('voice-active');
            messageInput.placeholder = translations[currentLang].listening;
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            messageInput.value += (messageInput.value ? ' ' : '') + transcript;
        };
        
        recognition.onend = function() {
            voiceBtn.classList.remove('voice-active');
            messageInput.placeholder = translations[currentLang].placeholder;
        };
        
        voiceBtn.addEventListener('click', () => {
            try { recognition.start(); } catch (e) { recognition.stop(); }
        });
    }

    // New Chat Button
    document.getElementById('new-chat-btn')?.addEventListener('click', () => {
        chatMessages.innerHTML = '';
        currentSessionId = Date.now().toString();
        localStorage.setItem('current_session_id', currentSessionId);
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
        appendMessage('bot', translations[currentLang].welcome);
        
        // Clear files container too
        const previewContainer = document.getElementById('attachment-preview');
        if (previewContainer) {
            previewContainer.innerHTML = '';
            previewContainer.classList.add('hidden');
        }
    });

    // Clear All Button
    document.getElementById('clear-all-btn')?.addEventListener('click', () => {
        if(confirm("Are you sure you want to clear the entire chat list?")) {
            const historyList = document.getElementById('chat-history-list');
            if(historyList) historyList.innerHTML = '';
            showToast(translations[currentLang].clearChatMsg);
        }
    });

    // Server Health Check
    async function checkServerStatus() {
        const statusDot = document.getElementById('connection-status');
        if (!statusDot) return;
        
        try {
            // Use a simple endpoint like /sessions or / to check connectivity
            const response = await fetch(`${API_BASE_URL}/`, { method: 'HEAD' });
            if (response.ok || response.status === 405) { // 405 is fine for HEAD if not allowed
                statusDot.className = 'status-indicator online';
                statusDot.title = 'Server Status: Online';
            } else {
                statusDot.className = 'status-indicator offline';
                statusDot.title = 'Server Status: Offline';
            }
        } catch (err) {
            statusDot.className = 'status-indicator offline';
            statusDot.title = 'Server Status: Offline (Connection Refused)';
        }
    }

    // Check on load and then every 30s
    checkServerStatus();
    setInterval(checkServerStatus, 30000);

    // Initial Load
    loadSessions();
}
