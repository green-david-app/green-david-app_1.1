/**
 * Mobile Mode Switch - FIELD ↔ FULL
 * 
 * Spravuje přepínání mezi Field a Full mobilními režimy.
 */

const MobileMode = {
    current: null,
    
    init() {
        // Získej aktuální mode z body data atributu nebo cookie
        this.current = document.body.dataset.mode || 
                      this.getCookie('mobile_mode') || 
                      'field';
        
        // Pokud je 'auto', urči podle role (z window.currentUser)
        if (this.current === 'auto') {
            const role = window.currentUser?.role || 'worker';
            const roleDefaults = {
                'director': 'full',
                'manager': 'full',
                'lander': 'field',
                'worker': 'field'
            };
            this.current = roleDefaults[role] || 'field';
        }
        
        this.updateUI();
    },
    
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },
    
    setCookie(name, value, days = 365) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    },
    
    async toggle() {
        const newMode = this.current === 'field' ? 'full' : 'field';
        
        try {
            // Zkus uložit na server
            const response = await fetch('/api/user/settings', {
                method: 'PATCH',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ mobile_mode: newMode })
            });
            
            if (response.ok) {
                // Úspěch - ulož do cookie jako fallback a reload
                this.setCookie('mobile_mode', newMode);
                window.location.reload();
            } else {
                // Fallback: uložit do cookie a reload
                this.setCookie('mobile_mode', newMode);
                window.location.reload();
            }
        } catch (error) {
            console.error('Mode switch failed:', error);
            // Fallback: uložit do cookie a reload
            this.setCookie('mobile_mode', newMode);
            window.location.reload();
        }
    },
    
    updateUI() {
        const toggleBtn = document.querySelector('.mode-toggle');
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-label', 
                this.current === 'field' 
                    ? 'Přepnout na Full režim' 
                    : 'Přepnout na Field režim'
            );
            
            // Aktualizuj ikonu podle aktuálního módu
            const icon = toggleBtn.querySelector('svg');
            if (icon && this.current === 'field') {
                // Ikona pro přepnutí na full (grid)
                icon.innerHTML = `
                    <rect x="3" y="3" width="7" height="7"/>
                    <rect x="14" y="3" width="7" height="7"/>
                    <rect x="3" y="14" width="7" height="7"/>
                    <rect x="14" y="14" width="7" height="7"/>
                `;
            } else if (icon && this.current === 'full') {
                // Ikona pro přepnutí na field (single column)
                icon.innerHTML = `
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <line x1="9" y1="3" x2="9" y2="21"/>
                `;
            }
        }
    }
};

// Globální funkce pro onclick handler
window.toggleMode = function() {
    MobileMode.toggle();
};

// Inicializace při načtení stránky
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => MobileMode.init());
} else {
    MobileMode.init();
}
