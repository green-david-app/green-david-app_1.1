/**
 * GREEN DAVID APP - Header (header.js)
 * Dropdown menu toggle, close on outside click
 */

(function() {
    'use strict';

    var dropdown = document.getElementById('headerDropdown');
    var overlay = document.getElementById('headerDropdownOverlay');
    var menuBtn = document.querySelector('.header-menu-btn');

    /**
     * Toggle header dropdown menu
     */
    window.toggleHeaderMenu = function() {
        if (!dropdown) return;
        
        var isOpen = dropdown.classList.contains('open');
        
        if (isOpen) {
            closeHeaderMenu();
        } else {
            openHeaderMenu();
        }
    };

    /**
     * Open dropdown
     */
    function openHeaderMenu() {
        if (!dropdown) return;
        dropdown.classList.add('open');
        if (overlay) overlay.classList.add('open');
        if (menuBtn) menuBtn.setAttribute('aria-expanded', 'true');
        dropdown.setAttribute('aria-hidden', 'false');
    }

    /**
     * Close dropdown
     */
    window.closeHeaderMenu = function() {
        if (!dropdown) return;
        dropdown.classList.remove('open');
        if (overlay) overlay.classList.remove('open');
        if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
        dropdown.setAttribute('aria-hidden', 'true');
    };

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeHeaderMenu();
        }
    });

    // Close on back button (mobile)
    window.addEventListener('popstate', function() {
        closeHeaderMenu();
    });

})();
