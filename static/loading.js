function showLoading(message = 'Načítám...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.8);
        backdrop-filter: blur(4px);
        z-index: 9998;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 16px;
    `;
    
    overlay.innerHTML = `
        <div style="
            width: 50px;
            height: 50px;
            border: 4px solid rgba(176, 251, 165, 0.3);
            border-top-color: #b0fba5;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        "></div>
        <div style="color: #fff; font-size: 16px;">${message}</div>
    `;
    
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => overlay.remove(), 300);
    }
}

// Animation
const loadingStyleEl = document.createElement('style');
loadingStyleEl.textContent = `
@keyframes spin {
    to { transform: rotate(360deg); }
}

@keyframes fadeOut {
    to { opacity: 0; }
}
`;
loadingStyleEl.id = 'loading-style';
if (!document.getElementById('loading-style')) document.head.appendChild(loadingStyleEl);

window.showLoading = showLoading;
window.hideLoading = hideLoading;

