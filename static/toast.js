class ToastManager {
    constructor() {
        this.container = this.createContainer();
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
        `;
        document.body.appendChild(container);
        return container;
    }
    
    show(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const colors = {
            success: '#b0fba5',
            error: '#f87171',
            warning: '#fb923c',
            info: '#60a5fa'
        };
        
        toast.style.cssText = `
            background: rgba(26, 26, 26, 0.95);
            border: 1px solid ${colors[type]};
            border-left: 4px solid ${colors[type]};
            border-radius: 8px;
            padding: 16px;
            min-width: 300px;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s ease;
        `;
        
        toast.innerHTML = `
            <span style="font-size: 20px;">${icons[type]}</span>
            <span style="color: #fff; flex: 1;">${message}</span>
            <button onclick="this.parentElement.remove()" style="
                background: none;
                border: none;
                color: rgba(255,255,255,0.6);
                cursor: pointer;
                font-size: 18px;
            ">&times;</button>
        `;
        
        this.container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Global instance
window.toast = new ToastManager();

// Helper functions
window.showToast = (msg, type) => window.toast.show(msg, type);

// CSS Animation
const toastStyleEl = document.createElement('style');
toastStyleEl.textContent = `
@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(400px);
        opacity: 0;
    }
}
`;
toastStyleEl.id = 'toast-style';
if (!document.getElementById('toast-style')) document.head.appendChild(toastStyleEl);

