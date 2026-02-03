/**
 * Offline Queue Manager
 * Spravuje lokální queue pro offline akce a synchronizaci při připojení
 */

const OfflineQueue = {
    STORAGE_KEY: 'offline_queue',
    MAX_RETRIES: 3,
    
    /**
     * Inicializace - kontrola online statusu a synchronizace
     */
    init() {
        // Zkontroluj online status
        window.addEventListener('online', () => {
            console.log('[OfflineQueue] Online - synchronizuji queue');
            this.sync();
        });
        
        window.addEventListener('offline', () => {
            console.log('[OfflineQueue] Offline - akce budou uloženy do queue');
        });
        
        // Při načtení stránky zkus synchronizovat
        if (navigator.onLine) {
            setTimeout(() => this.sync(), 1000);
        }
    },
    
    /**
     * Přidá event do queue
     */
    add(eventType, eventData) {
        const event = {
            id: this.generateEventId(),
            type: eventType,
            data: eventData,
            created_at: new Date().toISOString(),
            retries: 0
        };
        
        const queue = this.getQueue();
        queue.push(event);
        this.saveQueue(queue);
        
        console.log('[OfflineQueue] Event přidán do queue:', event.id);
        
        // Pokud jsme online, zkus okamžitě synchronizovat
        if (navigator.onLine) {
            setTimeout(() => this.sync(), 100);
        }
        
        return event.id;
    },
    
    /**
     * Získá aktuální queue
     */
    getQueue() {
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('[OfflineQueue] Error reading queue:', e);
            return [];
        }
    },
    
    /**
     * Uloží queue do localStorage
     */
    saveQueue(queue) {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(queue));
        } catch (e) {
            console.error('[OfflineQueue] Error saving queue:', e);
        }
    },
    
    /**
     * Synchronizuje queue se serverem
     */
    async sync() {
        if (!navigator.onLine) {
            console.log('[OfflineQueue] Offline - synchronizace přeskočena');
            return;
        }
        
        const queue = this.getQueue();
        if (queue.length === 0) {
            return;
        }
        
        console.log(`[OfflineQueue] Synchronizuji ${queue.length} eventů`);
        
        try {
            const response = await fetch('/api/offline/queue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ events: queue })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.ok) {
                // Odstraň úspěšně zpracované eventy
                const processedIds = new Set(result.processed.map(e => e.id));
                const failedIds = new Set(result.failed.map(e => e.id));
                
                const remainingQueue = queue.filter(event => {
                    // Necháme eventy, které selhaly a mají méně než MAX_RETRIES pokusů
                    if (failedIds.has(event.id)) {
                        event.retries++;
                        if (event.retries < this.MAX_RETRIES) {
                            return true; // Zkusíme znovu
                        }
                    }
                    return !processedIds.has(event.id) && !failedIds.has(event.id);
                });
                
                this.saveQueue(remainingQueue);
                
                console.log(`[OfflineQueue] Synchronizace dokončena: ${result.success_count} úspěšných, ${result.failed_count} selhalo`);
                
                // Zobraz notifikaci pokud byly nějaké chyby
                if (result.failed_count > 0 && window.showToast) {
                    window.showToast(`Některé akce se nepodařilo synchronizovat (${result.failed_count})`, 'warning');
                }
            } else {
                throw new Error(result.error || 'Synchronizace selhala');
            }
        } catch (error) {
            console.error('[OfflineQueue] Synchronizace selhala:', error);
            // Queue zůstane v localStorage pro další pokus
        }
    },
    
    /**
     * Vygeneruje unikátní event ID
     */
    generateEventId() {
        return 'event-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    },
    
    /**
     * Vymaže queue
     */
    clear() {
        localStorage.removeItem(this.STORAGE_KEY);
        console.log('[OfflineQueue] Queue vymazána');
    },
    
    /**
     * Získá počet eventů v queue
     */
    getQueueSize() {
        return this.getQueue().length;
    }
};

// Wrapper pro API volání s offline podporou
window.apiCall = async function(url, options = {}) {
    const eventId = options.headers?.['X-Event-ID'] || OfflineQueue.generateEventId();
    
    // Přidej event ID do headers
    const headers = {
        ...options.headers,
        'X-Event-ID': eventId
    };
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        // Pokud jsme offline nebo request selhal, přidej do queue
        if (!navigator.onLine || !response.ok) {
            if (response.status === 202 || response.status === 409) {
                // 202 = queued, 409 = duplicate - to je OK
                return response;
            }
            
            // Přidej do queue pro pozdější synchronizaci
            const eventType = url.split('/').pop().replace(/^api\//, '');
            OfflineQueue.add(eventType, JSON.parse(options.body || '{}'));
            
            return {
                ok: false,
                queued: true,
                event_id: eventId,
                message: 'Akce byla přidána do offline queue'
            };
        }
        
        return response;
    } catch (error) {
        // Offline nebo network error - přidej do queue
        const eventType = url.split('/').pop().replace(/^api\//, '');
        OfflineQueue.add(eventType, JSON.parse(options.body || '{}'));
        
        return {
            ok: false,
            queued: true,
            event_id: eventId,
            error: error.message
        };
    }
};

// Inicializuj při načtení
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => OfflineQueue.init());
} else {
    OfflineQueue.init();
}

// Export pro použití v jiných skriptech
window.OfflineQueue = OfflineQueue;
