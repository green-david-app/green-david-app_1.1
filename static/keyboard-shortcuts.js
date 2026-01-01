// Global Keyboard Shortcuts
(function() {
    const shortcuts = {
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
        }, desc: 'Nový úkol' },
        'e': { action: () => {
            window.location.href = '/timesheets.html';
        }, desc: 'Nový výkaz' },
        '?': { action: () => showShortcutsHelp(), desc: 'Zobrazit zkratky' },
        'k': { action: () => {
            if (window.openGlobalSearch) {
                window.openGlobalSearch();
            }
        }, desc: 'Vyhledávání', modifier: 'cmd' }
    };

    function showShortcutsHelp() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(8px);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: #1a1a1a;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 32px;
            max-width: 500px;
            width: 100%;
            max-height: 80vh;
            overflow-y: auto;
        `;

        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <h2 style="color: #fff; margin: 0; font-size: 24px;">⌨️ Klávesové zkratky</h2>
                <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" style="
                    background: none;
                    border: none;
                    color: rgba(255,255,255,0.6);
                    font-size: 28px;
                    cursor: pointer;
                    padding: 0;
                    width: 32px;
                    height: 32px;
                ">&times;</button>
            </div>
            <div style="display: flex; flex-direction: column; gap: 12px;">
        `;

        Object.keys(shortcuts).forEach(key => {
            const shortcut = shortcuts[key];
            const modifier = shortcut.modifier === 'cmd' ? '⌘' : '';
            html += `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px;">
                    <span style="color: #fff;">${shortcut.desc}</span>
                    <kbd style="
                        background: rgba(255,255,255,0.1);
                        border: 1px solid rgba(255,255,255,0.2);
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-size: 12px;
                        color: #b0fba5;
                        font-family: monospace;
                    ">${modifier}${key.toUpperCase()}</kbd>
                </div>
            `;
        });

        html += `
                <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.1);">
                    <div style="color: rgba(255,255,255,0.6); font-size: 12px;">
                        <strong style="color: #fff;">Esc</strong> - Zavřít modaly<br>
                        <strong style="color: #fff;">⌘K / Ctrl+K</strong> - Globální vyhledávání
                    </div>
                </div>
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
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        const key = e.key.toLowerCase();
        const shortcut = shortcuts[key];

        if (shortcut) {
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
    if (!localStorage.getItem('shortcuts-shown')) {
        setTimeout(() => {
            if (window.showToast) {
                showToast('Tip: Stiskněte ? pro zobrazení klávesových zkratek', 'info');
            }
            localStorage.setItem('shortcuts-shown', 'true');
        }, 3000);
    }
})();

