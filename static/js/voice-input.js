/**
 * GREEN DAVID APP - Voice Input (voice-input.js)
 * Speech recognition for task/note input
 */

(function() {
    'use strict';

    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    var recognition = null;
    var isRecording = false;

    /**
     * Start/stop voice input
     * @param {string} targetId - ID of textarea/input to fill
     */
    window.toggleVoiceInput = function(targetId) {
        if (!SpeechRecognition) {
            alert('Hlasové zadávání není v tomto prohlížeči podporováno.');
            return;
        }

        if (isRecording) {
            stopVoiceInput();
            return;
        }

        var target = document.getElementById(targetId);
        if (!target) return;

        recognition = new SpeechRecognition();
        recognition.lang = 'cs-CZ';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = function(event) {
            var transcript = event.results[0][0].transcript;
            target.value = (target.value ? target.value + ' ' : '') + transcript;
            target.dispatchEvent(new Event('input', { bubbles: true }));
        };

        recognition.onerror = function(event) {
            console.warn('Voice input error:', event.error);
            stopVoiceInput();
        };

        recognition.onend = function() {
            stopVoiceInput();
        };

        recognition.start();
        isRecording = true;

        // Update UI
        var btns = document.querySelectorAll('.voice-input-btn');
        btns.forEach(function(btn) { btn.classList.add('recording'); });
    };

    function stopVoiceInput() {
        if (recognition) {
            try { recognition.stop(); } catch(e) {}
        }
        isRecording = false;
        
        var btns = document.querySelectorAll('.voice-input-btn');
        btns.forEach(function(btn) { btn.classList.remove('recording'); });
    }

})();
