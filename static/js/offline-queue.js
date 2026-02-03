/**
 * GREEN DAVID APP - Offline Queue (offline-queue.js)
 * Stores API calls when offline, replays when back online
 */

(function() {
    'use strict';

    var QUEUE_KEY = 'gd_offline_queue';

    /**
     * Get pending items from queue
     */
    function getQueue() {
        try {
            var data = localStorage.getItem(QUEUE_KEY);
            return data ? JSON.parse(data) : [];
        } catch(e) {
            return [];
        }
    }

    /**
     * Save queue
     */
    function saveQueue(queue) {
        try {
            localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
        } catch(e) {
            console.warn('Cannot save offline queue:', e);
        }
    }

    /**
     * Add item to offline queue
     */
    window.addToOfflineQueue = function(url, method, data) {
        var queue = getQueue();
        queue.push({
            url: url,
            method: method || 'POST',
            data: data,
            timestamp: new Date().toISOString()
        });
        saveQueue(queue);
        updateQueueBadge();
    };

    /**
     * Process queue when online
     */
    async function processQueue() {
        if (!navigator.onLine) return;
        
        var queue = getQueue();
        if (queue.length === 0) return;

        var remaining = [];
        
        for (var i = 0; i < queue.length; i++) {
            var item = queue[i];
            try {
                await fetch(item.url, {
                    method: item.method,
                    headers: { 'Content-Type': 'application/json' },
                    body: item.data ? JSON.stringify(item.data) : undefined
                });
            } catch(e) {
                remaining.push(item);
            }
        }
        
        saveQueue(remaining);
        updateQueueBadge();
    }

    /**
     * Update badge showing pending items
     */
    function updateQueueBadge() {
        var queue = getQueue();
        var badges = document.querySelectorAll('.offline-queue-badge');
        badges.forEach(function(badge) {
            if (queue.length > 0) {
                badge.textContent = queue.length;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        });
    }

    // Process when coming back online
    window.addEventListener('online', processQueue);
    
    // Initial check
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            updateQueueBadge();
            processQueue();
        });
    } else {
        updateQueueBadge();
        processQueue();
    }

})();
