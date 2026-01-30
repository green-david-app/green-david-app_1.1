// ========================================
// APP-SETTINGS.JS - Globální aplikace nastavení
// Načte se na všech stránkách a aplikuje nastavení
// ========================================

(function() {
  'use strict';


  // ========================================
  // I18N (CZ/EN) - prepared for future languages
  // - Source of truth: localStorage appSettings.userLanguage
  // - Default: cs
  // - Missing keys fall back to Czech
  // ========================================

  const I18N_DICT = {
    cs: {
      // Navigation
      'nav.home': 'Domů',
      'nav.jobs': 'Zakázky',
      'nav.timesheets': 'Výkazy',
      'nav.calendar': 'Kalendář',
      'nav.reports': 'Přehledy',
      'nav.more': 'Více',
      'more.title': 'Navigace',
      'more.dashboard': 'přehled',
      'more.inbox': 'moje práce',
      'more.calendar': 'kalendář',
      'more.timesheets': 'výkazy hodin',
      'more.jobs': 'zakázky',
      'more.tasks': 'úkoly',
      'more.employees': 'zaměstnanci',
      'more.warehouse': 'sklad',
      'more.finance': 'finance',
      'more.documents': 'dokumenty',
      'more.reports': 'reporty',
      'more.archive': 'archiv',
      'more.settings': 'nastavení',
      'inbox.link': 'Moje práce',
      'inbox.sub': 'Work inbox',
      'settings.language': 'Preferovaný jazyk',
      
      // Home page quick actions
      'home.quick.new_job': 'Nová zakázka',
      'home.quick.timesheet': 'Výkaz hodin',
      'home.quick.create': 'Vytvořit',
      'home.quick.add_time': 'Přidat čas',
      'home.quick.overview': 'Přehled',
      'home.quick.team': 'Tým',
      'home.quick.manage': 'Spravovat',
      'home.quick.statistics': 'Statistiky',
      'home.quick.reports': 'Přehledy',
      
      // Common actions
      'action.add': 'Přidat',
      'action.edit': 'Upravit',
      'action.delete': 'Smazat',
      'action.save': 'Uložit',
      'action.cancel': 'Zrušit',
      'action.close': 'Zavřít',
      'action.refresh': 'Obnovit',
      'action.export': 'Export',
      'action.import': 'Import',
      'action.search': 'Hledat',
      'action.filter': 'Filtr',
      'action.clear': 'Vymazat',
      'action.new': 'Nový',
      'action.create': 'Vytvořit',
      'action.update': 'Aktualizovat',
      'action.submit': 'Odeslat',
      
      // Timesheets
      'timesheets.title': 'Výkazy hodin',
      'timesheets.add': 'Přidat záznam',
      'timesheets.refresh': 'Obnovit',
      'timesheets.export.csv': 'Export CSV',
      'timesheets.export.xlsx': 'Export XLSX',
      'timesheets.filter.from': 'Od',
      'timesheets.filter.to': 'Do',
      'timesheets.filter.employee': 'Zaměstnanec',
      'timesheets.filter.job': 'Zakázka',
      'timesheets.filter.text': 'Text',
      'timesheets.filter.placeholder': 'poznámka, název…',
      'timesheets.col.date': 'Datum',
      'timesheets.col.employee': 'Zaměstnanec',
      'timesheets.col.job': 'Zakázka',
      'timesheets.col.hours': 'Hodiny',
      'timesheets.col.note': 'Poznámka',
      'timesheets.col.actions': 'Akce',
      'timesheets.total': 'Celkem',
      'timesheets.delete': 'Smazat',
      'timesheets.no_data': 'Žádné záznamy',
      'timesheets.view.list': 'Seznam',
      'timesheets.view.timeline': 'Timeline',
      'timesheets.view.stats': 'Statistiky',
      'timesheets.nav.previous': '← Předchozí',
      'timesheets.nav.next': 'Další →',
      'timesheets.bulk_actions': 'Hromadné akce',
      'timesheets.copy_week': 'Kopírovat týden',
      
      // Jobs
      'jobs.title': 'Zakázky',
      'jobs.view.kanban': 'Kanban',
      'jobs.view.list': 'Seznam',
      'jobs.view.timeline': 'Timeline',
      'jobs.add': 'Nová zakázka',
      'jobs.edit': 'Upravit zakázku',
      'jobs.delete': 'Smazat zakázku',
      'jobs.details': 'Detail zakázky',
      'jobs.col.name': 'Název',
      'jobs.col.description': 'Popis',
      'jobs.col.status': 'Status',
      'jobs.col.priority': 'Priorita',
      'jobs.col.budget': 'Rozpočet',
      'jobs.col.client': 'Zadavatel',
      'jobs.col.start': 'Začátek',
      'jobs.col.end': 'Konec',
      'jobs.col.deadline': 'Termín',
      'jobs.status.new': 'Nová',
      'jobs.status.in_progress': 'Probíhá',
      'jobs.status.waiting': 'Čeká',
      'jobs.status.paused': 'Pozastaveno',
      'jobs.status.done': 'Hotovo',
      'jobs.status.cancelled': 'Zrušeno',
      'jobs.priority.low': 'Nízká',
      'jobs.priority.medium': 'Střední',
      'jobs.priority.high': 'Vysoká',
      'jobs.priority.urgent': 'Urgentní',
      'jobs.section.tasks': 'Úkoly',
      'jobs.section.issues': 'Issues',
      'jobs.section.info': 'Informace',
      'jobs.section.description': 'Popis',
      'jobs.section.files': 'Soubory',
      'jobs.section.notes': 'Poznámky',
      'jobs.no_jobs': 'Žádné zakázky',
      'jobs.stats.total_value': 'Celková hodnota aktivních',
      'jobs.stats.deadline': 'Blížící se deadline',
      'jobs.stats.jobs_count': 'zakázek',
      'jobs.stats.top3': 'Top 3 projekty',
      'jobs.stats.this_week': 'tento týden',
      'jobs.stats.trend': 'Trend',
      
      // Tasks
      'tasks.title': 'Úkoly',
      'tasks.add': 'Nový úkol',
      'tasks.edit': 'Upravit úkol',
      'tasks.delete': 'Smazat úkol',
      'tasks.details': 'Detail úkolu',
      'tasks.col.name': 'Název',
      'tasks.col.description': 'Popis',
      'tasks.col.status': 'Status',
      'tasks.col.priority': 'Priorita',
      'tasks.col.assigned': 'Přiřazen',
      'tasks.col.deadline': 'Termín',
      'tasks.col.created': 'Vytvořeno',
      'tasks.col.updated': 'Upraveno',
      'tasks.status.todo': 'K provedení',
      'tasks.status.in_progress': 'Probíhá',
      'tasks.status.done': 'Hotovo',
      'tasks.status.cancelled': 'Zrušeno',
      'tasks.priority.low': 'Nízká',
      'tasks.priority.medium': 'Střední',
      'tasks.priority.high': 'Vysoká',
      'tasks.section.info': 'Informace',
      'tasks.section.description': 'Popis',
      'tasks.section.comments': 'Komentáře',
      'tasks.section.attachments': 'Přílohy',
      'tasks.no_tasks': 'Žádné úkoly',
      'tasks.add_comment': 'Přidat komentář',
      'tasks.my_issues': 'Moje Issues',
      'tasks.show_issues': '🚨 Zobrazit Issues',
      'tasks.filter.all': 'Všechny',
      'tasks.filter.my': 'Moje úkoly',
      'tasks.filter.high': '🔴 Vysoká priorita',
      'tasks.filter.today': 'Dnes',
      'tasks.placeholder.name': 'Název úkolu',
      'tasks.placeholder.desc': 'Popis',
      'tasks.placeholder.deadline': 'Deadline',
      'tasks.placeholder.assignee': 'Vyberte zaměstnance',
      
      // Issues
      'issues.title': 'Issues',
      'issues.add': 'Nový issue',
      'issues.edit': 'Upravit issue',
      'issues.delete': 'Smazat issue',
      'issues.details': 'Detail issue',
      'issues.col.name': 'Název',
      'issues.col.description': 'Popis',
      'issues.col.type': 'Typ',
      'issues.col.status': 'Status',
      'issues.col.priority': 'Priorita',
      'issues.col.assigned': 'Přiřazen',
      'issues.col.created': 'Vytvořeno',
      'issues.type.bug': 'Bug',
      'issues.type.feature': 'Feature',
      'issues.type.improvement': 'Vylepšení',
      'issues.type.task': 'Úkol',
      'issues.type.question': 'Dotaz',
      'issues.status.open': 'Otevřeno',
      'issues.status.in_progress': 'Probíhá',
      'issues.status.resolved': 'Vyřešeno',
      'issues.status.closed': 'Uzavřeno',
      'issues.priority.low': 'Nízká',
      'issues.priority.medium': 'Střední',
      'issues.priority.high': 'Vysoká',
      'issues.priority.critical': 'Kritická',
      'issues.no_issues': 'Žádné issues',
      'issues.filter.all': 'Vše',
      'issues.filter.all_types': 'Všechny typy',
      'issues.type.blocker': 'Blokuje',
      'issues.type.todo': 'To-Do',
      'issues.type.note': 'Poznámka',
      'issues.stats.blockers': 'Blokující',
      'issues.stats.in_progress': 'Řeší se',
      'issues.stats.resolved_today': 'Vyřešené dnes',
      'issues.assigned_to_me': 'Přiřazené mně',
      'issues.all': 'Všechny issues',
      
      // Common fields
      'field.name': 'Název',
      'field.description': 'Popis',
      'field.status': 'Status',
      'field.priority': 'Priorita',
      'field.date': 'Datum',
      'field.time': 'Čas',
      'field.hours': 'Hodiny',
      'field.note': 'Poznámka',
      'field.notes': 'Poznámky',
      'field.comment': 'Komentář',
      'field.comments': 'Komentáře',
      'field.assigned': 'Přiřazen',
      'field.assignee': 'Zodpovědná osoba',
      'field.created': 'Vytvořeno',
      'field.updated': 'Upraveno',
      'field.deadline': 'Termín',
      'field.budget': 'Rozpočet',
      'field.client': 'Klient',
      'field.employee': 'Zaměstnanec',
      'field.job': 'Zakázka',
      'field.task': 'Úkol',
      'field.issue': 'Issue',
      'field.file': 'Soubor',
      'field.files': 'Soubory',
      'field.attachment': 'Příloha',
      'field.attachments': 'Přílohy',
      
      // Messages
      'msg.confirm_delete': 'Opravdu smazat?',
      'msg.saved': 'Uloženo',
      'msg.deleted': 'Smazáno',
      'msg.error': 'Chyba',
      'msg.success': 'Úspěch',
      'msg.loading': 'Načítání...',
      'msg.no_data': 'Žádná data',
      'msg.required': 'Povinné pole',
    },
    en: {
      // Navigation
      'nav.home': 'Home',
      'nav.jobs': 'Jobs',
      'nav.timesheets': 'Timesheets',
      'nav.calendar': 'Calendar',
      'nav.reports': 'Reports',
      'nav.more': 'More',
      'more.title': 'Navigation',
      'more.dashboard': 'dashboard',
      'more.inbox': 'my work',
      'more.calendar': 'calendar',
      'more.timesheets': 'timesheets',
      'more.jobs': 'jobs',
      'more.tasks': 'tasks',
      'more.employees': 'employees',
      'more.warehouse': 'warehouse',
      'more.finance': 'finance',
      'more.documents': 'documents',
      'more.reports': 'reports',
      'more.archive': 'archive',
      'more.settings': 'settings',
      'inbox.link': 'My work',
      'inbox.sub': 'Work inbox',
      'settings.language': 'Preferred language',
      
      // Home page quick actions
      'home.quick.new_job': 'New job',
      'home.quick.timesheet': 'Timesheet',
      'home.quick.create': 'Create',
      'home.quick.add_time': 'Add time',
      'home.quick.overview': 'Overview',
      'home.quick.team': 'Team',
      'home.quick.manage': 'Manage',
      'home.quick.statistics': 'Statistics',
      'home.quick.reports': 'Reports',
      
      // Common actions
      'action.add': 'Add',
      'action.edit': 'Edit',
      'action.delete': 'Delete',
      'action.save': 'Save',
      'action.cancel': 'Cancel',
      'action.close': 'Close',
      'action.refresh': 'Refresh',
      'action.export': 'Export',
      'action.import': 'Import',
      'action.search': 'Search',
      'action.filter': 'Filter',
      'action.clear': 'Clear',
      'action.new': 'New',
      'action.create': 'Create',
      'action.update': 'Update',
      'action.submit': 'Submit',
      
      // Timesheets
      'timesheets.title': 'Timesheets',
      'timesheets.add': 'Add entry',
      'timesheets.refresh': 'Refresh',
      'timesheets.export.csv': 'Export CSV',
      'timesheets.export.xlsx': 'Export XLSX',
      'timesheets.filter.from': 'From',
      'timesheets.filter.to': 'To',
      'timesheets.filter.employee': 'Employee',
      'timesheets.filter.job': 'Job',
      'timesheets.filter.text': 'Text',
      'timesheets.filter.placeholder': 'note, name…',
      'timesheets.col.date': 'Date',
      'timesheets.col.employee': 'Employee',
      'timesheets.col.job': 'Job',
      'timesheets.col.hours': 'Hours',
      'timesheets.col.note': 'Note',
      'timesheets.col.actions': 'Actions',
      'timesheets.total': 'Total',
      'timesheets.delete': 'Delete',
      'timesheets.no_data': 'No entries',
      'timesheets.view.list': 'List',
      'timesheets.view.timeline': 'Timeline',
      'timesheets.view.stats': 'Statistics',
      'timesheets.nav.previous': '← Previous',
      'timesheets.nav.next': 'Next →',
      'timesheets.bulk_actions': 'Bulk actions',
      'timesheets.copy_week': 'Copy week',
      
      // Jobs
      'jobs.title': 'Jobs',
      'jobs.view.kanban': 'Kanban',
      'jobs.view.list': 'List',
      'jobs.view.timeline': 'Timeline',
      'jobs.add': 'New job',
      'jobs.edit': 'Edit job',
      'jobs.delete': 'Delete job',
      'jobs.details': 'Job details',
      'jobs.col.name': 'Name',
      'jobs.col.description': 'Description',
      'jobs.col.status': 'Status',
      'jobs.col.priority': 'Priority',
      'jobs.col.budget': 'Budget',
      'jobs.col.client': 'Client',
      'jobs.col.start': 'Start',
      'jobs.col.end': 'End',
      'jobs.col.deadline': 'Deadline',
      'jobs.status.new': 'New',
      'jobs.status.in_progress': 'In Progress',
      'jobs.status.waiting': 'Waiting',
      'jobs.status.paused': 'Paused',
      'jobs.status.done': 'Done',
      'jobs.status.cancelled': 'Cancelled',
      'jobs.priority.low': 'Low',
      'jobs.priority.medium': 'Medium',
      'jobs.priority.high': 'High',
      'jobs.priority.urgent': 'Urgent',
      'jobs.section.tasks': 'Tasks',
      'jobs.section.issues': 'Issues',
      'jobs.section.info': 'Information',
      'jobs.section.description': 'Description',
      'jobs.section.files': 'Files',
      'jobs.section.notes': 'Notes',
      'jobs.no_jobs': 'No jobs',
      'jobs.stats.total_value': 'Total value of active',
      'jobs.stats.deadline': 'Approaching deadline',
      'jobs.stats.jobs_count': 'jobs',
      'jobs.stats.top3': 'Top 3 projects',
      'jobs.stats.this_week': 'this week',
      'jobs.stats.trend': 'Trend',
      
      // Tasks
      'tasks.title': 'Tasks',
      'tasks.add': 'New task',
      'tasks.edit': 'Edit task',
      'tasks.delete': 'Delete task',
      'tasks.details': 'Task details',
      'tasks.col.name': 'Name',
      'tasks.col.description': 'Description',
      'tasks.col.status': 'Status',
      'tasks.col.priority': 'Priority',
      'tasks.col.assigned': 'Assigned',
      'tasks.col.deadline': 'Deadline',
      'tasks.col.created': 'Created',
      'tasks.col.updated': 'Updated',
      'tasks.status.todo': 'To Do',
      'tasks.status.in_progress': 'In Progress',
      'tasks.status.done': 'Done',
      'tasks.status.cancelled': 'Cancelled',
      'tasks.priority.low': 'Low',
      'tasks.priority.medium': 'Medium',
      'tasks.priority.high': 'High',
      'tasks.section.info': 'Information',
      'tasks.section.description': 'Description',
      'tasks.section.comments': 'Comments',
      'tasks.section.attachments': 'Attachments',
      'tasks.no_tasks': 'No tasks',
      'tasks.add_comment': 'Add comment',
      'tasks.my_issues': 'My Issues',
      'tasks.show_issues': '🚨 Show Issues',
      'tasks.filter.all': 'All',
      'tasks.filter.my': 'My tasks',
      'tasks.filter.high': '🔴 High priority',
      'tasks.filter.today': 'Today',
      'tasks.placeholder.name': 'Task name',
      'tasks.placeholder.desc': 'Description',
      'tasks.placeholder.deadline': 'Deadline',
      'tasks.placeholder.assignee': 'Select employee',
      
      // Issues
      'issues.title': 'Issues',
      'issues.add': 'New issue',
      'issues.edit': 'Edit issue',
      'issues.delete': 'Delete issue',
      'issues.details': 'Issue details',
      'issues.col.name': 'Name',
      'issues.col.description': 'Description',
      'issues.col.type': 'Type',
      'issues.col.status': 'Status',
      'issues.col.priority': 'Priority',
      'issues.col.assigned': 'Assigned',
      'issues.col.created': 'Created',
      'issues.type.bug': 'Bug',
      'issues.type.feature': 'Feature',
      'issues.type.improvement': 'Improvement',
      'issues.type.task': 'Task',
      'issues.type.question': 'Question',
      'issues.status.open': 'Open',
      'issues.status.in_progress': 'In Progress',
      'issues.status.resolved': 'Resolved',
      'issues.status.closed': 'Closed',
      'issues.priority.low': 'Low',
      'issues.priority.medium': 'Medium',
      'issues.priority.high': 'High',
      'issues.priority.critical': 'Critical',
      'issues.no_issues': 'No issues',
      'issues.filter.all': 'All',
      'issues.filter.all_types': 'All types',
      'issues.type.blocker': 'Blocker',
      'issues.type.todo': 'To-Do',
      'issues.type.note': 'Note',
      'issues.stats.blockers': 'Blockers',
      'issues.stats.in_progress': 'In Progress',
      'issues.stats.resolved_today': 'Resolved today',
      'issues.assigned_to_me': 'Assigned to me',
      'issues.all': 'All issues',
      
      // Common fields
      'field.name': 'Name',
      'field.description': 'Description',
      'field.status': 'Status',
      'field.priority': 'Priority',
      'field.date': 'Date',
      'field.time': 'Time',
      'field.hours': 'Hours',
      'field.note': 'Note',
      'field.notes': 'Notes',
      'field.comment': 'Comment',
      'field.comments': 'Comments',
      'field.assigned': 'Assigned',
      'field.assignee': 'Assignee',
      'field.created': 'Created',
      'field.updated': 'Updated',
      'field.deadline': 'Deadline',
      'field.budget': 'Budget',
      'field.client': 'Client',
      'field.employee': 'Employee',
      'field.job': 'Job',
      'field.task': 'Task',
      'field.issue': 'Issue',
      'field.file': 'File',
      'field.files': 'Files',
      'field.attachment': 'Attachment',
      'field.attachments': 'Attachments',
      
      // Messages
      'msg.confirm_delete': 'Confirm delete?',
      'msg.saved': 'Saved',
      'msg.deleted': 'Deleted',
      'msg.error': 'Error',
      'msg.success': 'Success',
      'msg.loading': 'Loading...',
      'msg.no_data': 'No data',
      'msg.required': 'Required field',
    }
  };

  function getCurrentLangFromSettings(settings) {
    const lang = settings && settings.userLanguage ? String(settings.userLanguage) : 'cs';
    return Object.prototype.hasOwnProperty.call(I18N_DICT, lang) ? lang : 'cs';
  }

  function t(key) {
    const settings = loadAppSettings() || {};
    const lang = getCurrentLangFromSettings(settings);
    return (I18N_DICT[lang] && I18N_DICT[lang][key]) || (I18N_DICT.cs[key]) || key;
  }

  function applyLanguage(settings) {
    const lang = getCurrentLangFromSettings(settings || loadAppSettings() || {});
    document.documentElement.setAttribute('lang', lang);

    // Translate only opted-in elements to avoid breaking existing copy/layout.
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (!key) return;
      const val = (I18N_DICT[lang] && I18N_DICT[lang][key]) || (I18N_DICT.cs[key]);
      if (val) el.textContent = val;
    });

    // Translate placeholders (opt-in)
    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (!key) return;
      const val = (I18N_DICT[lang] && I18N_DICT[lang][key]) || (I18N_DICT.cs[key]);
      if (val) el.setAttribute('placeholder', val);
    });
  }

  
  // Apply translations for current language (helper for legacy calls)
  function applyTranslations() {
    try {
      const settings = loadAppSettings() || {};
      applyLanguage(settings);
    } catch (e) {
      console.error('applyTranslations failed:', e);
    }
  }

