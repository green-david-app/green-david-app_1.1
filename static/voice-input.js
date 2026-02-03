/**
 * Voice Input Module - Green David App
 * Znovupoužitelný modul pro hlasové zadávání pomocí Web Speech API
 * 
 * Použití:
 *   VoiceInput.addButton('input-id');
 *   VoiceInput.addButton('textarea-id', { lang: 'cs-CZ', continuous: true });
 */

(function() {
  'use strict';

  // Check browser support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const isSupported = !!SpeechRecognition;

  if (!isSupported) {
    console.warn('Voice input not supported in this browser');
  }

  // Active recognition instance
  let activeRecognition = null;
  let activeButton = null;

  // Default options
  const defaultOptions = {
    lang: 'cs-CZ',
    continuous: false,
    interimResults: true,
    maxAlternatives: 1
  };

  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    .voice-input-wrapper {
      position: relative;
      display: inline-flex;
      align-items: center;
      width: 100%;
    }
    .voice-input-wrapper input,
    .voice-input-wrapper textarea {
      padding-right: 44px !important;
    }
    .voice-btn {
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      width: 32px;
      height: 32px;
      border: none;
      border-radius: 50%;
      background: rgba(159, 212, 161, 0.15);
      color: #4ade80;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      z-index: 5;
    }
    .voice-btn:hover {
      background: rgba(159, 212, 161, 0.25);
      transform: translateY(-50%) scale(1.05);
    }
    .voice-btn.recording {
      background: rgba(239, 68, 68, 0.2);
      color: #ef4444;
      animation: pulse-recording 1.5s ease-in-out infinite;
    }
    .voice-btn.recording:hover {
      background: rgba(239, 68, 68, 0.3);
    }
    .voice-btn svg {
      width: 18px;
      height: 18px;
    }
    .voice-btn.disabled {
      opacity: 0.3;
      cursor: not-allowed;
    }
    @keyframes pulse-recording {
      0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
      50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
    }
    
    /* Tooltip */
    .voice-btn::after {
      content: attr(data-tooltip);
      position: absolute;
      bottom: 100%;
      left: 50%;
      transform: translateX(-50%);
      padding: 4px 8px;
      background: #1a1a1a;
      color: #e8eef2;
      font-size: 11px;
      border-radius: 4px;
      white-space: nowrap;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s;
      margin-bottom: 4px;
    }
    .voice-btn:hover::after {
      opacity: 1;
    }
    
    /* For textarea - position at top right */
    .voice-input-wrapper textarea + .voice-btn {
      top: 12px;
      transform: none;
    }
  `;
  document.head.appendChild(style);

  // Mic icon SVG
  const micIconSVG = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
  </svg>`;

  // Stop icon SVG
  const stopIconSVG = `<svg viewBox="0 0 24 24" fill="currentColor" stroke="none">
    <rect x="6" y="6" width="12" height="12" rx="2"/>
  </svg>`;

  /**
   * Add voice input button to an input/textarea element
   * @param {string|HTMLElement} element - Element ID or element itself
   * @param {Object} options - Configuration options
   */
  function addButton(element, options = {}) {
    if (!isSupported) {
      console.warn('Voice input not supported');
      return null;
    }

    // Get element
    const input = typeof element === 'string' ? document.getElementById(element) : element;
    if (!input) {
      console.warn('Voice input: Element not found:', element);
      return null;
    }

    // Skip if already wrapped
    if (input.parentElement?.classList.contains('voice-input-wrapper')) {
      return input.parentElement.querySelector('.voice-btn');
    }

    // Merge options
    const opts = { ...defaultOptions, ...options };

    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'voice-input-wrapper';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    // Create button
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'voice-btn';
    btn.innerHTML = micIconSVG;
    btn.setAttribute('data-tooltip', 'Hlasové zadávání');
    wrapper.appendChild(btn);

    // Click handler
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      if (btn.classList.contains('recording')) {
        stopRecording();
      } else {
        startRecording(input, btn, opts);
      }
    });

    return btn;
  }

  /**
   * Start voice recognition
   */
  function startRecording(input, btn, opts) {
    // Stop any active recording
    if (activeRecognition) {
      stopRecording();
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = opts.lang;
      recognition.continuous = opts.continuous;
      recognition.interimResults = opts.interimResults;
      recognition.maxAlternatives = opts.maxAlternatives;

      // Store original value for interim results
      const originalValue = input.value;
      let finalTranscript = '';

      recognition.onstart = () => {
        btn.classList.add('recording');
        btn.innerHTML = stopIconSVG;
        btn.setAttribute('data-tooltip', 'Klikni pro zastavení');
        activeRecognition = recognition;
        activeButton = btn;
      };

      recognition.onresult = (event) => {
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        // Update input value
        const cursorPos = input.selectionStart || originalValue.length;
        const before = originalValue.substring(0, cursorPos);
        const after = originalValue.substring(cursorPos);
        
        if (opts.interimResults) {
          input.value = before + finalTranscript + interimTranscript + after;
        } else {
          input.value = before + finalTranscript + after;
        }

        // Trigger input event for React/Vue compatibility
        input.dispatchEvent(new Event('input', { bubbles: true }));
      };

      recognition.onerror = (event) => {
        console.error('Voice recognition error:', event.error);
        
        let message = 'Chyba rozpoznávání';
        switch (event.error) {
          case 'not-allowed':
            message = 'Přístup k mikrofonu byl zamítnut';
            break;
          case 'no-speech':
            message = 'Žádná řeč nebyla rozpoznána';
            break;
          case 'network':
            message = 'Chyba sítě';
            break;
        }
        
        if (window.showToast) {
          window.showToast(message, 'warning');
        }
        
        stopRecording();
      };

      recognition.onend = () => {
        stopRecording();
        
        // Clean up extra spaces
        input.value = input.value.replace(/\s+/g, ' ').trim();
        input.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Focus input
        input.focus();
      };

      recognition.start();
      
      if (window.showToast) {
        window.showToast('🎤 Poslouchám...', 'info');
      }

    } catch (err) {
      console.error('Failed to start voice recognition:', err);
      if (window.showToast) {
        window.showToast('Nepodařilo se spustit rozpoznávání hlasu', 'error');
      }
    }
  }

  /**
   * Stop voice recognition
   */
  function stopRecording() {
    if (activeRecognition) {
      try {
        activeRecognition.stop();
      } catch (e) {
        // Ignore
      }
      activeRecognition = null;
    }
    
    if (activeButton) {
      activeButton.classList.remove('recording');
      activeButton.innerHTML = micIconSVG;
      activeButton.setAttribute('data-tooltip', 'Hlasové zadávání');
      activeButton = null;
    }
  }

  /**
   * Check if voice input is supported
   */
  function checkSupport() {
    return isSupported;
  }

  /**
   * Initialize voice input on all elements with data-voice-input attribute
   */
  function autoInit() {
    document.querySelectorAll('[data-voice-input]').forEach(el => {
      const lang = el.getAttribute('data-voice-lang') || 'cs-CZ';
      addButton(el, { lang });
    });
  }

  // Auto-init on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }

  // Export
  window.VoiceInput = {
    addButton,
    stopRecording,
    isSupported: checkSupport,
    autoInit
  };

})();
