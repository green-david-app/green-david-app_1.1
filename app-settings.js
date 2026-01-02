// ========================================
// APP-SETTINGS.JS - Globální aplikace nastavení
// Načte se na všech stránkách a aplikuje nastavení
// ========================================

(function() {
  'use strict';
  
  // ========================================
  // LOAD SETTINGS
  // ========================================
  
  function loadAppSettings() {
    try {
      const saved = localStorage.getItem('appSettings');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.error('Error loading app settings:', e);
    }
    return null;
  }
  
  // ========================================
  // APPLY SETTINGS GLOBALLY
  // ========================================
  
  function applyGlobalSettings() {
    const settings = loadAppSettings();
    if (!settings) return;
    
    // Apply theme
    if (settings.theme) {
      applyTheme(settings.theme);
    }
    
    // Apply accent color
    if (settings.accentColor) {
      applyAccentColor(settings.accentColor);
    }
    
    // Apply font size
    if (settings.fontSize) {
      applyFontSize(settings.fontSize);
    }
    
    // Apply company settings
    if (settings.companyName) {
      applyCompanyName(settings.companyName);
    }
    
    if (settings.companyLogo) {
      applyCompanyLogo(settings.companyLogo);
    }
    
    if (settings.brandColor) {
      applyBrandColor(settings.brandColor);
    }
  }
  
  function applyTheme(theme) {
    const isDark = theme === 'dark';
    document.documentElement.setAttribute('data-theme', theme);
    
    if (isDark) {
      document.body.style.background = '#1a1a1a';
      document.body.style.color = '#ffffff';
    } else {
      document.body.style.background = '#ffffff';
      document.body.style.color = '#0a0e11';
    }
    
    // Apply to all cards
    document.querySelectorAll('.card, .settings-card').forEach(card => {
      if (isDark) {
        card.style.background = '#1f2428';
        card.style.color = '#ffffff';
      } else {
        card.style.background = '#ffffff';
        card.style.color = '#0a0e11';
      }
    });
  }
  
  function applyAccentColor(color) {
    document.documentElement.style.setProperty('--accent-green', color);
    document.documentElement.style.setProperty('--mint', color);
    
    // Update all buttons and links
    document.querySelectorAll('.btn-primary, .nav-item.active').forEach(el => {
      el.style.color = color;
    });
  }
  
  function applyFontSize(size) {
    const sizes = { small: '14px', medium: '15px', large: '16px' };
    document.body.style.fontSize = sizes[size] || sizes.medium;
  }
  
  function applyCompanyName(name) {
    // Update page title
    const title = document.querySelector('title');
    if (title && !title.textContent.includes('Nastavení')) {
      const currentTitle = title.textContent.split('—')[1] || '';
      title.textContent = `${name}${currentTitle ? ' — ' + currentTitle.trim() : ''}`;
    }
    
    // Update header brand name
    const brandNames = document.querySelectorAll('.brand-title, [class*="brand"]');
    brandNames.forEach(el => {
      if (el.textContent.includes('green david')) {
        el.textContent = name;
      }
    });
  }
  
  function applyCompanyLogo(logoDataUrl) {
    const logos = document.querySelectorAll('img[src*="logo"], .brand-logo, header img');
    logos.forEach(img => {
      img.src = logoDataUrl;
      img.onerror = function() {
        this.src = '/logo.svg';
      };
    });
  }
  
  function applyBrandColor(color) {
    document.documentElement.style.setProperty('--brand-color', color);
  }
  
  // ========================================
  // LISTEN FOR SETTINGS CHANGES
  // ========================================
  
  function setupSettingsListener() {
    // Listen for storage events (when settings change in another tab)
    window.addEventListener('storage', (e) => {
      if (e.key === 'appSettings') {
        applyGlobalSettings();
      }
    });
    
    // Custom event for same-tab updates
    window.addEventListener('settingsUpdated', () => {
      applyGlobalSettings();
    });
  }
  
  // ========================================
  // INIT
  // ========================================
  
  function init() {
    applyGlobalSettings();
    setupSettingsListener();
  }
  
  // Run immediately
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Export for use in other scripts
  window.AppSettings = {
    load: loadAppSettings,
    apply: applyGlobalSettings
  };
  
})();





