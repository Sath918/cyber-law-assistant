// Cyber Law Assistant - Premium Frontend Logic

const API_BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.origin === "file://" 
    ? "http://127.0.0.1:5001" 
    : window.location.origin;
let currentFile = null;

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
    const previewFilename = document.getElementById('preview-filename');
    const previewSize = document.getElementById('preview-size');
    const removeFileBtn = document.getElementById('remove-file-btn');
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
                    const bDiv = appendMessage('bot', chat.response, false);
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
            const fsize = parts[2];
            contentHtml = `
            <div class="file-attachment-bubble">
                <i class="fas fa-file-pdf file-icon"></i>
                <div class="file-details" style="color:white;">
                    <span class="file-name">${fname}</span>
                    <span class="file-size">${fsize}</span>
                </div>
            </div>`;
        } else {
            if (typeof marked !== 'undefined') {
                contentHtml = marked.parse(content);
            } else {
                contentHtml = content.replace(/\n/g, '<br>');
            }
        }

        msgDiv.innerHTML = `
            <div class="message-inner">
                <div class="avatar ${avatarClass}">${avatarIcon}</div>
                <div class="message-content">
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
                     scrollToBottom();
                 } else {
                     clearInterval(interval);
                     if (typeof marked !== 'undefined') {
                         textContainer.innerHTML = marked.parse(rawText);
                     } else {
                         textContainer.innerHTML = rawText.replace(/\n/g, '<br>');
                     }
                 }
             }, 15);
        } else {
             textContainer.innerHTML = contentHtml;
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
        let fullText = "";
        let isDone = false;
        
        const cursorHtml = '<span class="typing-cursor"></span>';

        // Process stream
        const readStream = async () => {
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    isDone = true;
                    break;
                }
                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;
            }
        };
        readStream();

        // Animation loop
        const animate = async () => {
            let lastLength = 0;
            while (!isDone || lastLength < fullText.length) {
                if (lastLength < fullText.length) {
                    const remaining = fullText.slice(lastLength);
                    const words = remaining.split(/(\s+)/); // Keep delimiters
                    
                    for (const word of words) {
                        if (word === "") continue;
                        lastLength += word.length;
                        
                        const currentText = fullText.slice(0, lastLength);
                        if (typeof marked !== 'undefined') {
                            container.innerHTML = marked.parse(currentText) + cursorHtml;
                        } else {
                            container.innerHTML = currentText.replace(/\n/g, '<br>') + cursorHtml;
                        }
                        scrollToBottom();
                        
                        await new Promise(r => setTimeout(r, 15)); 
                    }
                } else {
                    await new Promise(r => setTimeout(r, 50));
                }
            }
            
            if (typeof marked !== 'undefined') {
                container.innerHTML = marked.parse(fullText);
            } else {
                container.innerHTML = fullText.replace(/\n/g, '<br>');
            }
            
            // Final update to ensure copy button works with the right text
            const copyBtn = container.closest('.message-content').querySelector('.copy-btn');
            if (copyBtn) {
                copyBtn.onclick = () => {
                    navigator.clipboard.writeText(fullText).then(() => {
                        showToast('Copied to clipboard!');
                    });
                };
            }

            // Final update to ensure share button works with the right text
            const shareBtn = container.closest('.message-content').querySelector('.share-btn');
            if (shareBtn) {
                shareBtn.onclick = () => {
                    if (navigator.share) {
                        navigator.share({
                            title: 'Cyber Law Assistant',
                            text: fullText
                        }).catch((err) => console.log('Error sharing:', err));
                    } else {
                        showToast('Sharing not supported on this browser', true);
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
        if (!message && !currentFile) return;
        
        let fileContext = "";
        
        // Handle file send logic
        if (currentFile) {
             const fname = currentFile.name;
             const fsize = formatBytes(currentFile.size);
             
             // Append bubble to UI
             appendMessage('user', `FILE_ATTACHMENT:|:${fname}:|:${fsize}`);
             
             // Upload to backend
             const formData = new FormData();
             formData.append('file', currentFile);
             if (userId) formData.append('user_id', userId);
             
             try {
                 const upRes = await fetch(`${API_BASE_URL}/upload`, {
                     method: 'POST',
                     body: formData
                 });
                 if (upRes.ok) {
                     const upData = await upRes.json();
                     fileContext = `[User attached a document: ${upData.filename}] `;
                 }
             } catch(err) {
                 console.error("File upload error:", err);
             }
             
             // Clear file selection
             currentFile = null;
             attachmentPreview.classList.add('hidden');
             fileUpload.value = '';
        }
        
        if (!message && !fileContext) return;
        
        const finalMessage = fileContext + message;
        
        if (message) {
            appendMessage('user', message);
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
                body: JSON.stringify({ user_id: userId, message: finalMessage, session_id: currentSessionId, language: currentLang })
            });
            
            typingMsg.remove();
            
            if (!response.ok) {
                const errText = await response.text();
                appendMessage('bot', tr.errorServer + " Error Code: " + response.status);
                return;
            }
            
            document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
            addSessionToSidebar(currentSessionId, finalMessage, true);
            
            const botMsgDiv = appendMessage('bot', "", false); 
            const textContainer = botMsgDiv.querySelector('.message-text');
            
            const reader = response.body.getReader();
            await streamTypewriter(reader, textContainer);
            
            
        } catch (err) {
            typingMsg.remove();
            appendMessage('bot', tr.errorNet);
        }
    }

    // File Preview Handler
    fileUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        currentFile = file;
        previewFilename.textContent = file.name;
        previewSize.textContent = formatBytes(file.size);
        attachmentPreview.classList.remove('hidden');
    });

    removeFileBtn.addEventListener('click', () => {
        currentFile = null;
        fileUpload.value = '';
        attachmentPreview.classList.add('hidden');
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
