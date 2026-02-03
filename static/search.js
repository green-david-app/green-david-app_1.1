(function () {
  function getQuery() {
    const params = new URLSearchParams(window.location.search);
    return (params.get('q') || '').trim();
  }

  function esc(s) {
    return (s || '').toString()
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function icon(label) {
    // lightweight inline icons (avoid dependency issues on this page)
    const map = {
      jobs: '📁',
      tasks: '✅',
      issues: '⚠️',
      employees: '👤'
    };
    return map[label] || '•';
  }

  async function fetchJSON(url) {
    const r = await fetch(url, { credentials: 'include' });
    const ct = (r.headers.get('content-type') || '').toLowerCase();
    if (!r.ok) {
      // try to extract server message
      let body = '';
      try { body = await r.text(); } catch (e) {}
      throw new Error(`HTTP ${r.status} ${r.statusText}${body ? ' - ' + body.slice(0, 200) : ''}`);
    }
    if (!ct.includes('application/json')) {
      const t = await r.text();
      throw new Error('Server did not return JSON (got ' + ct + '). ' + t.slice(0, 200));
    }
    return await r.json();
  }

  function renderGroup(title, itemsHtml) {
    return `
      <div class="search-group">
        <h2>${esc(title)}</h2>
        ${itemsHtml}
      </div>
    `;
  }

  function renderEmpty() {
    return `<div class="search-empty">Žádné výsledky.</div>`;
  }

  function renderItems(items, type) {
    if (!items || items.length === 0) return renderEmpty();

    return items.map(it => {
      let href = '#';
      let name = '';
      let muted = '';

      if (type === 'jobs') {
        href = `/jobs.html?id=${encodeURIComponent(it.id)}`;
        name = it.name || it.title || '';
        muted = [it.customer || it.client || '', it.status || ''].filter(Boolean).join(' • ');
      } else if (type === 'tasks') {
        href = `/tasks.html?id=${encodeURIComponent(it.id)}`;
        name = it.title || it.name || '';
        muted = [it.job_name || '', it.status || ''].filter(Boolean).join(' • ');
      } else if (type === 'issues') {
        // issues in dropdown open job detail (consistent with global-search dropdown)
        href = it.job_id ? `/jobs.html?id=${encodeURIComponent(it.job_id)}` : '#';
        name = it.title || '';
        muted = [it.job_name || '', it.type || it.severity || ''].filter(Boolean).join(' • ');
      } else if (type === 'employees') {
        href = `/employees.html?id=${encodeURIComponent(it.id)}`;
        name = it.name || '';
        muted = [it.email || '', it.role || ''].filter(Boolean).join(' • ');
      }

      return `
        <div class="search-item">
          <a href="${href}">${esc(name)}</a>
          ${muted ? `<div class="muted">${esc(muted)}</div>` : ''}
        </div>
      `;
    }).join('');
  }

  function setMeta(q, totals) {
    const metaEl = document.getElementById('search-meta');
    if (!metaEl) return;
    const total = (totals.jobs || 0) + (totals.tasks || 0) + (totals.issues || 0) + (totals.employees || 0);
    metaEl.textContent = q ? `Výraz: "${q}" • Nalezeno: ${total}` : 'Zadejte výraz pro vyhledávání.';
  }

  async function runSearch(q) {
    const groupsEl = document.getElementById('search-groups');
    if (!groupsEl) return;

    if (!q || q.length < 2) {
      setMeta(q, { jobs: 0, tasks: 0, issues: 0, employees: 0 });
      groupsEl.innerHTML = '';
      return;
    }

    groupsEl.innerHTML = renderGroup('Načítám…', '<div class="search-empty">Načítám…</div>');

    try {
      const data = await fetchJSON(`/api/search?q=${encodeURIComponent(q)}`);
      const results = (data && (data.results || data.data || data)) || {};
      const jobs = results.jobs || [];
      const tasks = results.tasks || [];
      const issues = results.issues || [];
      const employees = results.employees || [];

      setMeta(q, { jobs: jobs.length, tasks: tasks.length, issues: issues.length, employees: employees.length });

      const html =
        renderGroup(`${icon('jobs')} Zakázky (${jobs.length})`, renderItems(jobs, 'jobs')) +
        renderGroup(`${icon('employees')} Tým (${employees.length})`, renderItems(employees, 'employees')) +
        renderGroup(`${icon('tasks')} Úkoly (${tasks.length})`, renderItems(tasks, 'tasks')) +
        renderGroup(`${icon('issues')} Issues (${issues.length})`, renderItems(issues, 'issues'));

      groupsEl.innerHTML = html;
    } catch (err) {
      console.error('Search page error:', err);
      setMeta(q, { jobs: 0, tasks: 0, issues: 0, employees: 0 });
      groupsEl.innerHTML = renderGroup('Chyba', `<div class="search-empty">Vyhledávání selhalo: ${esc(err.message || err)}</div>`);
    }
  }

  // initial
  runSearch(getQuery());

  // support header "global-search" event
  window.addEventListener('global-search', (e) => {
    const q = (e.detail && e.detail.q) ? e.detail.q : getQuery();
    // keep URL in sync
    try {
      const u = new URL(window.location.href);
      u.searchParams.set('q', q);
      window.history.replaceState({}, '', u.toString());
    } catch (_) {}
    runSearch(q);
  });
})();