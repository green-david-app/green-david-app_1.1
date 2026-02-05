// AUTOCOMPLETE PRO MATERIÁLY - WAREHOUSE INTEGRATION
// ===================================================

let searchTimeout = null;
let selectedWarehouseItem = null;

function initMaterialAutocomplete() {
    const input = document.getElementById('material-name-input');
    const dropdown = document.getElementById('material-autocomplete');
    const infoDiv = document.getElementById('material-info');
    
    if (!input || !dropdown) {
        console.warn('Material autocomplete elements not found');
        return;
    }
    
    // Poslouchej psaní
    input.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        // Reset selection
        delete input.dataset.warehouseItemId;
        selectedWarehouseItem = null;
        if (infoDiv) infoDiv.style.display = 'none';
        
        if (query.length < 2) {
            dropdown.style.display = 'none';
            return;
        }
        
        searchTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`/api/warehouse/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.items && data.items.length > 0) {
                    renderAutocompleteResults(dropdown, data.items, input, infoDiv);
                    dropdown.style.display = 'block';
                } else {
                    dropdown.innerHTML = '<div style="padding:12px;color:#9ca3af;">Žádné položky na skladě</div>';
                    dropdown.style.display = 'block';
                }
            } catch (error) {
                console.error('Autocomplete error:', error);
                dropdown.style.display = 'none';
            }
        }, 300);
    });
    
    // Zavři při kliknutí mimo
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });
    
    // Zavři při ESC
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            dropdown.style.display = 'none';
        }
    });
}

function renderAutocompleteResults(dropdown, items, input, infoDiv) {
    dropdown.innerHTML = '';
    
    items.forEach(item => {
        const div = document.createElement('div');
        div.style.cssText = `
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid #2d3748;
            transition: background 0.2s;
        `;
        
        const availableQty = item.available_qty !== undefined ? item.available_qty : (item.qty - (item.reserved_qty || 0));
        const isAvailable = availableQty > 0;
        
        div.innerHTML = `
            <div style="font-weight: 600; color: white; margin-bottom: 4px;">${escapeHtml(item.name)}</div>
            <div style="font-size: 12px; color: #9ca3af; display: flex; gap: 12px; flex-wrap: wrap;">
                ${item.sku ? `<span>SKU: ${escapeHtml(item.sku)}</span>` : ''}
                ${item.category ? `<span>Kategorie: ${escapeHtml(item.category)}</span>` : ''}
                <span style="color: ${isAvailable ? '#9fd4a1' : '#f56565'}; font-weight: 600;">
                    Dostupné: ${availableQty.toFixed(2)} ${escapeHtml(item.unit)}
                </span>
                ${item.location ? `<span>📍 ${escapeHtml(item.location)}</span>` : ''}
                ${item.price ? `<span>💰 ${item.price} Kč/${escapeHtml(item.unit)}</span>` : ''}
            </div>
        `;
        
        div.addEventListener('mouseenter', () => {
            div.style.background = '#2d3748';
        });
        
        div.addEventListener('mouseleave', () => {
            div.style.background = 'transparent';
        });
        
        div.addEventListener('click', () => {
            selectWarehouseItem(item, input, dropdown, infoDiv);
        });
        
        dropdown.appendChild(div);
    });
}

function selectWarehouseItem(item, input, dropdown, infoDiv) {
    selectedWarehouseItem = item;
    
    // Vyplň formulář
    input.value = item.name;
    input.dataset.warehouseItemId = item.id;
    input.dataset.availableQty = item.available_qty !== undefined ? item.available_qty : (item.qty - (item.reserved_qty || 0));
    input.dataset.location = item.location || '';
    input.dataset.price = item.price || 0;
    
    // Nastav jednotku a cenu
    const unitInput = document.getElementById('material-unit-input');
    const priceInput = document.getElementById('material-price-input');
    
    if (unitInput) unitInput.value = item.unit || 'ks';
    if (priceInput) priceInput.value = item.price || 0;
    
    // Zobraz info
    if (infoDiv) {
        const availableQty = item.available_qty !== undefined ? item.available_qty : (item.qty - (item.reserved_qty || 0));
        const reservedQty = item.reserved_qty || 0;
        
        infoDiv.innerHTML = `
            <div style="background: #1a2332; padding: 12px; border-radius: 8px; border-left: 3px solid #9fd4a1;">
                <div style="font-size: 14px; color: white; font-weight: 600; margin-bottom: 8px;">
                    ✅ Položka ze skladu vybrána
                </div>
                <div style="display: grid; gap: 6px; font-size: 13px; color: #9ca3af;">
                    <div>
                        📦 <strong style="color: white;">${availableQty.toFixed(2)} ${item.unit}</strong> dostupné
                        ${reservedQty > 0 ? `<span style="color: #f59e0b;">(${reservedQty.toFixed(2)} ${item.unit} již rezervováno)</span>` : ''}
                    </div>
                    ${item.location ? `<div>📍 Lokace: <strong style="color: white;">${escapeHtml(item.location)}</strong></div>` : ''}
                    ${item.price ? `<div>💰 Cena: <strong style="color: white;">${item.price} Kč/${item.unit}</strong></div>` : ''}
                    ${item.sku ? `<div>🏷️ SKU: ${escapeHtml(item.sku)}</div>` : ''}
                </div>
            </div>
        `;
        infoDiv.style.display = 'block';
    }
    
    // Zavři dropdown
    dropdown.style.display = 'none';
    
    // Focus na množství
    const qtyInput = document.getElementById('material-qty-input');
    if (qtyInput) {
        qtyInput.focus();
        qtyInput.select();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// Inicializuj po načtení
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMaterialAutocomplete);
} else {
    initMaterialAutocomplete();
}

debugLog('✅ Material autocomplete loaded');
