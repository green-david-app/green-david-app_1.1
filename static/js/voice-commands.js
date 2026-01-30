/**
 * Voice Commands System
 * Hlasové ovládání aplikace
 * 
 * Příkazy:
 * - "Dokonči úkol [název]"
 * - "Přidej úkol [název]"
 * - "Check-in [zakázka]" / "Příchod [zakázka]"
 * - "Check-out" / "Odchod"
 * - "Zapiš [počet] hodin na [zakázka]"
 * - "Otevři [stránka]"
 * - "Kolik mám úkolů"
 * - "Jaké je počasí"
 */

class VoiceCommands {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.commandHandlers = {};
        this.lastTranscript = '';
        
        this.setupCommands();
    }
    
    init() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn('Speech Recognition not supported');
            return false;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'cs-CZ';
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript.toLowerCase().trim();
            this.lastTranscript = transcript;
            console.log('🎤 Voice command:', transcript);
            this.processCommand(transcript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech error:', event.error);
            this.isListening = false;
            this.updateUI();
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this.updateUI();
        };
        
        console.log('✅ Voice Commands ready');
        return true;
    }
    
    setupCommands() {
        // Task commands
        this.addCommand(/(?:dokonči|splň|hotovo)\s+(?:úkol\s+)?(.+)/i, this.completeTask.bind(this));
        this.addCommand(/(?:přidej|vytvoř|nový)\s+(?:úkol\s+)?(.+)/i, this.createTask.bind(this));
        this.addCommand(/(?:smaž|odstraň)\s+(?:úkol\s+)?(.+)/i, this.deleteTask.bind(this));
        
        // GPS/Check-in commands
        this.addCommand(/(?:check.?in|příchod|přihlásit)\s*(?:na\s+)?(.+)?/i, this.checkIn.bind(this));
        this.addCommand(/(?:check.?out|odchod|odhlásit)/i, this.checkOut.bind(this));
        
        // Timesheet commands
        this.addCommand(/(?:zapiš|přidej)\s+(\d+(?:[.,]\d+)?)\s*(?:hodin?y?|h)\s+(?:na\s+)?(.+)/i, this.logHours.bind(this));
        
        // Navigation commands
        this.addCommand(/(?:otevři|jdi na|zobraz)\s+(.+)/i, this.navigate.bind(this));
        
        // Info commands
        this.addCommand(/(?:kolik|počet)\s+(?:mám\s+)?úkolů/i, this.countTasks.bind(this));
        this.addCommand(/(?:jaké je\s+)?počasí/i, this.getWeather.bind(this));
        this.addCommand(/(?:co mám\s+)?(?:dělat\s+)?dnes/i, this.todayOverview.bind(this));
        
        // Help
        this.addCommand(/(?:pomoc|help|příkazy|nápověda)/i, this.showHelp.bind(this));
    }
    
    addCommand(pattern, handler) {
        this.commandHandlers[pattern.source] = { pattern, handler };
    }
    
    async processCommand(transcript) {
        for (const key in this.commandHandlers) {
            const { pattern, handler } = this.commandHandlers[key];
            const match = transcript.match(pattern);
            
            if (match) {
                try {
                    await handler(match);
                    return;
                } catch (e) {
                    console.error('Command error:', e);
                    this.speak('Nastala chyba při vykonávání příkazu');
                    return;
                }
            }
        }
        
        // No command matched
        this.speak('Nerozuměl jsem příkazu. Řekni "nápověda" pro seznam příkazů.');
    }
    
    // === Command Handlers ===
    
    async completeTask(match) {
        const taskName = match[1].trim();
        
        try {
            const res = await fetch('/api/tasks');
            const data = await res.json();
            const tasks = Array.isArray(data) ? data : (data.tasks || []);
            
            // Find matching task
            const task = tasks.find(t => 
                t.title.toLowerCase().includes(taskName) && t.status !== 'done'
            );
            
            if (task) {
                await fetch(`/api/tasks/${task.id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'done' })
                });
                
                this.speak(`Úkol "${task.title}" označen jako dokončený`);
                showNotification(`✅ Úkol "${task.title}" dokončen`, 'success');
            } else {
                this.speak(`Nenašel jsem úkol obsahující "${taskName}"`);
            }
        } catch (e) {
            this.speak('Nepodařilo se dokončit úkol');
        }
    }
    
    async createTask(match) {
        const taskTitle = match[1].trim();
        
        try {
            await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    title: taskTitle.charAt(0).toUpperCase() + taskTitle.slice(1),
                    status: 'pending',
                    priority: 'normal'
                })
            });
            
            this.speak(`Vytvořen nový úkol: ${taskTitle}`);
            showNotification(`✅ Vytvořen úkol: ${taskTitle}`, 'success');
        } catch (e) {
            this.speak('Nepodařilo se vytvořit úkol');
        }
    }
    
    async deleteTask(match) {
        const taskName = match[1].trim();
        
        try {
            const res = await fetch('/api/tasks');
            const data = await res.json();
            const tasks = Array.isArray(data) ? data : (data.tasks || []);
            
            const task = tasks.find(t => t.title.toLowerCase().includes(taskName));
            
            if (task) {
                await fetch(`/api/tasks/${task.id}`, { method: 'DELETE' });
                this.speak(`Úkol "${task.title}" smazán`);
                showNotification(`🗑️ Úkol "${task.title}" smazán`, 'info');
            } else {
                this.speak(`Nenašel jsem úkol "${taskName}"`);
            }
        } catch (e) {
            this.speak('Nepodařilo se smazat úkol');
        }
    }
    
    async checkIn(match) {
        const jobName = match[1]?.trim();
        
        if (window.gpsTracker) {
            if (jobName) {
                // Find job by name
                const job = window.gpsTracker.jobLocations.find(j => 
                    j.name.toLowerCase().includes(jobName)
                );
                
                if (job) {
                    await window.gpsTracker.checkIn(job.id);
                    this.speak(`Check-in na zakázku ${job.name}`);
                } else {
                    this.speak(`Nenašel jsem zakázku "${jobName}"`);
                }
            } else {
                window.gpsTracker.showCheckInModal();
                this.speak('Vyber zakázku pro check-in');
            }
        } else {
            this.speak('GPS tracker není dostupný');
        }
    }
    
    async checkOut() {
        if (window.gpsTracker) {
            const result = await window.gpsTracker.checkOut();
            if (result) {
                this.speak(`Check-out. Zaznamenáno ${result.hoursWorked.toFixed(1)} hodin.`);
            } else {
                this.speak('Nejsi přihlášen na žádné zakázce');
            }
        }
    }
    
    async logHours(match) {
        const hours = parseFloat(match[1].replace(',', '.'));
        const jobName = match[2].trim();
        
        try {
            const res = await fetch('/api/jobs');
            const data = await res.json();
            const jobs = Array.isArray(data) ? data : (data.jobs || []);
            
            const job = jobs.find(j => 
                (j.client || j.name || '').toLowerCase().includes(jobName)
            );
            
            if (job) {
                await fetch('/api/timesheets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        job_id: job.id,
                        hours: hours,
                        date: new Date().toISOString().split('T')[0],
                        description: 'Zapsáno hlasem'
                    })
                });
                
                this.speak(`Zapsáno ${hours} hodin na zakázku ${job.client || job.name}`);
                showNotification(`✅ Zapsáno ${hours}h na ${job.client || job.name}`, 'success');
            } else {
                this.speak(`Nenašel jsem zakázku "${jobName}"`);
            }
        } catch (e) {
            this.speak('Nepodařilo se zapsat hodiny');
        }
    }
    
    navigate(match) {
        const page = match[1].trim().toLowerCase();
        
        const routes = {
            'domů': '/',
            'dashboard': '/',
            'úvod': '/',
            'zakázky': '/jobs.html',
            'zakázek': '/jobs.html',
            'úkoly': '/tasks.html',
            'úkolů': '/tasks.html',
            'výkazy': '/timesheets.html',
            'zaměstnance': '/employees.html',
            'zaměstnanců': '/employees.html',
            'tým': '/employees.html',
            'sklad': '/warehouse',
            'materiál': '/warehouse',
            'timeline': '/timeline',
            'plánování': '/planning/daily',
            'kalendář': '/calendar.html',
            'nastavení': '/settings.html',
            'školka': '/nursery',
            'rostliny': '/nursery'
        };
        
        for (const [key, url] of Object.entries(routes)) {
            if (page.includes(key)) {
                this.speak(`Otevírám ${key}`);
                window.location.href = url;
                return;
            }
        }
        
        this.speak(`Neznám stránku "${page}"`);
    }
    
    async countTasks() {
        try {
            const res = await fetch('/api/tasks');
            const data = await res.json();
            const tasks = Array.isArray(data) ? data : (data.tasks || []);
            
            const pending = tasks.filter(t => t.status !== 'done').length;
            const urgent = tasks.filter(t => t.priority === 'urgent' && t.status !== 'done').length;
            
            let message = `Máš ${pending} nesplněných úkolů.`;
            if (urgent > 0) {
                message += ` Z toho ${urgent} urgentních.`;
            }
            
            this.speak(message);
        } catch (e) {
            this.speak('Nepodařilo se načíst úkoly');
        }
    }
    
    async getWeather() {
        try {
            const res = await fetch('/api/weather');
            const weather = await res.json();
            
            if (weather && weather.current) {
                const temp = Math.round(weather.current.temperature);
                const desc = weather.current.description || '';
                this.speak(`Aktuálně ${temp} stupňů, ${desc}`);
            } else {
                this.speak('Počasí není dostupné');
            }
        } catch (e) {
            this.speak('Nepodařilo se načíst počasí');
        }
    }
    
    async todayOverview() {
        try {
            const [tasksRes, weatherRes] = await Promise.all([
                fetch('/api/tasks').then(r => r.json()),
                fetch('/api/weather').then(r => r.json()).catch(() => null)
            ]);
            
            const tasks = Array.isArray(tasksRes) ? tasksRes : (tasksRes.tasks || []);
            const today = new Date().toISOString().split('T')[0];
            
            const todayTasks = tasks.filter(t => t.deadline === today && t.status !== 'done');
            const urgent = tasks.filter(t => t.priority === 'urgent' && t.status !== 'done');
            
            let message = '';
            
            if (weatherRes?.current) {
                message += `Dnes ${Math.round(weatherRes.current.temperature)} stupňů. `;
            }
            
            if (todayTasks.length > 0) {
                message += `Máš ${todayTasks.length} úkolů na dnes. `;
            }
            
            if (urgent.length > 0) {
                message += `${urgent.length} urgentních úkolů čeká. `;
            }
            
            if (!message) {
                message = 'Dnes nemáš žádné naplánované úkoly. Volný den!';
            }
            
            this.speak(message);
        } catch (e) {
            this.speak('Nepodařilo se načíst přehled');
        }
    }
    
    showHelp() {
        const helpText = `
            Dostupné příkazy:
            "Přidej úkol" a pak název.
            "Dokonči úkol" a část názvu.
            "Check-in" pro příchod na zakázku.
            "Check-out" pro odchod.
            "Zapiš 4 hodiny na" a název zakázky.
            "Otevři zakázky" pro navigaci.
            "Kolik mám úkolů" pro přehled.
            "Jaké je počasí" pro počasí.
        `;
        
        this.speak('Dostupné příkazy: Přidej úkol, Dokonči úkol, Check-in, Check-out, Zapiš hodiny, Otevři stránku, a další.');
        
        // Show visual help
        if (typeof showNotification === 'function') {
            showNotification('Příkazy: Přidej/Dokonči úkol, Check-in/out, Zapiš hodiny, Otevři [stránka]', 'info');
        }
    }
    
    // === Voice Output ===
    
    speak(text) {
        if ('speechSynthesis' in window) {
            // Cancel any ongoing speech
            speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'cs-CZ';
            utterance.rate = 1.1;
            utterance.pitch = 1;
            
            // Try to find Czech voice
            const voices = speechSynthesis.getVoices();
            const czechVoice = voices.find(v => v.lang.startsWith('cs'));
            if (czechVoice) {
                utterance.voice = czechVoice;
            }
            
            speechSynthesis.speak(utterance);
        }
        
        // Also show notification
        if (typeof showNotification === 'function') {
            showNotification(text, 'info');
        }
    }
    
    // === UI Controls ===
    
    startListening() {
        if (!this.recognition) {
            if (!this.init()) return;
        }
        
        this.isListening = true;
        this.updateUI();
        this.recognition.start();
        
        // Visual feedback
        if (typeof showNotification === 'function') {
            showNotification('🎤 Poslouchám... Řekni příkaz', 'info');
        }
    }
    
    stopListening() {
        if (this.recognition) {
            this.recognition.stop();
        }
        this.isListening = false;
        this.updateUI();
    }
    
    updateUI() {
        const btn = document.getElementById('voice-command-btn');
        if (!btn) return;
        
        if (this.isListening) {
            btn.classList.add('listening');
            btn.innerHTML = `
                <div class="voice-pulse"></div>
                <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
                    <rect x="6" y="6" width="12" height="12" rx="2"/>
                </svg>
            `;
        } else {
            btn.classList.remove('listening');
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="23"/>
                    <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
            `;
        }
    }
    
    // Create floating button
    createFloatingButton() {
        const existing = document.getElementById('voice-command-btn');
        if (existing) return;
        
        const btn = document.createElement('button');
        btn.id = 'voice-command-btn';
        btn.className = 'voice-command-btn';
        btn.title = 'Hlasové příkazy (podržte)';
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
        `;
        
        // Click to toggle
        btn.onclick = () => {
            if (this.isListening) {
                this.stopListening();
            } else {
                this.startListening();
            }
        };
        
        document.body.appendChild(btn);
    }
}

// Styles
const voiceStyles = document.createElement('style');
voiceStyles.textContent = `
    .voice-command-btn {
        position: fixed;
        bottom: 100px;
        left: 20px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: linear-gradient(135deg, #9FD4A1, #7bc47e);
        border: none;
        color: #0a0e11;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(159, 212, 161, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s;
        z-index: 1000;
    }
    
    .voice-command-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 25px rgba(159, 212, 161, 0.5);
    }
    
    .voice-command-btn.listening {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        animation: voice-glow 1s infinite;
    }
    
    @keyframes voice-glow {
        0%, 100% { box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4); }
        50% { box-shadow: 0 4px 30px rgba(239, 68, 68, 0.7); }
    }
    
    .voice-pulse {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: rgba(239, 68, 68, 0.3);
        animation: voice-pulse 1.5s infinite;
    }
    
    @keyframes voice-pulse {
        0% { transform: scale(1); opacity: 1; }
        100% { transform: scale(2); opacity: 0; }
    }
    
    @media (max-width: 768px) {
        .voice-command-btn {
            bottom: 160px;
            left: 16px;
            width: 48px;
            height: 48px;
        }
    }
`;
document.head.appendChild(voiceStyles);

// Global instance
window.voiceCommands = new VoiceCommands();

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    voiceCommands.init();
    // Plovoucí tlačítko odstraněno - použij VoiceInput pro input pole
});
