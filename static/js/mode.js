/**
 * GREEN DAVID APP - Mode Toggle (mode.js)
 * Switches between FIELD (simplified) and FULL (desktop-like) mode
 */

(function() {
    'use strict';

    /**
     * Get current mode from body class or data attribute
     */
    function getCurrentMode() {
        // From body class
        if (document.body.classList.contains('mobile-field')) return 'field';
        if (document.body.classList.contains('mobile-full')) return 'full';
        
        // From data attribute
        var mode = document.body.dataset.mode;
        if (mode) return mode;
        
        // From cookie
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var parts = cookies[i].trim().split('=');
            if (parts[0] === 'mobile_mode') return parts[1];
        }
        
        // Default
        return 'field';
    }

    /**
     * Toggle between FIELD and FULL mode
     */
    window.toggleMobileMode = function() {
        var currentMode = getCurrentMode();
        var newMode = currentMode === 'field' ? 'full' : 'field';
        
        // Set cookie for server-side detection
        document.cookie = 'mobile_mode=' + newMode + ';path=/;max-age=31536000;SameSite=Lax';
        
        // Try API call to set mode server-side
        fetch('/api/set-mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: newMode })
        }).catch(function() {
            // API might not exist yet, cookie is enough
        });
        
        // Reload to apply new mode layout
        window.location.reload();
    };

    /**
     * Get mode for use in other scripts
     */
    window.getMobileMode = function() {
        return getCurrentMode();
    };

})();
