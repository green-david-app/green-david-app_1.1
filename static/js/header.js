/**
 * Mobile Header - Dropdown Menu + Mode Toggle
 */

(function() {
    'use strict';
    
    let dropdownOpen = false;
    
    // ==========================================
    // DROPDOWN MENU
    // ==========================================
    
    window.toggleHeaderMenu = function() {
        const dropdown = document.getElementById('headerDropdown');
        const overlay = document.getElementById('headerDropdownOverlay');
        const menuBtn = document.querySelector('.header-menu-btn');
        
        if (!dropdown) return;
        
        dropdownOpen = !dropdownOpen;
        
        if (dropdownOpen) {
            dropdown.classList.add('open');
            dropdown.setAttribute('aria-hidden', 'false');
            if (overlay) overlay.classList.add('open');
            if (menuBtn) menuBtn.setAttribute('aria-expanded', 'true');
            
            // Zavři při kliknutí mimo
            setTimeout(() => {
                document.addEventListener('click', handleOutsideClick);
            }, 10);
        } else {
            closeHeaderMenu();
        }
    };
    
    window.closeHeaderMenu = function() {
        const dropdown = document.getElementById('headerDropdown');
        const overlay = document.getElementById('headerDropdownOverlay');
        const menuBtn = document.querySelector('.header-menu-btn');
        
        dropdownOpen = false;
        
        if (dropdown) {
            dropdown.classList.remove('open');
            dropdown.setAttribute('aria-hidden', 'true');
        }
        if (overlay) overlay.classList.remove('open');
        if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
        
        document.removeEventListener('click', handleOutsideClick);
    };
    
    function handleOutsideClick(event) {
        const dropdown = document.getElementById('headerDropdown');
        const menuBtn = document.querySelector('.header-menu-btn');
        
        if (dropdown && menuBtn) {
            if (!dropdown.contains(event.target) && !menuBtn.contains(event.target)) {
                closeHeaderMenu();
            }
        }
    }
    
    // Zavři při scroll
    window.addEventListener('scroll', function() {
        if (dropdownOpen) closeHeaderMenu();
    }, { passive: true });
    
    // Zavři při resize
    window.addEventListener('resize', function() {
        if (dropdownOpen) closeHeaderMenu();
    });
    
    // Zavři při Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && dropdownOpen) {
            closeHeaderMenu();
        }
    });
    
    // ==========================================
    // MODE TOGGLE (FIELD/FULL)
    // ==========================================
    
    window.toggleMobileMode = async function() {
        const btn = document.querySelector('.mode-toggle-btn');
        const currentMode = btn?.dataset.currentMode || getCurrentMode();
        const newMode = currentMode === 'field' ? 'full' : 'field';
        
        console.log(`[Mode] Přepínám: ${currentMode} → ${newMode}`);
        
        // Vizuální feedback
        if (btn) {
            btn.classList.add('switching');
            btn.disabled = true;
        }
        
        try {
            // Ulož na server
            const response = await fetch('/api/user/settings', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mobile_mode: newMode })
            });
            
            if (response.ok) {
                // Cookie backup
                document.cookie = `mobile_mode=${newMode};path=/;max-age=31536000;SameSite=Lax`;
                
                // Toast
                showModeToast(newMode);
                
                // Reload po krátké pauze (aby uživatel viděl toast)
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                throw new Error('Server error');
            }
        } catch (error) {
            console.error('[Mode] Error:', error);
            
            // Offline fallback
            document.cookie = `mobile_mode=${newMode};path=/;max-age=31536000;SameSite=Lax`;
            showModeToast(newMode);
            
            setTimeout(() => {
                window.location.reload();
            }, 500);
        }
    };
    
    function getCurrentMode() {
        // 1. Z body class
        if (document.body.classList.contains('mobile-field')) return 'field';
        if (document.body.classList.contains('mobile-full')) return 'full';
        
        // 2. Z data atributu
        if (document.body.dataset.mode) return document.body.dataset.mode;
        
        // 3. Z cookie
        const match = document.cookie.match(/mobile_mode=(\w+)/);
        if (match) return match[1];
        
        // 4. Default
        return 'field';
    }
    
    function showModeToast(mode) {
        const message = mode === 'field' 
            ? '🏠 Režim: Terén (Field)' 
            : '📊 Režim: Plný (Full)';
        
        // Použij existující toast nebo vytvoř vlastní
        if (typeof showToast === 'function') {
            showToast(message, 'success');
        } else {
            // Fallback toast
            const toast = document.createElement('div');
            toast.className = 'mode-toast';
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                bottom: 80px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0,0,0,0.9);
                color: white;
                padding: 12px 24px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 500;
                z-index: 9999;
                animation: toastIn 0.3s ease;
            `;
            document.body.appendChild(toast);
            
            setTimeout(() => toast.remove(), 2000);
        }
    }
    
    // ==========================================
    // INIT
    // ==========================================
    
    document.addEventListener('DOMContentLoaded', function() {
        const mode = getCurrentMode();
        document.body.classList.add(`mode-${mode}`);
        document.body.dataset.mode = mode;
        
        // Aktualizuj mode toggle button
        const modeBtn = document.querySelector('.mode-toggle-btn');
        if (modeBtn) {
            modeBtn.dataset.currentMode = mode;
        }
        
        console.log('[Header] Initialized, mode:', mode);
    });
    
    // Legacy support - pokud existuje stará funkce toggleMode()
    if (typeof window.toggleMode === 'undefined') {
        window.toggleMode = window.toggleMobileMode;
    }
    
})();
