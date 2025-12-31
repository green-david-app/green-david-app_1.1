// ========================================
// SETTINGS.JS - Logika pro nastavení
// ========================================

(function() {
  'use strict';
  
  // ========================================
  // STATE & STORAGE
  // ========================================
  
  const defaultSettings = {
    theme: 'dark',
    accentColor: '#4ade80',
    fontSize: 'medium',
    viewMode: 'cards',
    companyName: 'green david',
    companySlogan: 'interní systém',
    brandColor: '#4ade80',
    userName: '',
    userEmail: '',
    userPhone: '',
    userRole: 'employee',
    userLanguage: 'cs',
    notifications: {
      newJobs: true,
      deadlines: true,
      tasks: true,
      team: true,
      dailySummary: false,
      summaryTime: '08:00'
    },
    workPreferences: {
      defaultView: 'dashboard',
      workHours: 8,
      workDays: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
      weekStart: 'monday',
      dateFormat: 'DD.MM.YYYY',
      timezone: 'auto'
    },
    lastExport: null,
    backupFrequency: 'none'
  };
  
  let currentSettings = {};
  
  // ========================================
  // INITIALIZATION
  // ========================================
  
  function init() {
    loadSettings();
    setupEventListeners();
    applySettings();
    setupKeyboardShortcuts();
  }
  
  // ========================================
  // SETTINGS LOAD/SAVE
  // ========================================
  
  function loadSettings() {
    try {
      const saved = localStorage.getItem('appSettings');
      if (saved) {
        currentSettings = { ...defaultSettings, ...JSON.parse(saved) };
      } else {
        currentSettings = { ...defaultSettings };
      }
    } catch (e) {
      console.error('Error loading settings:', e);
      currentSettings = { ...defaultSettings };
    }
  }
  
  function saveSettings() {
    try {
      localStorage.setItem('appSettings', JSON.stringify(currentSettings));
      showSaveIndicator();
      applySettings();
      
      // Dispatch event to notify other pages
      window.dispatchEvent(new Event('settingsUpdated'));
      
      // Also trigger storage event for cross-tab sync
      window.dispatchEvent(new StorageEvent('storage', {
        key: 'appSettings',
        newValue: JSON.stringify(currentSettings)
      }));
    } catch (e) {
      console.error('Error saving settings:', e);
      alert('Chyba při ukládání nastavení');
    }
  }
  
  function showSaveIndicator() {
    const indicator = document.getElementById('saveIndicator');
    indicator.classList.add('show');
    setTimeout(() => {
      indicator.classList.remove('show');
    }, 2000);
  }
  
  // ========================================
  // APPLY SETTINGS
  // ========================================
  
  function applySettings() {
    applyTheme();
    applyAccentColor();
    applyFontSize();
    applyViewMode();
    applyCompanySettings();
    applyUserSettings();
    applyNotifications();
    applyWorkPreferences();
  }
  
  function applyTheme() {
    const isDark = currentSettings.theme === 'dark';
    document.body.style.background = isDark ? '#1a1a1a' : '#ffffff';
    document.body.style.color = isDark ? '#ffffff' : '#0a0e11';
    
    const toggle = document.getElementById('darkModeToggle');
    if (toggle) toggle.checked = isDark;
    
    const icon = document.getElementById('theme-icon');
    if (icon) icon.textContent = isDark ? '🌙' : '☀️';
  }
  
  function applyAccentColor() {
    const color = currentSettings.accentColor;
    document.documentElement.style.setProperty('--accent-green', color);
    
    // Update active color option
    document.querySelectorAll('.color-option').forEach(opt => {
      opt.classList.remove('active');
      if (opt.dataset.hex === color) {
        opt.classList.add('active');
      }
    });
  }
  
  function applyFontSize() {
    const size = currentSettings.fontSize;
    const sizes = { small: '14px', medium: '15px', large: '16px' };
    document.body.style.fontSize = sizes[size] || sizes.medium;
    
    document.querySelectorAll('.size-btn').forEach(btn => {
      btn.classList.remove('active');
      if (btn.dataset.size === size) {
        btn.classList.add('active');
      }
    });
  }
  
  function applyViewMode() {
    const mode = currentSettings.viewMode;
    const select = document.getElementById('viewMode');
    if (select) select.value = mode;
  }
  
  function applyCompanySettings() {
    const nameInput = document.getElementById('companyName');
    const sloganInput = document.getElementById('companySlogan');
    const brandColorInput = document.getElementById('brandColor');
    
    if (nameInput) nameInput.value = currentSettings.companyName || '';
    if (sloganInput) sloganInput.value = currentSettings.companySlogan || '';
    if (brandColorInput) brandColorInput.value = currentSettings.brandColor || '#4ade80';
    
    // Apply to page title
    if (currentSettings.companyName) {
      document.title = `${currentSettings.companyName} — Nastavení`;
    }
  }
  
  function applyUserSettings() {
    const nameInput = document.getElementById('userName');
    const emailInput = document.getElementById('userEmail');
    const phoneInput = document.getElementById('userPhone');
    const roleSelect = document.getElementById('userRole');
    const langSelect = document.getElementById('userLanguage');
    
    if (nameInput) nameInput.value = currentSettings.userName || '';
    if (emailInput) emailInput.value = currentSettings.userEmail || '';
    if (phoneInput) phoneInput.value = currentSettings.userPhone || '';
    if (roleSelect) roleSelect.value = currentSettings.userRole || 'employee';
    if (langSelect) langSelect.value = currentSettings.userLanguage || 'cs';
  }
  
  function applyNotifications() {
    const notifs = currentSettings.notifications || {};
    const checkboxes = {
      notifNewJobs: notifs.newJobs,
      notifDeadlines: notifs.deadlines,
      notifTasks: notifs.tasks,
      notifTeam: notifs.team,
      dailySummary: notifs.dailySummary
    };
    
    Object.entries(checkboxes).forEach(([id, value]) => {
      const checkbox = document.getElementById(id);
      if (checkbox) checkbox.checked = value;
    });
    
    const timeInput = document.getElementById('summaryTime');
    if (timeInput && notifs.summaryTime) {
      timeInput.value = notifs.summaryTime;
    }
  }
  
  function applyWorkPreferences() {
    const prefs = currentSettings.workPreferences || {};
    
    const defaultView = document.getElementById('defaultView');
    if (defaultView) defaultView.value = prefs.defaultView || 'dashboard';
    
    const workHours = document.getElementById('workHours');
    const workHoursValue = document.getElementById('workHoursValue');
    if (workHours) {
      workHours.value = prefs.workHours || 8;
      if (workHoursValue) workHoursValue.textContent = workHours.value;
    }
    
    const weekStart = document.getElementById('weekStart');
    if (weekStart) weekStart.value = prefs.weekStart || 'monday';
    
    const dateFormat = document.getElementById('dateFormat');
    if (dateFormat) dateFormat.value = prefs.dateFormat || 'DD.MM.YYYY';
    
    const timezone = document.getElementById('timezone');
    if (timezone) timezone.value = prefs.timezone || 'auto';
    
    // Apply work days
    const days = prefs.workDays || ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    const dayMap = {
      monday: 'dayMon',
      tuesday: 'dayTue',
      wednesday: 'dayWed',
      thursday: 'dayThu',
      friday: 'dayFri',
      saturday: 'daySat',
      sunday: 'daySun'
    };
    
    Object.entries(dayMap).forEach(([day, id]) => {
      const checkbox = document.getElementById(id);
      if (checkbox) checkbox.checked = days.includes(day);
    });
  }
  
  // ========================================
  // EVENT LISTENERS
  // ========================================
  
  function setupEventListeners() {
    // Theme toggle
    const themeToggle = document.getElementById('darkModeToggle');
    if (themeToggle) {
      themeToggle.addEventListener('change', (e) => {
        currentSettings.theme = e.target.checked ? 'dark' : 'light';
        saveSettings();
      });
    }
    
    // Color picker
    document.querySelectorAll('.color-option').forEach(opt => {
      opt.addEventListener('click', () => {
        currentSettings.accentColor = opt.dataset.hex;
        saveSettings();
      });
    });
    
    // Font size
    document.querySelectorAll('.size-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        currentSettings.fontSize = btn.dataset.size;
        saveSettings();
      });
    });
    
    // View mode
    const viewMode = document.getElementById('viewMode');
    if (viewMode) {
      viewMode.addEventListener('change', (e) => {
        currentSettings.viewMode = e.target.value;
        saveSettings();
      });
    }
    
    // Company settings
    const companyName = document.getElementById('companyName');
    const companySlogan = document.getElementById('companySlogan');
    const brandColor = document.getElementById('brandColor');
    
    if (companyName) {
      companyName.addEventListener('input', debounce(() => {
        currentSettings.companyName = companyName.value;
        saveSettings();
      }, 500));
    }
    
    if (companySlogan) {
      companySlogan.addEventListener('input', debounce(() => {
        currentSettings.companySlogan = companySlogan.value;
        saveSettings();
      }, 500));
    }
    
    if (brandColor) {
      brandColor.addEventListener('change', () => {
        currentSettings.brandColor = brandColor.value;
        saveSettings();
      });
    }
    
    // Logo upload
    const logoUpload = document.getElementById('logoUpload');
    if (logoUpload) {
      logoUpload.addEventListener('change', (e) => {
        handleFileUpload(e.target.files[0], 'logoPreview', (dataUrl) => {
          currentSettings.companyLogo = dataUrl;
          saveSettings();
        });
      });
    }
    
    // Avatar upload
    const avatarUpload = document.getElementById('avatarUpload');
    if (avatarUpload) {
      avatarUpload.addEventListener('change', (e) => {
        handleFileUpload(e.target.files[0], 'avatarPreview', (dataUrl) => {
          currentSettings.userAvatar = dataUrl;
          saveSettings();
        });
      });
    }
    
    // User settings
    const userName = document.getElementById('userName');
    const userEmail = document.getElementById('userEmail');
    const userPhone = document.getElementById('userPhone');
    const userRole = document.getElementById('userRole');
    const userLanguage = document.getElementById('userLanguage');
    
    if (userName) {
      userName.addEventListener('input', debounce(() => {
        currentSettings.userName = userName.value;
        saveSettings();
      }, 500));
    }
    
    if (userEmail) {
      userEmail.addEventListener('input', debounce(() => {
        if (validateEmail(userEmail.value)) {
          currentSettings.userEmail = userEmail.value;
          saveSettings();
        }
      }, 500));
    }
    
    if (userPhone) {
      userPhone.addEventListener('input', debounce(() => {
        currentSettings.userPhone = userPhone.value;
        saveSettings();
      }, 500));
    }
    
    if (userRole) {
      userRole.addEventListener('change', (e) => {
        currentSettings.userRole = e.target.value;
        saveSettings();
      });
    }
    
    if (userLanguage) {
      userLanguage.addEventListener('change', (e) => {
        currentSettings.userLanguage = e.target.value;
        saveSettings();
      });
    }
    
    // Notifications
    const notifIds = ['notifNewJobs', 'notifDeadlines', 'notifTasks', 'notifTeam', 'dailySummary'];
    notifIds.forEach(id => {
      const checkbox = document.getElementById(id);
      if (checkbox) {
        checkbox.addEventListener('change', () => {
          if (!currentSettings.notifications) currentSettings.notifications = {};
          const key = id.replace('notif', '').toLowerCase();
          currentSettings.notifications[key] = checkbox.checked;
          saveSettings();
        });
      }
    });
    
    const summaryTime = document.getElementById('summaryTime');
    if (summaryTime) {
      summaryTime.addEventListener('change', () => {
        if (!currentSettings.notifications) currentSettings.notifications = {};
        currentSettings.notifications.summaryTime = summaryTime.value;
        saveSettings();
      });
    }
    
    // Work preferences
    const defaultView = document.getElementById('defaultView');
    if (defaultView) {
      defaultView.addEventListener('change', (e) => {
        if (!currentSettings.workPreferences) currentSettings.workPreferences = {};
        currentSettings.workPreferences.defaultView = e.target.value;
        saveSettings();
      });
    }
    
    const workHours = document.getElementById('workHours');
    const workHoursValue = document.getElementById('workHoursValue');
    if (workHours) {
      workHours.addEventListener('input', (e) => {
        if (!currentSettings.workPreferences) currentSettings.workPreferences = {};
        currentSettings.workPreferences.workHours = parseInt(e.target.value);
        if (workHoursValue) workHoursValue.textContent = e.target.value;
        saveSettings();
      });
    }
    
    const weekStart = document.getElementById('weekStart');
    if (weekStart) {
      weekStart.addEventListener('change', (e) => {
        if (!currentSettings.workPreferences) currentSettings.workPreferences = {};
        currentSettings.workPreferences.weekStart = e.target.value;
        saveSettings();
      });
    }
    
    const dateFormat = document.getElementById('dateFormat');
    if (dateFormat) {
      dateFormat.addEventListener('change', (e) => {
        if (!currentSettings.workPreferences) currentSettings.workPreferences = {};
        currentSettings.workPreferences.dateFormat = e.target.value;
        saveSettings();
      });
    }
    
    const timezone = document.getElementById('timezone');
    if (timezone) {
      timezone.addEventListener('change', (e) => {
        if (!currentSettings.workPreferences) currentSettings.workPreferences = {};
        currentSettings.workPreferences.timezone = e.target.value;
        saveSettings();
      });
    }
    
    // Work days
    const dayIds = ['dayMon', 'dayTue', 'dayWed', 'dayThu', 'dayFri', 'daySat', 'daySun'];
    const dayMap = {
      dayMon: 'monday',
      dayTue: 'tuesday',
      dayWed: 'wednesday',
      dayThu: 'thursday',
      dayFri: 'friday',
      daySat: 'saturday',
      daySun: 'sunday'
    };
    
    dayIds.forEach(id => {
      const checkbox = document.getElementById(id);
      if (checkbox) {
        checkbox.addEventListener('change', () => {
          if (!currentSettings.workPreferences) currentSettings.workPreferences = {};
          if (!currentSettings.workPreferences.workDays) {
            currentSettings.workPreferences.workDays = [];
          }
          
          const day = dayMap[id];
          if (checkbox.checked) {
            if (!currentSettings.workPreferences.workDays.includes(day)) {
              currentSettings.workPreferences.workDays.push(day);
            }
          } else {
            currentSettings.workPreferences.workDays = 
              currentSettings.workPreferences.workDays.filter(d => d !== day);
          }
          saveSettings();
        });
      }
    });
    
    // Action buttons
    const exportBtn = document.getElementById('exportDataBtn');
    if (exportBtn) {
      exportBtn.addEventListener('click', exportData);
    }
    
    const importData = document.getElementById('importData');
    if (importData) {
      importData.addEventListener('change', (e) => {
        handleCSVImport(e.target.files[0]);
      });
    }
    
    const createBackupBtn = document.getElementById('createBackupBtn');
    if (createBackupBtn) {
      createBackupBtn.addEventListener('click', createBackup);
    }
    
    const backupFrequency = document.getElementById('backupFrequency');
    if (backupFrequency) {
      backupFrequency.addEventListener('change', (e) => {
        currentSettings.backupFrequency = e.target.value;
        saveSettings();
      });
    }
    
    const clearCacheBtn = document.getElementById('clearCacheBtn');
    if (clearCacheBtn) {
      clearCacheBtn.addEventListener('click', clearCache);
    }
    
    const changePasswordBtn = document.getElementById('changePasswordBtn');
    if (changePasswordBtn) {
      changePasswordBtn.addEventListener('click', () => {
        const newPassword = prompt('Zadejte nové heslo:');
        if (newPassword) {
          // TODO: Implement password change
          alert('Změna hesla bude implementována');
        }
      });
    }
    
    const downloadGDPRBtn = document.getElementById('downloadGDPRBtn');
    if (downloadGDPRBtn) {
      downloadGDPRBtn.addEventListener('click', downloadGDPRData);
    }
    
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    if (deleteAccountBtn) {
      deleteAccountBtn.addEventListener('click', () => {
        if (confirm('Opravdu chcete smazat svůj účet? Tato akce je nevratná!')) {
          if (confirm('Jste si opravdu jisti? Všechna vaše data budou trvale smazána.')) {
            deleteAccount();
          }
        }
      });
    }
    
    const resetSettingsBtn = document.getElementById('resetSettingsBtn');
    if (resetSettingsBtn) {
      resetSettingsBtn.addEventListener('click', () => {
        if (confirm('Obnovit všechna nastavení na výchozí hodnoty?')) {
          resetSettings();
        }
      });
    }
    
    // Load login history and sessions
    loadLoginHistory();
    loadActiveSessions();
  }
  
  // ========================================
  // UTILITY FUNCTIONS
  // ========================================
  
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
  
  function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
  
  function handleFileUpload(file, previewId, callback) {
    if (!file) return;
    
    // Validate file type
    if (!file.type.match(/^image\/(jpeg|png)$/)) {
      alert('Pouze JPG a PNG soubory jsou podporovány');
      return;
    }
    
    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('Soubor je příliš velký. Maximální velikost je 5MB');
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = document.getElementById(previewId);
      if (preview) {
        preview.src = e.target.result;
        preview.style.display = 'block';
      }
      if (callback) callback(e.target.result);
    };
    reader.readAsDataURL(file);
  }
  
  function exportData() {
    try {
      const data = {
        settings: currentSettings,
        exportDate: new Date().toISOString()
      };
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `green-david-export-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      
      currentSettings.lastExport = new Date().toISOString();
      saveSettings();
      
      const lastExport = document.getElementById('lastExport');
      if (lastExport) {
        lastExport.textContent = new Date().toLocaleString('cs-CZ');
      }
      
      alert('Data byla úspěšně exportována');
    } catch (e) {
      console.error('Export error:', e);
      alert('Chyba při exportu dat');
    }
  }
  
  function handleCSVImport(file) {
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const csv = e.target.result;
        // TODO: Implement CSV parsing and mapping
        alert('Import CSV bude implementován');
      } catch (e) {
        alert('Chyba při importu CSV souboru');
      }
    };
    reader.readAsText(file);
  }
  
  function createBackup() {
    try {
      const backup = {
        settings: currentSettings,
        timestamp: new Date().toISOString()
      };
      
      localStorage.setItem('appBackup', JSON.stringify(backup));
      alert('Záloha byla úspěšně vytvořena');
    } catch (e) {
      alert('Chyba při vytváření zálohy');
    }
  }
  
  function clearCache() {
    if (confirm('Opravdu chcete vymazat cache?')) {
      // Clear service worker cache if exists
      if ('caches' in window) {
        caches.keys().then(names => {
          names.forEach(name => caches.delete(name));
        });
      }
      alert('Cache byla vymazána');
    }
  }
  
  function downloadGDPRData() {
    try {
      const gdprData = {
        user: {
          name: currentSettings.userName,
          email: currentSettings.userEmail,
          phone: currentSettings.userPhone
        },
        settings: currentSettings,
        exportDate: new Date().toISOString()
      };
      
      const blob = new Blob([JSON.stringify(gdprData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `gdpr-data-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      
      alert('Vaše data byla stažena');
    } catch (e) {
      alert('Chyba při stahování dat');
    }
  }
  
  function deleteAccount() {
    // TODO: Implement account deletion
    alert('Smazání účtu bude implementováno');
  }
  
  function resetSettings() {
    currentSettings = { ...defaultSettings };
    saveSettings();
    location.reload();
  }
  
  function loadLoginHistory() {
    // TODO: Load from API
    const history = document.getElementById('loginHistory');
    if (history) {
      history.innerHTML = 'Poslední přihlášení: ' + new Date().toLocaleString('cs-CZ');
    }
  }
  
  function loadActiveSessions() {
    // TODO: Load from API
    const sessions = document.getElementById('activeSessions');
    if (sessions) {
      sessions.innerHTML = 'Aktivní session: Tento prohlížeč';
    }
  }
  
  // ========================================
  // KEYBOARD SHORTCUTS
  // ========================================
  
  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl+S or Cmd+S to save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveSettings();
      }
    });
  }
  
  // ========================================
  // INIT ON LOAD
  // ========================================
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
})();

