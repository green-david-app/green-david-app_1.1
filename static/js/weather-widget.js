// === WEATHER WIDGET WITH GPS ===

const WeatherWidget = {
    location: null,
    source: 'unknown', // 'gps', 'manual', 'fallback'
    
    async init() {
        this.showLoading();
        
        // Zkusit GPS
        const gpsResult = await this.tryGPS();
        
        if (gpsResult.success) {
            // GPS funguje!
            this.location = gpsResult.coords;
            this.source = 'gps';
            this.hideGPSWarning();
            await this.loadWeather();
        } else {
            // GPS selhala - použít fallback a ukázat varování
            this.location = { lat: 49.6833, lon: 14.0167, city: 'Příbram' };
            this.source = 'fallback';
            this.showGPSWarning(gpsResult.error);
            await this.loadWeather();
        }
    },
    
    tryGPS() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve({ success: false, error: 'Prohlížeč nepodporuje GPS' });
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                async (pos) => {
                    const coords = {
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude,
                        city: 'GPS lokace' // Bude aktualizováno z API
                    };
                    resolve({ success: true, coords });
                },
                (error) => {
                    let reason = 'Neznámá chyba';
                    if (error.code === 1) reason = 'Přístup k poloze byl zamítnut. Povolte GPS v nastavení prohlížeče.';
                    if (error.code === 2) reason = 'Poloha není dostupná';
                    if (error.code === 3) reason = 'Časový limit vypršel';
                    resolve({ success: false, error: reason });
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
            );
        });
    },
    
    async loadWeather() {
        const { lat, lon, city } = this.location;
        
        try {
            const url = `/api/weather?lat=${lat}&lon=${lon}&city=${encodeURIComponent(city)}&source=${this.source}`;
            const response = await fetch(url, { credentials: 'same-origin' });
            const data = await response.json();
            
            if (data.success) {
                this.render(data);
            }
        } catch (error) {
            console.error('Weather error:', error);
        }
    },
    
    render(data) {
        // Aktualizovat název města pokud přišel z API
        if (data.city && data.city !== 'GPS lokace') {
            this.location.city = data.city;
        }
        
        // Location info
        const locationNameEl = document.getElementById('location-name');
        const locationSourceEl = document.getElementById('location-source');
        const locationIconEl = document.getElementById('location-icon');
        
        if (locationNameEl) locationNameEl.textContent = this.location.city;
        this.updateSourceBadge(locationSourceEl, locationIconEl);
        
        // Current weather
        const current = data.current;
        const tempEl = document.getElementById('temp-value');
        const descEl = document.getElementById('weather-desc');
        const feelsLikeEl = document.getElementById('feels-like');
        const humidityEl = document.getElementById('humidity');
        const windSpeedEl = document.getElementById('wind-speed');
        const iconEl = document.getElementById('weather-icon');
        
        if (tempEl) tempEl.textContent = current.temperature;
        if (descEl) descEl.textContent = current.description;
        if (feelsLikeEl) feelsLikeEl.textContent = current.feels_like;
        if (humidityEl) humidityEl.textContent = current.humidity;
        if (windSpeedEl) windSpeedEl.textContent = current.wind_speed;
        if (iconEl) iconEl.textContent = current.icon;
        
        // Alerts pro zahradníky
        this.renderAlerts(data.alerts || []);
        
        // Forecast
        this.renderForecast(data.forecast || []);
    },
    
    updateSourceBadge(badgeEl, iconEl) {
        if (!badgeEl) return;
        
        if (this.source === 'gps') {
            badgeEl.textContent = '(GPS)';
            badgeEl.className = 'location-source source-gps';
            if (iconEl) iconEl.textContent = '📍';
        } else if (this.source === 'manual') {
            badgeEl.textContent = '(Manuální)';
            badgeEl.className = 'location-source source-manual';
            if (iconEl) iconEl.textContent = '🏙️';
        } else {
            badgeEl.textContent = '(Výchozí)';
            badgeEl.className = 'location-source source-fallback';
            if (iconEl) iconEl.textContent = '⚠️';
        }
    },
    
    renderAlerts(alerts) {
        const container = document.getElementById('weather-alerts');
        if (!container) return;
        
        if (alerts.length > 0) {
            container.innerHTML = alerts.map(a => `
                <div class="alert alert-${a.type}">
                    <span class="alert-icon">${a.icon}</span>
                    <span class="alert-text">${a.text}</span>
                </div>
            `).join('');
            container.style.display = 'block';
        } else {
            container.style.display = 'none';
        }
    },
    
    renderForecast(forecast) {
        const container = document.getElementById('weather-forecast');
        if (!container || !forecast.length) return;
        
        const dayNames = ['Ne', 'Po', 'Út', 'St', 'Čt', 'Pá', 'So'];
        const html = forecast.slice(0, 5).map((day, i) => {
            const date = new Date(day.date);
            const dayName = dayNames[date.getDay()] || day.date;
            return `
                <div class="forecast-day">
                    <span class="day-name">${dayName}</span>
                    <span class="day-icon">${day.icon}</span>
                    <span class="day-temps">
                        <strong>${Math.round(day.temp_max)}°</strong>
                        ${day.temp_min ? `<small>${Math.round(day.temp_min)}°</small>` : ''}
                    </span>
                </div>
            `;
        }).join('');
        
        container.innerHTML = html;
    },
    
    showGPSWarning(reason) {
        const warning = document.getElementById('gps-warning');
        const reasonEl = document.getElementById('gps-error-reason');
        if (warning) warning.style.display = 'flex';
        if (reasonEl) reasonEl.textContent = reason;
    },
    
    hideGPSWarning() {
        const warning = document.getElementById('gps-warning');
        if (warning) warning.style.display = 'none';
    },
    
    showLoading() {
        const nameEl = document.getElementById('location-name');
        if (nameEl) nameEl.textContent = 'Načítám...';
    },
    
    setManualLocation(city, lat, lon) {
        this.location = { lat, lon, city };
        this.source = 'manual';
        this.hideGPSWarning();
        this.loadWeather();
    }
};

// === GLOBAL FUNCTIONS ===

window.retryGPS = function() {
    WeatherWidget.init();
};

window.setCity = function(name, lat, lon) {
    WeatherWidget.setManualLocation(name, lat, lon);
    closeLocationModal();
};

window.openLocationModal = function() {
    const modal = document.getElementById('location-modal');
    if (modal) modal.classList.add('open');
};

window.closeLocationModal = function() {
    const modal = document.getElementById('location-modal');
    if (modal) modal.classList.remove('open');
};

// Init on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => WeatherWidget.init());
} else {
    WeatherWidget.init();
}
