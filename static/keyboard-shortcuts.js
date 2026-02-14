// Global Keyboard Shortcuts
(function() {
    const shortcuts = {
        'g': { action: null, desc: 'Navigace (G + ...)' }, // Group
        'n': { action: () => {
            const currentPath = window.location.pathname;
            if (currentPath.includes('jobs')) {
                document.getElementById('btn-new-job')?.click();
            } else if (currentPath.includes('tasks')) {
                document.getElementById('btn-new-task')?.click();
            } else if (currentPath.includes('timesheets')) {
                window.location.href = '/timesheets.html';
            } else {
                if (window.setAppTab) {
                    window.setAppTab('jobs');
                } else {
                    window.location.href = '/jobs.html';
                }
            }
        }, desc: 'Nová zakázka/úkol' },
        't': { action: () => {
            if (window.location.pathname.includes('tasks')) {
                document.getElementById('btn-new-task')?.click();
            } else {
                window.location.href = '/tasks.html';
            }
        }, desc: 'Přejít na úkoly' },
        'e': { action: () => {
            window.location.href = '/timesheets.html';
        }, desc: 'Výkazy hodin' },
        's': { action: () => {
            window.location.href = '/warehouse.html';
        }, desc: 'Sklad' },
        'c': { action: () => {
            window.location.href = '/calendar.html';
        }, desc: 'Kalendář' },
        'h': { action: () => {
            window.location.href = '/';
        }, desc: 'Domů (Dashboard)' },
        'j': { action: () => {
            window.location.href = '/jobs.html';
        }, desc: 'Zakázky' },
        'r': { action: () => {
            window.location.href = '/reports.html';
        }, desc: 'Reporty' },
        '?': { action: () => showShortcutsHelp(), desc: 'Zobrazit zkratky' },
        '/': { action: () => {
            // Focus search input
            const searchInput = document.querySelector('#globalSearch input, .global-search-input, [name="q"]');
            if (searchInput) {
                searchInput.focus();
            } else if (window.openGlobalSearch) {
                window.openGlobalSearch();
            }
        }, desc: 'Vyhledávání' },
        'k': { action: () => {
            if (window.openGlobalSearch) {
                window.openGlobalSearch();
            }
        }, desc: 'Globální vyhledávání', modifier: 'cmd' },
        'Escape': { action: () => {
            // Close any open modals
            document.querySelectorAll('.modal, [data-modal], [role="dialog"]').forEach(m => {
                if (m.style.display !== 'none') {
                    m.style.display = 'none';
                }
            });
            // Blur any focused input
            if (document.activeElement) {
                document.activeElement.blur();
            }
        }, desc: 'Zavřít modal / Zrušit' }
    };

    // Navigation shortcuts (G + key)
    const navShortcuts = {
        'd': { action: () => window.location.href = '/', desc: 'Dashboard' },
        'j': { action: () => window.location.href = '/jobs.html', desc: 'Zakázky' },
        't': { action: () => window.location.href = '/tasks.html', desc: 'Úkoly' },
        'e': { action: () => window.location.href = '/employees.html', desc: 'Team' },
        's': { action: () => window.location.href = '/warehouse.html', desc: 'Sklad' },
        'c': { action: () => window.location.href = '/calendar.html', desc: 'Kalendář' },
        'r': { action: () => window.location.href = '/reports.html', desc: 'Reporty' },
        'n': { action: () => window.location.href = '/nursery.html', desc: 'Školka' },
        'f': { action: () => window.location.href = '/finance.html', desc: 'Finance' },
    };

    let gPressed = false;
    let gTimeout = null;

    function showShortcutsHelp() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: #151a1e;
            border: 1px solid rgba(74, 222, 128, 0.3);
            border-radius: 16px;
            padding: 32px;
            max-width: 700px;
            width: 100%;
            max-height: 85vh;
            overflow-y: auto;
        `;

        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <h2 style="color: #e8eef2; margin: 0; font-size: 24px; display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 28px;">⌨️</span> Klávesové zkratky
                </h2>
                <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" style="
                    background: rgba(255,255,255,0.1);
                    border: none;
                    color: rgba(255,255,255,0.6);
                    font-size: 20px;
                    cursor: pointer;
                    padding: 8px 12px;
                    border-radius: 8px;
                    transition: all 0.2s;
                " onmouseover="this.style.background='rgba(255,255,255,0.2)'" onmouseout="this.style.background='rgba(255,255,255,0.1)'">&times;</button>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
                <div>
                    <h3 style="color: #4ade80; font-size: 14px; margin: 0 0 12px 0; text-transform: uppercase; letter-spacing: 1px;">Navigace</h3>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
        `;

        // Navigation shortcuts
        Object.entries(navShortcuts).forEach(([key, shortcut]) => {
            html += `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: rgba(255,255,255,0.03); border-radius: 8px;">
                    <span style="color: #9ca8b3; font-size: 13px;">${shortcut.desc}</span>
                    <div style="display: flex; gap: 4px;">
                        <kbd style="background: rgba(74, 222, 128, 0.15); border: 1px solid rgba(74, 222, 128, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 11px; color: #4ade80; font-family: monospace;">G</kbd>
                        <kbd style="background: rgba(74, 222, 128, 0.15); border: 1px solid rgba(74, 222, 128, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 11px; color: #4ade80; font-family: monospace;">${key.toUpperCase()}</kbd>
                    </div>
                </div>
            `;
        });

        html += `
                    </div>
                </div>
                <div>
                    <h3 style="color: #4ade80; font-size: 14px; margin: 0 0 12px 0; text-transform: uppercase; letter-spacing: 1px;">Akce</h3>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
        `;

        // Action shortcuts
        const actionShortcuts = ['n', '/', '?', 'Escape'];
        actionShortcuts.forEach(key => {
            const shortcut = shortcuts[key];
            if (shortcut && shortcut.action) {
                const displayKey = key === 'Escape' ? 'Esc' : key === '/' ? '/' : key.toUpperCase();
                html += `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: rgba(255,255,255,0.03); border-radius: 8px;">
                        <span style="color: #9ca8b3; font-size: 13px;">${shortcut.desc}</span>
                        <kbd style="background: rgba(74, 222, 128, 0.15); border: 1px solid rgba(74, 222, 128, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 11px; color: #4ade80; font-family: monospace;">${displayKey}</kbd>
                    </div>
                `;
            }
        });

        html += `
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: rgba(255,255,255,0.03); border-radius: 8px;">
                            <span style="color: #9ca8b3; font-size: 13px;">Globální vyhledávání</span>
                            <div style="display: flex; gap: 4px;">
                                <kbd style="background: rgba(74, 222, 128, 0.15); border: 1px solid rgba(74, 222, 128, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 11px; color: #4ade80; font-family: monospace;">⌘/Ctrl</kbd>
                                <kbd style="background: rgba(74, 222, 128, 0.15); border: 1px solid rgba(74, 222, 128, 0.3); border-radius: 4px; padding: 3px 6px; font-size: 11px; color: #4ade80; font-family: monospace;">K</kbd>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.1); text-align: center;">
                <span style="color: #6b7580; font-size: 12px;">Tip: Stiskni <kbd style="background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 3px; font-size: 11px;">G</kbd> a pak písmeno pro rychlou navigaci</span>
            </div>
        `;

        content.innerHTML = html;
        modal.appendChild(content);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', escHandler);
            }
        });

        document.body.appendChild(modal);
    }

    document.addEventListener('keydown', (e) => {
        // Don't trigger if typing in input/textarea
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.contentEditable === 'true') {
            // Allow Escape even in inputs
            if (e.key === 'Escape') {
                e.target.blur();
            }
            return;
        }

        const key = e.key.toLowerCase();

        // Handle G + key navigation
        if (gPressed && navShortcuts[key]) {
            e.preventDefault();
            navShortcuts[key].action();
            gPressed = false;
            clearTimeout(gTimeout);
            return;
        }

        // Start G sequence
        if (key === 'g' && !e.metaKey && !e.ctrlKey && !e.altKey) {
            gPressed = true;
            clearTimeout(gTimeout);
            gTimeout = setTimeout(() => { gPressed = false; }, 1500);
            return;
        }

        const shortcut = shortcuts[key] || shortcuts[e.key];

        if (shortcut && shortcut.action) {
            // Check for modifier
            if (shortcut.modifier === 'cmd') {
                if (e.metaKey || e.ctrlKey) {
                    e.preventDefault();
                    shortcut.action();
                }
            } else {
                // No modifier needed
                if (!e.metaKey && !e.ctrlKey && !e.altKey && !e.shiftKey) {
                    e.preventDefault();
                    shortcut.action();
                }
            }
        }
    });

    // Show help on first visit
    if (!localStorage.getItem('shortcuts-shown-v2')) {
        setTimeout(() => {
            // Show small toast notification
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                bottom: 24px;
                right: 24px;
                background: rgba(21, 26, 30, 0.95);
                border: 1px solid rgba(74, 222, 128, 0.3);
                border-radius: 12px;
                padding: 16px 20px;
                z-index: 9999;
                display: flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                animation: slideIn 0.3s ease;
            `;
            toast.innerHTML = `
                <span style="font-size: 24px;">⌨️</span>
                <div>
                    <div style="color: #e8eef2; font-size: 14px; font-weight: 500;">Klávesové zkratky</div>
                    <div style="color: #9ca8b3; font-size: 12px;">Stiskni <kbd style="background: rgba(74, 222, 128, 0.2); padding: 2px 6px; border-radius: 3px; color: #4ade80;">?</kbd> pro zobrazení</div>
                </div>
                <button onclick="this.parentElement.remove()" style="background: none; border: none; color: #6b7580; cursor: pointer; padding: 4px; font-size: 18px;">&times;</button>
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 8000);
            localStorage.setItem('shortcuts-shown-v2', 'true');
        }, 5000);
    }

    // Export for external use
    window.showShortcutsHelp = showShortcutsHelp;
})();

