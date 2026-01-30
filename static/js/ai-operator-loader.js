/**
 * AI OPERATOR LOADER
 * ==================
 * Jednoduchý loader pro AI Operator komponenty.
 * Přidej tento script do každé stránky pro aktivaci AI vrstvy.
 */

(function() {
  'use strict';

  // Seznam AI skriptů k načtení
  const scripts = [
    '/static/js/ai-operator-drawer.js',
    '/static/js/ai-operator-inline.js'
  ];

  // Dynamicky načíst skripty
  function loadScript(src) {
    return new Promise((resolve, reject) => {
      // Check if already loaded
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  // Načíst všechny AI skripty
  async function initAIOperator() {
    try {
      for (const src of scripts) {
        await loadScript(src);
      }
      console.log('[AI] Operator loaded successfully');
    } catch (err) {
      console.error('[AI] Failed to load operator:', err);
    }
  }

  // Spustit po načtení DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAIOperator);
  } else {
    initAIOperator();
  }
})();
