// Notification Center - Bell icon with dropdown
(function() {
  'use strict';

  let unreadCount = 0;
  let notifications = [];
  let isOpen = false;
  let pollInterval = null;
  let container = null;

  // Icons
  const bellIcon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
  </svg>`;

  const icons = {
    task: '📋',
    job: '🏗️',
    deadline: '⏰',
    warning: '⚠️',
    success: '✅',
    info: 'ℹ️',
    comment: '💬',
    assignment: '👤',
    stock: '📦',
    weather: '🌤️'
  };

  // Request browser notification permission
  async function requestPermission() {
    if (!('Notification' in window)) {
      console.log('Browser does not support notifications');
      return false;
    }
    
    if (Notification.permission === 'granted') {
      return true;
    }
    
    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    
    return false;
  }

  // Show browser notification
  function showBrowserNotification(title, body, icon) {
    if (Notification.permission === 'granted') {
      const notif = new Notification(title, {
        body: body,
        icon: icon || '/logo.jpg',
        badge: '/logo.jpg',
        tag: 'green-david-' + Date.now(),
        requireInteraction: false
      });
      
      notif.onclick = function() {
        window.focus();
        notif.close();
      };
      
      // Auto close after 5 seconds
      setTimeout(() => notif.close(), 5000);
    }
  }

  // Fetch notifications from API
  async function fetchNotifications() {
    try {
      const response = await fetch('/api/notifications?limit=20', {
        credentials: 'same-origin'
      });
      
      if (!response.ok) return;
      
      const data = await response.json();
      if (!data.ok) return;
      
      const oldUnread = unreadCount;
      notifications = data.rows || [];
      unreadCount = notifications.filter(n => !n.is_read).length;
      
      // Show browser notification for new items
      if (unreadCount > oldUnread && oldUnread >= 0) {
        const newOnes = notifications.filter(n => !n.is_read).slice(0, unreadCount - oldUnread);
        newOnes.forEach(n => {
          showBrowserNotification(n.title || 'Nová notifikace', n.body || '', null);
        });
      }
      
      updateBadge();
      if (isOpen) renderDropdown();
      
    } catch (e) {
      console.warn('Failed to fetch notifications:', e);
      // NEZOBRAZUJ technické chyby uživateli - jen loguj do konzole
    }
  }

  // Mark notification as read
  async function markAsRead(id) {
    try {
      await fetch('/api/notifications', {
        method: 'PATCH',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
      });
      
      const notif = notifications.find(n => n.id === id);
      if (notif) notif.is_read = 1;
      unreadCount = notifications.filter(n => !n.is_read).length;
      updateBadge();
      renderDropdown();
    } catch (e) {
      console.warn('Failed to mark as read:', e);
    }
  }

  // Mark all as read
  async function markAllAsRead() {
    try {
      await fetch('/api/notifications', {
        method: 'PATCH',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ all: true })
      });
      
      notifications.forEach(n => n.is_read = 1);
      unreadCount = 0;
      updateBadge();
      renderDropdown();
    } catch (e) {
      console.warn('Failed to mark all as read:', e);
    }
  }

  // Update badge count
  function updateBadge() {
    // Použij existující badge z app-header.js
    const badge = document.getElementById('notif-badge');
    if (badge) {
      badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
      badge.style.display = unreadCount > 0 ? 'inline-flex' : 'none';
    }
  }

  // Format time ago
  function timeAgo(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'právě teď';
    if (diff < 3600) return Math.floor(diff / 60) + ' min';
    if (diff < 86400) return Math.floor(diff / 3600) + ' h';
    if (diff < 604800) return Math.floor(diff / 86400) + ' d';
    return date.toLocaleDateString('cs-CZ');
  }

  // Render dropdown content
  function renderDropdown() {
    const dropdown = container?.querySelector('.notif-dropdown');
    if (!dropdown) return;

    if (notifications.length === 0) {
      dropdown.innerHTML = `
        <div class="notif-header">
          <span>Notifikace</span>
        </div>
        <div class="notif-empty">
          <span style="font-size: 32px; margin-bottom: 8px;">🔔</span>
          <span>Žádné notifikace</span>
        </div>
      `;
      return;
    }

    let html = `
      <div class="notif-header">
        <span>Notifikace ${unreadCount > 0 ? `(${unreadCount} nové)` : ''}</span>
        ${unreadCount > 0 ? `<button class="notif-mark-all" onclick="window.NotificationCenter.markAllAsRead()">Označit vše</button>` : ''}
      </div>
      <div class="notif-list">
    `;

    notifications.forEach(n => {
      const icon = icons[n.kind] || icons.info;
      const unreadClass = n.is_read ? '' : 'unread';
      
      html += `
        <div class="notif-item ${unreadClass}" data-id="${n.id}" onclick="window.NotificationCenter.handleClick(${n.id}, '${n.entity_type || ''}', ${n.entity_id || 0})">
          <div class="notif-icon">${icon}</div>
          <div class="notif-content">
            <div class="notif-title">${n.title || 'Notifikace'}</div>
            <div class="notif-body">${n.body || ''}</div>
            <div class="notif-time">${timeAgo(n.created_at)}</div>
          </div>
        </div>
      `;
    });

    html += `
      </div>
      <div class="notif-footer">
        <a href="/notifications.html">Zobrazit všechny</a>
      </div>
    `;

    dropdown.innerHTML = html;
  }

  // Handle notification click
  function handleClick(id, entityType, entityId) {
    markAsRead(id);
    
    // Navigate to entity if available
    if (entityType && entityId) {
      switch (entityType) {
        case 'task':
          window.location.href = `/tasks.html?id=${entityId}`;
          break;
        case 'job':
          window.location.href = `/job-detail.html?id=${entityId}`;
          break;
        case 'employee':
          window.location.href = `/employee-detail.html?id=${entityId}`;
          break;
        default:
          break;
      }
    }
    
    closeDropdown();
  }

  // Toggle dropdown
  function toggleDropdown() {
    isOpen = !isOpen;
    const dropdown = container?.querySelector('.notif-dropdown');
    if (dropdown) {
      dropdown.style.display = isOpen ? 'block' : 'none';
      if (isOpen) {
        renderDropdown();
        // Request permission on first open
        requestPermission();
      }
    }
  }

  // Close dropdown
  function closeDropdown() {
    isOpen = false;
    const dropdown = container?.querySelector('.notif-dropdown');
    if (dropdown) {
      dropdown.style.display = 'none';
    }
  }

  // Initialize notification center
  function init() {
    // Použij existující notifikační ikonu z app-header.js
    // NEVYTVÁŘEJ nový element!
    const existingBell = document.getElementById('app-header-notifications');
    const existingBadge = document.getElementById('notif-badge');
    
    if (!existingBell || !existingBadge) {
      // Header ještě není načtený, zkus znovu
      setTimeout(init, 500);
      return;
    }

    // Pokud už existuje notification-center container, nepřidávej další
    if (document.getElementById('notification-center')) return;

    // Vytvoř pouze dropdown container (ne ikonu)
    container = document.createElement('div');
    container.id = 'notification-center';
    container.className = 'notification-center';
    container.innerHTML = `<div class="notif-dropdown" style="display: none;"></div>`;
    
    // Vlož dropdown vedle existující ikony
    existingBell.parentElement.appendChild(container);

    // Přidej click handler na existující ikonu
    // Pokud uživatel klikne na badge nebo SVG ikonu, otevři dropdown místo navigace
    existingBell.addEventListener('click', (e) => {
      // Pokud klikne na badge nebo SVG, otevři dropdown
      if (e.target.closest('.notif-badge') || e.target.tagName === 'svg' || e.target.closest('svg')) {
        e.preventDefault();
        e.stopPropagation();
        window.NotificationCenter.toggle();
      }
      // Jinak nech link navigovat na /notifications.html
    });

    // Add styles
    addStyles();

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (isOpen && container && !container.contains(e.target) && !existingBell.contains(e.target)) {
        closeDropdown();
      }
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isOpen) {
        closeDropdown();
      }
    });

    // Initial fetch
    fetchNotifications();

    // Poll every 30 seconds
    pollInterval = setInterval(fetchNotifications, 30000);

    // Request permission after a delay
    setTimeout(() => {
      if (Notification.permission === 'default') {
        // Don't auto-request, wait for user interaction
      }
    }, 5000);
  }

  // Add CSS styles
  function addStyles() {
    if (document.getElementById('notification-center-styles')) return;

    const style = document.createElement('style');
    style.id = 'notification-center-styles';
    style.textContent = `
      .notification-center {
        position: relative;
        margin-right: 8px;
      }

      .notif-bell {
        background: none;
        border: none;
        color: #9ca8b3;
        cursor: pointer;
        padding: 8px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        transition: all 0.2s;
      }

      .notif-bell:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #e8eef2;
      }

      .notif-badge {
        position: absolute;
        top: 2px;
        right: 2px;
        background: #ef4444;
        color: white;
        font-size: 10px;
        font-weight: 600;
        min-width: 16px;
        height: 16px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 4px;
      }

      .notif-dropdown {
        position: absolute;
        top: 100%;
        right: 0;
        width: 360px;
        max-width: calc(100vw - 32px);
        background: #151a1e;
        border: 1px solid rgba(159, 212, 161, 0.2);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        z-index: 10000;
        overflow: hidden;
        margin-top: 8px;
      }

      .notif-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 600;
        color: #e8eef2;
      }

      .notif-mark-all {
        background: none;
        border: none;
        color: #4ade80;
        font-size: 12px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        transition: background 0.2s;
      }

      .notif-mark-all:hover {
        background: rgba(159, 212, 161, 0.1);
      }

      .notif-list {
        max-height: 400px;
        overflow-y: auto;
      }

      .notif-item {
        display: flex;
        gap: 12px;
        padding: 12px 16px;
        cursor: pointer;
        transition: background 0.2s;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      }

      .notif-item:hover {
        background: rgba(255, 255, 255, 0.05);
      }

      .notif-item.unread {
        background: rgba(59, 130, 246, 0.1);
        border-left: 3px solid #3b82f6;
      }

      .notif-icon {
        font-size: 20px;
        flex-shrink: 0;
      }

      .notif-content {
        flex: 1;
        min-width: 0;
      }

      .notif-title {
        font-weight: 500;
        color: #e8eef2;
        font-size: 13px;
        margin-bottom: 2px;
      }

      .notif-body {
        font-size: 12px;
        color: #9ca8b3;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .notif-time {
        font-size: 11px;
        color: #6b7580;
        margin-top: 4px;
      }

      .notif-empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 20px;
        color: #6b7580;
        font-size: 14px;
      }

      .notif-footer {
        padding: 12px 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
      }

      .notif-footer a {
        color: #4ade80;
        text-decoration: none;
        font-size: 13px;
        font-weight: 500;
      }

      .notif-footer a:hover {
        text-decoration: underline;
      }

      @media (max-width: 480px) {
        .notif-dropdown {
          position: fixed;
          top: 60px;
          left: 8px;
          right: 8px;
          width: auto;
        }
      }
    `;
    document.head.appendChild(style);
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Export for external use
  window.NotificationCenter = {
    toggle: toggleDropdown,
    close: closeDropdown,
    refresh: fetchNotifications,
    markAsRead: markAsRead,
    markAllAsRead: markAllAsRead,
    handleClick: handleClick,
    requestPermission: requestPermission
  };
})();
