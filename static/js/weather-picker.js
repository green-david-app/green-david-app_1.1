/**
 * Weather Location Picker
 * Allows user to select weather location: GPS, job sites, or custom cities
 * Persists selection in localStorage
 */
window.WeatherPicker = (function() {
  const STORAGE_KEY = 'gd_weather_location';
  
  // Czech cities with coordinates
  const CITIES = [
    { name: 'Praha', lat: 50.0755, lon: 14.4378 },
    { name: 'Příbram', lat: 49.6897, lon: 14.0101 },
    { name: 'Brno', lat: 49.1951, lon: 16.6068 },
    { name: 'Ostrava', lat: 49.8209, lon: 18.2625 },
    { name: 'Plzeň', lat: 49.7384, lon: 13.3736 },
    { name: 'Liberec', lat: 50.7671, lon: 15.0562 },
    { name: 'Olomouc', lat: 49.5938, lon: 17.2509 },
    { name: 'Č. Budějovice', lat: 48.9745, lon: 14.4743 },
    { name: 'Hradec Králové', lat: 50.2092, lon: 15.8328 },
    { name: 'Pardubice', lat: 50.0343, lon: 15.7812 },
    { name: 'Zlín', lat: 49.2265, lon: 17.6675 },
    { name: 'Karlovy Vary', lat: 50.2325, lon: 12.8713 },
  ];

  // Geocoding cache
  const geoCache = {};

  function getSaved() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch(e) { return null; }
  }

  function save(loc) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(loc)); } catch(e) {}
  }

  function clear() {
    try { localStorage.removeItem(STORAGE_KEY); } catch(e) {}
  }

  /**
   * Get weather API URL based on saved location or GPS
   * Returns promise of URL string
   */
  async function getWeatherUrl() {
    const saved = getSaved();
    
    if (saved) {
      if (saved.type === 'gps') {
        // Use fresh GPS
        try {
          const pos = await getGPS();
          return `/api/weather?lat=${pos.lat}&lon=${pos.lon}`;
        } catch(e) {
          return '/api/weather'; // fallback
        }
      }
      if (saved.lat && saved.lon) {
        return `/api/weather?lat=${saved.lat}&lon=${saved.lon}&city=${encodeURIComponent(saved.name || '')}`;
      }
      if (saved.city) {
        return `/api/weather?city=${encodeURIComponent(saved.city)}`;
      }
    }
    
    // Default: try GPS, fallback to default
    try {
      const pos = await getGPS();
      return `/api/weather?lat=${pos.lat}&lon=${pos.lon}`;
    } catch(e) {
      return '/api/weather';
    }
  }

  function getGPS() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) return reject(new Error('No geolocation'));
      navigator.geolocation.getCurrentPosition(
        pos => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        err => reject(err),
        { timeout: 5000, maximumAge: 600000 }
      );
    });
  }

  /**
   * Geocode a city name using Open-Meteo geocoding API (free, no key)
   */
  async function geocodeCity(query) {
    if (geoCache[query]) return geoCache[query];
    try {
      const resp = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=5&language=cs&format=json`);
      const data = await resp.json();
      const results = (data.results || []).map(r => ({
        name: r.name + (r.admin1 ? `, ${r.admin1}` : ''),
        lat: r.latitude,
        lon: r.longitude,
        country: r.country || ''
      }));
      geoCache[query] = results;
      return results;
    } catch(e) {
      return [];
    }
  }

  /**
   * Fetch job locations from API
   */
  async function getJobLocations() {
    try {
      const resp = await fetch('/api/jobs', { credentials: 'same-origin' });
      const data = await resp.json();
      const jobs = data.jobs || data || [];
      const locations = [];
      const seen = new Set();
      
      jobs.forEach(j => {
        if (!j.city && !j.address) return;
        if (['archived', 'cancelled', 'Archivováno', 'Zrušeno'].includes(j.status)) return;
        
        const key = (j.city || j.address || '').toLowerCase().trim();
        if (seen.has(key) || !key) return;
        seen.add(key);
        
        locations.push({
          name: j.city || j.address,
          jobName: j.client || j.name || j.title || '',
          jobId: j.id
        });
      });
      
      return locations;
    } catch(e) {
      return [];
    }
  }

  /**
   * Create and show the location picker dropdown
   * @param {HTMLElement} anchor - element to position near
   * @param {Function} onSelect - callback(location) when selected
   */
  async function showPicker(anchor, onSelect) {
    // Remove existing
    const existing = document.getElementById('weather-location-picker');
    if (existing) { existing.remove(); return; }

    const picker = document.createElement('div');
    picker.id = 'weather-location-picker';
    picker.innerHTML = `
      <div class="wlp-backdrop"></div>
      <div class="wlp-panel">
        <div class="wlp-header">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
          <span>Poloha pro počasí</span>
        </div>
        <div class="wlp-search-wrap">
          <input type="text" class="wlp-search" placeholder="Hledat město nebo adresu..." autocomplete="off"/>
        </div>
        <div class="wlp-options">
          <button class="wlp-option wlp-gps" data-type="gps">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/></svg>
            <span>Moje poloha (GPS)</span>
            <small>automaticky</small>
          </button>
          <div class="wlp-divider"><span>Zakázky</span></div>
          <div class="wlp-jobs-list wlp-loading">Načítám...</div>
          <div class="wlp-divider"><span>Města</span></div>
          <div class="wlp-cities-list"></div>
          <div class="wlp-search-results" style="display:none;">
            <div class="wlp-divider"><span>Výsledky hledání</span></div>
            <div class="wlp-search-list"></div>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(picker);
    
    // Position panel near anchor (skip on mobile — CSS centers it)
    const panel = picker.querySelector('.wlp-panel');
    if (window.innerWidth > 768) {
      const rect = anchor.getBoundingClientRect();
      const panelW = 320;
      let left = rect.left + rect.width / 2 - panelW / 2;
      if (left + panelW > window.innerWidth - 16) left = window.innerWidth - panelW - 16;
      if (left < 16) left = 16;
      panel.style.left = left + 'px';
      panel.style.top = (rect.bottom + 8) + 'px';
    }

    // Close handlers
    picker.querySelector('.wlp-backdrop').addEventListener('click', () => picker.remove());
    document.addEventListener('keydown', function esc(e) {
      if (e.key === 'Escape') { picker.remove(); document.removeEventListener('keydown', esc); }
    });

    // Highlight current selection
    const saved = getSaved();
    if (saved?.type === 'gps') {
      picker.querySelector('.wlp-gps').classList.add('active');
    }

    // GPS option
    picker.querySelector('.wlp-gps').addEventListener('click', async () => {
      save({ type: 'gps' });
      picker.remove();
      if (onSelect) onSelect({ type: 'gps' });
    });

    // Load job locations
    const jobsList = picker.querySelector('.wlp-jobs-list');
    const jobLocations = await getJobLocations();
    if (jobLocations.length === 0) {
      jobsList.innerHTML = '<div class="wlp-empty">Žádné zakázky s adresou</div>';
    } else {
      jobsList.innerHTML = '';
      // Need to geocode job cities
      for (const jl of jobLocations) {
        const btn = document.createElement('button');
        btn.className = 'wlp-option wlp-job-option';
        if (saved?.name === jl.name && saved?.type === 'job') btn.classList.add('active');
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="15" y2="13"/></svg>
          <span>${jl.name}</span>
          <small>${jl.jobName}</small>
        `;
        btn.addEventListener('click', async () => {
          // Geocode the city
          const cityName = jl.name.split(',')[0].trim();
          const known = CITIES.find(c => c.name.toLowerCase() === cityName.toLowerCase());
          if (known) {
            save({ type: 'job', name: jl.name, lat: known.lat, lon: known.lon });
            picker.remove();
            if (onSelect) onSelect({ type: 'job', name: jl.name, lat: known.lat, lon: known.lon });
          } else {
            btn.querySelector('small').textContent = 'Hledám...';
            const results = await geocodeCity(cityName);
            if (results.length > 0) {
              save({ type: 'job', name: jl.name, lat: results[0].lat, lon: results[0].lon });
              picker.remove();
              if (onSelect) onSelect({ type: 'job', name: jl.name, lat: results[0].lat, lon: results[0].lon });
            } else {
              btn.querySelector('small').textContent = 'Nenalezeno';
            }
          }
        });
        jobsList.appendChild(btn);
      }
    }
    jobsList.classList.remove('wlp-loading');

    // Render cities
    const citiesList = picker.querySelector('.wlp-cities-list');
    CITIES.forEach(city => {
      const btn = document.createElement('button');
      btn.className = 'wlp-option wlp-city-option';
      if (saved?.name === city.name && saved?.type === 'city') btn.classList.add('active');
      btn.innerHTML = `
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
        <span>${city.name}</span>
      `;
      btn.addEventListener('click', () => {
        save({ type: 'city', name: city.name, lat: city.lat, lon: city.lon });
        picker.remove();
        if (onSelect) onSelect({ type: 'city', name: city.name, lat: city.lat, lon: city.lon });
      });
      citiesList.appendChild(btn);
    });

    // Search functionality
    const searchInput = picker.querySelector('.wlp-search');
    const searchResults = picker.querySelector('.wlp-search-results');
    const searchList = picker.querySelector('.wlp-search-list');
    let searchTimeout;
    
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      const q = searchInput.value.trim();
      
      if (q.length < 2) {
        searchResults.style.display = 'none';
        // Show cities and jobs again
        picker.querySelector('.wlp-cities-list').style.display = '';
        jobsList.style.display = '';
        picker.querySelectorAll('.wlp-divider').forEach(d => d.style.display = '');
        return;
      }
      
      // Hide cities/jobs, show search
      picker.querySelector('.wlp-cities-list').style.display = 'none';
      jobsList.style.display = 'none';
      picker.querySelectorAll('.wlp-divider').forEach(d => d.style.display = 'none');
      searchResults.style.display = '';
      searchResults.querySelector('.wlp-divider').style.display = '';
      searchList.innerHTML = '<div class="wlp-empty">Hledám...</div>';
      
      searchTimeout = setTimeout(async () => {
        // First check local cities
        const localMatches = CITIES.filter(c => c.name.toLowerCase().includes(q.toLowerCase()));
        // Then geocode
        const geoResults = await geocodeCity(q);
        
        searchList.innerHTML = '';
        const allResults = [
          ...localMatches.map(c => ({ ...c, source: 'local' })),
          ...geoResults.filter(r => !localMatches.find(l => l.name === r.name)).map(r => ({ ...r, source: 'geo' }))
        ];
        
        if (allResults.length === 0) {
          searchList.innerHTML = '<div class="wlp-empty">Nic nenalezeno</div>';
          return;
        }
        
        allResults.forEach(r => {
          const btn = document.createElement('button');
          btn.className = 'wlp-option wlp-search-option';
          btn.innerHTML = `
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
            <span>${r.name}</span>
            ${r.country ? `<small>${r.country}</small>` : ''}
          `;
          btn.addEventListener('click', () => {
            save({ type: 'search', name: r.name, lat: r.lat, lon: r.lon });
            picker.remove();
            if (onSelect) onSelect({ type: 'search', name: r.name, lat: r.lat, lon: r.lon });
          });
          searchList.appendChild(btn);
        });
      }, 400);
    });
    
    // Focus search
    setTimeout(() => searchInput.focus(), 100);
  }

  return { getWeatherUrl, showPicker, getSaved, save, clear, geocodeCity, CITIES };
})();
