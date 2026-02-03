/**
 * Voice Input Module pro Green David App
 * 
 * Podporované prohlížeče:
 * - Chrome (desktop) - plná podpora
 * - Chrome Android - plná podpora (vyžaduje HTTPS)
 * - Samsung Internet - plná podpora (vyžaduje HTTPS)
 * - Edge Android - plná podpora (vyžaduje HTTPS)
 * - Safari iOS 14.5+ - plná podpora (vyžaduje HTTPS + user gesture)
 * - Firefox - NEPODPORUJE Web Speech API
 * 
 * DŮLEŽITÉ: Vyžaduje HTTPS (kromě localhost)!
 */
const VoiceInput = {
    recognition: null,
    isListening: false,
    targetInput: null,
    button: null,
    supportStatus: 'unknown', // 'supported', 'unsupported', 'no-https'
    
    // Konfigurace
    config: {
        lang: 'cs-CZ',           // Čeština
        continuous: false,        // Jeden příkaz (lepší pro mobil)
        interimResults: true,     // Průběžné výsledky
        maxAlternatives: 1
    },
    
    /**
     * Inicializace - volat při DOMContentLoaded
     */
    init() {
        // Detekce podpory - MUSÍ použít webkit prefix pro Android/iOS
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('[VoiceInput] Speech Recognition není podporováno v tomto prohlížeči');
            this.supportStatus = 'unsupported';
            this.hideAllVoiceButtons();
            return false;
        }
        
        // Kontrola HTTPS (vyžadováno na mobilech)
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            console.warn('[VoiceInput] Speech Recognition vyžaduje HTTPS');
            this.supportStatus = 'no-https';
            this.hideAllVoiceButtons();
            return false;
        }
        
        // Vytvoř instanci
        try {
            this.recognition = new SpeechRecognition();
            this.recognition.lang = this.config.lang;
            this.recognition.continuous = this.config.continuous;
            this.recognition.interimResults = this.config.interimResults;
            this.recognition.maxAlternatives = this.config.maxAlternatives;
            
            // Event handlery
            this.recognition.onstart = () => this.onStart();
            this.recognition.onresult = (e) => this.onResult(e);
            this.recognition.onerror = (e) => this.onError(e);
            this.recognition.onend = () => this.onEnd();
            this.recognition.onspeechend = () => {
                // Auto-stop po dokončení řeči (důležité pro mobil)
                console.log('[VoiceInput] Speech ended');
            };
            this.recognition.onnomatch = () => {
                console.log('[VoiceInput] No match');
                this.showError('Nerozpoznáno. Zkuste to znovu.');
            };
            
            this.supportStatus = 'supported';
            
        } catch (error) {
            console.error('[VoiceInput] Chyba při vytváření instance:', error);
            this.supportStatus = 'unsupported';
            this.hideAllVoiceButtons();
            return false;
        }
        
        // Nastav všechny voice buttony
        this.setupButtons();
        
        console.log('[VoiceInput] Inicializován, platforma:', this.detectPlatform());
        return true;
    },
    
    /**
     * Detekce platformy pro debugging
     */
    detectPlatform() {
        const ua = navigator.userAgent;
        if (/Android/i.test(ua)) return 'Android';
        if (/iPad|iPhone|iPod/i.test(ua)) return 'iOS';
        if (/Windows/i.test(ua)) return 'Windows';
        if (/Mac/i.test(ua)) return 'macOS';
        return 'Unknown';
    },
    
    /**
     * Najde a nastaví všechny voice buttony
     */
    setupButtons() {
        document.querySelectorAll('[data-voice-input]').forEach(btn => {
            const targetSelector = btn.dataset.voiceInput;
            const targetInput = document.querySelector(targetSelector);
            
            if (targetInput) {
                // Odstraň staré event listenery (pokud existují)
                btn.replaceWith(btn.cloneNode(true));
                const newBtn = document.querySelector(`[data-voice-input="${targetSelector}"]`);
                
                // Přidej nový event listener
                newBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.startListening(targetInput, newBtn);
                });
                
                // Touch events pro lepší mobilní odezvu
                newBtn.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.startListening(targetInput, newBtn);
                }, { passive: false });
                
                // Zobraz button
                newBtn.style.display = '';
                newBtn.disabled = false;
                newBtn.classList.add('voice-enabled');
                
                // Ulož původní placeholder
                if (!targetInput.dataset.originalPlaceholder) {
                    targetInput.dataset.originalPlaceholder = targetInput.placeholder || '';
                }
            }
        });
        
        console.log('[VoiceInput] Nastaveno buttonů:', document.querySelectorAll('[data-voice-input]').length);
    },
    
    /**
     * Skryje voice buttony pokud není podpora
     */
    hideAllVoiceButtons() {
        document.querySelectorAll('[data-voice-input]').forEach(btn => {
            btn.style.display = 'none';
        });
    },
    
    /**
     * Spustí naslouchání
     */
    startListening(inputElement, buttonElement) {
        // Toggle - pokud už běží, zastav
        if (this.isListening) {
            this.stopListening();
            return;
        }
        
        this.targetInput = inputElement;
        this.button = buttonElement;
        
        // Focus na input (pomáhá na některých mobilech)
        this.targetInput.focus();
        
        // Spusť rozpoznávání
        try {
            // Na Androidu někdy potřeba malý delay
            setTimeout(() => {
                try {
                    this.recognition.start();
                    console.log('[VoiceInput] Recognition started');
                } catch (error) {
                    this.handleStartError(error);
                }
            }, 100);
            
        } catch (error) {
            this.handleStartError(error);
        }
    },
    
    /**
     * Zpracování chyby při startu
     */
    handleStartError(error) {
        console.error('[VoiceInput] Start error:', error);
        
        if (error.name === 'InvalidStateError') {
            // Už běží - zastav a zkus znovu
            this.recognition.stop();
            setTimeout(() => {
                try {
                    this.recognition.start();
                } catch (e) {
                    this.showError('Nepodařilo se spustit mikrofon. Zkuste to znovu.');
                }
            }, 200);
        } else if (error.name === 'NotAllowedError') {
            this.showError('Přístup k mikrofonu byl zamítnut. Povolte mikrofon v nastavení prohlížeče.');
        } else {
            this.showError('Nepodařilo se spustit mikrofon.');
        }
    },
    
    /**
     * Zastaví naslouchání
     */
    stopListening() {
        if (this.recognition && this.isListening) {
            try {
                this.recognition.stop();
            } catch (e) {
                console.warn('[VoiceInput] Stop error:', e);
            }
        }
    },
    
    /**
     * Event: Začátek naslouchání
     */
    onStart() {
        this.isListening = true;
        console.log('[VoiceInput] Listening started');
        
        if (this.button) {
            this.button.classList.add('listening');
            this.button.setAttribute('aria-label', 'Naslouchám... (klikni pro zastavení)');
        }
        
        if (this.targetInput) {
            this.targetInput.placeholder = '🎤 Mluvte...';
            this.targetInput.classList.add('voice-active');
        }
        
        // Vizuální feedback
        this.showListeningIndicator();
        
        // Vibrace na mobilu (pokud podporováno)
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    },
    
    /**
     * Event: Výsledek rozpoznávání
     */
    onResult(event) {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            const confidence = event.results[i][0].confidence;
            
            console.log(`[VoiceInput] Result: "${transcript}" (confidence: ${confidence}, final: ${event.results[i].isFinal})`);
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }
        
        if (this.targetInput) {
            if (finalTranscript) {
                // Finální text - přidej k existujícímu obsahu
                const currentValue = this.targetInput.value;
                const separator = currentValue && !currentValue.endsWith(' ') ? ' ' : '';
                this.targetInput.value = currentValue + separator + finalTranscript;
                
                // Trigger input event pro případné listenery
                this.targetInput.dispatchEvent(new Event('input', { bubbles: true }));
                this.targetInput.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Vibrace pro potvrzení
                if (navigator.vibrate) {
                    navigator.vibrate([50, 50, 50]);
                }
                
                console.log('[VoiceInput] Final text added:', finalTranscript);
                
            } else if (interimTranscript) {
                // Průběžný text - zobraz
                this.showInterimResult(interimTranscript);
            }
        }
    },
    
    /**
     * Event: Chyba
     */
    onError(event) {
        console.error('[VoiceInput] Error:', event.error, event.message);
        
        const errorMessages = {
            'no-speech': 'Nezachycen žádný hlas. Zkuste mluvit hlasitěji.',
            'audio-capture': 'Mikrofon není dostupný. Zkontrolujte, zda není používán jinou aplikací.',
            'not-allowed': 'Přístup k mikrofonu byl zamítnut.\n\nPovolte mikrofon v nastavení prohlížeče.',
            'network': 'Chyba sítě. Zkontrolujte připojení k internetu.',
            'aborted': 'Rozpoznávání bylo přerušeno.',
            'language-not-supported': 'Čeština není podporována na tomto zařízení.',
            'service-not-allowed': 'Služba rozpoznávání hlasu není dostupná.'
        };
        
        const message = errorMessages[event.error] || `Chyba rozpoznávání: ${event.error}`;
        
        // Nezobrazuj error pro 'aborted' (uživatel zastavil)
        if (event.error !== 'aborted') {
            this.showError(message);
        }
        
        this.onEnd();
    },
    
    /**
     * Event: Konec naslouchání
     */
    onEnd() {
        this.isListening = false;
        console.log('[VoiceInput] Listening ended');
        
        if (this.button) {
            this.button.classList.remove('listening');
            this.button.setAttribute('aria-label', 'Hlasové zadávání');
        }
        
        if (this.targetInput) {
            this.targetInput.placeholder = this.targetInput.dataset.originalPlaceholder || '';
            this.targetInput.classList.remove('voice-active');
        }
        
        this.hideListeningIndicator();
        this.hideInterimResult();
    },
    
    /**
     * Zobrazí indikátor naslouchání
     */
    showListeningIndicator() {
        // Odstraň existující
        this.hideListeningIndicator();
        
        const indicator = document.createElement('div');
        indicator.id = 'voice-listening-indicator';
        indicator.className = 'voice-indicator';
        indicator.innerHTML = `
            <div class="voice-indicator-content">
                <div class="voice-waves">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
                <span class="voice-text">Naslouchám...</span>
                <button class="voice-stop-btn" onclick="VoiceInput.stopListening()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <rect x="6" y="6" width="12" height="12" rx="2"/>
                    </svg>
                </button>
            </div>
        `;
        document.body.appendChild(indicator);
        
        // Animace vstupu
        requestAnimationFrame(() => {
            indicator.classList.add('visible');
        });
    },
    
    /**
     * Skryje indikátor
     */
    hideListeningIndicator() {
        const indicator = document.getElementById('voice-listening-indicator');
        if (indicator) {
            indicator.classList.remove('visible');
            setTimeout(() => indicator.remove(), 200);
        }
    },
    
    /**
     * Zobrazí průběžný výsledek
     */
    showInterimResult(text) {
        let interim = document.getElementById('voice-interim-result');
        if (!interim) {
            interim = document.createElement('div');
            interim.id = 'voice-interim-result';
            interim.className = 'voice-interim';
            document.body.appendChild(interim);
        }
        interim.textContent = text;
        interim.classList.add('visible');
    },
    
    /**
     * Skryje průběžný výsledek
     */
    hideInterimResult() {
        const interim = document.getElementById('voice-interim-result');
        if (interim) {
            interim.classList.remove('visible');
            setTimeout(() => interim.remove(), 200);
        }
    },
    
    /**
     * Zobrazí chybu
     */
    showError(message) {
        // Použij existující toast systém
        if (typeof showToast === 'function') {
            showToast(message, 'error');
        } else if (typeof Toastify === 'function') {
            Toastify({
                text: message,
                duration: 4000,
                gravity: 'top',
                position: 'center',
                backgroundColor: '#f44336'
            }).showToast();
        } else {
            // Fallback - vlastní toast
            this.showFallbackToast(message, 'error');
        }
    },
    
    /**
     * Fallback toast pokud není žádný toast systém
     */
    showFallbackToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `voice-toast voice-toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        requestAnimationFrame(() => toast.classList.add('visible'));
        
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },
    
    /**
     * Kontrola podpory (pro podmíněné zobrazení UI)
     */
    isSupported() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const hasHttps = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
        return !!SpeechRecognition && hasHttps;
    },
    
    /**
     * Vrátí důvod proč není podporováno
     */
    getUnsupportedReason() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            return 'Váš prohlížeč nepodporuje hlasové zadávání. Zkuste Chrome nebo Safari.';
        }
        if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
            return 'Hlasové zadávání vyžaduje zabezpečené připojení (HTTPS).';
        }
        return 'Neznámý důvod';
    }
};

// Auto-init při načtení stránky
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => VoiceInput.init());
} else {
    VoiceInput.init();
}

// Export pro globální použití
window.VoiceInput = VoiceInput;
