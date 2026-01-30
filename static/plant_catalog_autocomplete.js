/**
 * Plant Catalog Autocomplete
 * Komponenta pro vyhledávání a výběr rostlin z katalogu s automatickým vyplněním údajů
 */

class PlantCatalogAutocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            minChars: 2,
            debounceMs: 300,
            onSelect: options.onSelect || null,
            container: options.container || document.body
        };
        
        this.debounceTimer = null;
        this.resultsDiv = null;
        this.selectedIndex = -1;
        this.currentResults = [];
        
        this.init();
    }
    
    init() {
        // Vytvoř dropdown pro výsledky
        this.resultsDiv = document.createElement('div');
        this.resultsDiv.className = 'plant-autocomplete-results';
        this.resultsDiv.style.display = 'none';
        this.options.container.appendChild(this.resultsDiv);
        
        // Position pod input
        this.positionResults();
        
        // Event listenery
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.input.addEventListener('focus', (e) => this.handleFocus(e));
        
        // Zavři při kliknutí mimo
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.resultsDiv.contains(e.target)) {
                this.hideResults();
            }
        });
        
        // Reposition při scroll/resize
        window.addEventListener('scroll', () => this.positionResults());
        window.addEventListener('resize', () => this.positionResults());
    }
    
    positionResults() {
        const rect = this.input.getBoundingClientRect();
        this.resultsDiv.style.position = 'fixed';
        this.resultsDiv.style.top = `${rect.bottom + 4}px`;
        this.resultsDiv.style.left = `${rect.left}px`;
        this.resultsDiv.style.width = `${rect.width}px`;
        this.resultsDiv.style.maxHeight = '300px';
        this.resultsDiv.style.overflowY = 'auto';
        this.resultsDiv.style.zIndex = '9999';
    }
    
    handleInput(e) {
        const value = e.target.value.trim();
        
        clearTimeout(this.debounceTimer);
        
        if (value.length < this.options.minChars) {
            this.hideResults();
            return;
        }
        
        this.debounceTimer = setTimeout(() => {
            this.search(value);
        }, this.options.debounceMs);
    }
    
    handleKeydown(e) {
        if (!this.resultsDiv.style.display || this.resultsDiv.style.display === 'none') {
            return;
        }
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectNext();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectPrevious();
                break;
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0 && this.currentResults[this.selectedIndex]) {
                    this.selectPlant(this.currentResults[this.selectedIndex]);
                }
                break;
            case 'Escape':
                this.hideResults();
                break;
        }
    }
    
    handleFocus(e) {
        const value = e.target.value.trim();
        if (value.length >= this.options.minChars) {
            this.search(value);
        }
    }
    
    async search(query) {
        try {
            const response = await fetch(`/api/plant-catalog/search?q=${encodeURIComponent(query)}&limit=30`);
            const data = await response.json();
            
            if (data.success && data.plants.length > 0) {
                this.currentResults = data.plants;
                this.showResults(data.plants);
            } else {
                this.showNoResults();
            }
        } catch (error) {
            console.error('Chyba při vyhledávání:', error);
            this.hideResults();
        }
    }
    
    showResults(plants) {
        this.selectedIndex = -1;
        this.resultsDiv.innerHTML = '';
        
        plants.forEach((plant, index) => {
            const item = document.createElement('div');
            item.className = 'plant-autocomplete-item';
            item.dataset.index = index;
            
            item.innerHTML = `
                <div class="plant-name">${plant.full_name}</div>
                <div class="plant-details">
                    <span class="plant-detail">${plant.flower_color || '-'}</span>
                    <span class="plant-detail">${plant.flowering_time || '-'}</span>
                    <span class="plant-detail">${plant.height || '-'}</span>
                    <span class="plant-detail">Zona ${plant.hardiness_zone || '-'}</span>
                </div>
            `;
            
            item.addEventListener('click', () => this.selectPlant(plant));
            item.addEventListener('mouseenter', () => {
                this.selectedIndex = index;
                this.updateSelection();
            });
            
            this.resultsDiv.appendChild(item);
        });
        
        this.positionResults();
        this.resultsDiv.style.display = 'block';
    }
    
    showNoResults() {
        this.resultsDiv.innerHTML = '<div class="plant-autocomplete-no-results">Žádné výsledky</div>';
        this.resultsDiv.style.display = 'block';
        this.currentResults = [];
    }
    
    hideResults() {
        this.resultsDiv.style.display = 'none';
        this.currentResults = [];
        this.selectedIndex = -1;
    }
    
    selectNext() {
        if (this.selectedIndex < this.currentResults.length - 1) {
            this.selectedIndex++;
            this.updateSelection();
        }
    }
    
    selectPrevious() {
        if (this.selectedIndex > 0) {
            this.selectedIndex--;
            this.updateSelection();
        }
    }
    
    updateSelection() {
        const items = this.resultsDiv.querySelectorAll('.plant-autocomplete-item');
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('selected');
            }
        });
    }
    
    async selectPlant(plant) {
        // Načti kompletní detail rostliny
        try {
            const response = await fetch(`/api/plant-catalog/${plant.id}`);
            const data = await response.json();
            
            if (data.success) {
                this.input.value = plant.full_name;
                this.hideResults();
                
                if (this.options.onSelect) {
                    this.options.onSelect(data.plant);
                }
            }
        } catch (error) {
            console.error('Chyba při načítání detailu:', error);
        }
    }
    
    destroy() {
        if (this.resultsDiv && this.resultsDiv.parentNode) {
            this.resultsDiv.parentNode.removeChild(this.resultsDiv);
        }
    }
}

// CSS styly pro autocomplete
const autocompleteStyles = `
<style>
.plant-autocomplete-results {
    background: var(--bg-modal, #1a1f24);
    border: 1px solid var(--border-primary, #2d3439);
    border-radius: 8px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    min-width: 700px;
    max-height: 450px;
    overflow-y: auto;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    padding: 10px;
}

.plant-autocomplete-item {
    padding: 10px 12px;
    cursor: pointer;
    border-radius: 6px;
    background: rgba(255,255,255,0.02);
    border: 1px solid transparent;
    transition: all 0.15s;
}

.plant-autocomplete-item:hover,
.plant-autocomplete-item.selected {
    background: rgba(159, 212, 161, 0.12);
    border-color: var(--mint, #9FD4A1);
}

.plant-name {
    font-weight: 600;
    color: var(--text-primary, #e8eef2);
    font-size: 13px;
    margin-bottom: 5px;
    line-height: 1.3;
}

.plant-details {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
}

.plant-detail {
    font-size: 10px;
    color: var(--text-secondary, #9ca8b3);
    background: rgba(159, 212, 161, 0.08);
    padding: 2px 6px;
    border-radius: 3px;
}

.plant-autocomplete-no-results {
    grid-column: 1 / -1;
    padding: 20px;
    text-align: center;
    color: var(--text-secondary, #9ca8b3);
    font-size: 13px;
}
</style>
`;

// Přidej styly do dokumentu
if (typeof document !== 'undefined') {
    document.head.insertAdjacentHTML('beforeend', autocompleteStyles);
}