window.AppI18n = {
    setLanguage: function(lang){
      const settings = loadAppSettings();
      settings.userLanguage = lang || 'cs';
      saveAppSettings(settings);
      applyTranslations();
      window.dispatchEvent(new Event('settingsUpdated'));
    },
    t,
    applyLanguage,
    getLang: () => getCurrentLangFromSettings(loadAppSettings() || {}),
    setLang: (lang) => {
      try {
        const saved = localStorage.getItem('appSettings');
        const settings = saved ? JSON.parse(saved) : {};
        settings.userLanguage = lang;
        localStorage.setItem('appSettings', JSON.stringify(settings));
        applyLanguage(settings);
        window.dispatchEvent(new Event('settingsUpdated'));
      } catch (e) {
        console.error('Error setting language:', e);
      }
    }
  };
  
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
  
  function saveAppSettings(settings) {
    try {
      localStorage.setItem('appSettings', JSON.stringify(settings));
    } catch (e) {
      console.error('Error saving app settings:', e);
    }
  }
  
  // ========================================
  // APPLY SETTINGS GLOBALLY
  // ========================================
  
  function applyGlobalSettings() {
    const settings = loadAppSettings();
    if (!settings) return;

    // Apply language (i18n)
    applyLanguage(settings);
    
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
    // Apply language even before settings exist
    try { applyLanguage(loadAppSettings() || {}); } catch (_) {}
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





