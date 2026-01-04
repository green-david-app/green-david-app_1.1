(function () {
  function getQuery() {
    const params = new URLSearchParams(window.location.search);
    return (params.get('q') || '').trim();
  }

  function norm(s) {
    return (s || '').toString().toLowerCase();
  }

  function includesAny(hay, q) {
    return norm(hay).includes(norm(q));
  }

  async function fetchJSON(url) {
    const r = await fetch(url, { credentials: 'include' });
    if (!r.ok) throw new Error(`${url} => ${r.status}`);
    return await r.json();
  }

  function renderGroup(title, itemsHtml) {
    return `
      <div class="search-group">
        <h2>${title}</h2>
        ${itemsHtml}
      </div>
    `;
  }

  function emptyHtml() {
    return '<div class="search-empty">Žádné výsledky.</div>';
  }

  function jobLink(job) {
    // Přesměrování na zakázky; detail je v aplikaci řešen JS. Odkaz vede na přehled s hash/id.
    const id = job.id || job.job_id || '';
    return `/jobs.html#job=${encodeURIComponent(id)}`;
  }

  function employeeLink(emp) {
    const id = emp.id || emp.employee_id || '';
    return `/employee-detail.html?id=${encodeURIComponent(id)}`;
  }

  function taskLink(task) {
    // Úkoly mají vlastní přehled; použijeme hash/id pro případné zvýraznění později
    const id = task.id || task.task_id || '';
    return `/tasks.html#task=${encodeURIComponent(id)}`;
  }

  function renderItems(results, kind) {
    if (!results.length) return emptyHtml();
    return results.slice(0, 20).map(r => {
      if (kind === 'jobs') {
        const title = r.name || r.title || r.job_name || `Zakázka ${r.id ?? ''}`;
        const meta = [r.customer, r.client, r.code, r.status].filter(Boolean).join(' • ');
        return `
          <div class="search-item">
            <a href="${jobLink(r)}">${title}</a>
            ${meta ? `<div class="muted">${meta}</div>` : ``}
          </div>
        `;
      }
      if (kind === 'employees') {
        const title = r.name || r.full_name || `${r.first_name ?? ''} ${r.last_name ?? ''}`.trim() || `Zaměstnanec ${r.id ?? ''}`;
        const meta = [r.role, r.position, (r.account_email ? `Účet: ${r.account_email} (${r.account_role || ''})` : null)].filter(Boolean).join(' • ');
        return `
          <div class="search-item">
            <a href="${employeeLink(r)}">${title}</a>
            ${meta ? `<div class="muted">${meta}</div>` : ``}
          </div>
        `;
      }
      if (kind === 'tasks') {
        const title = r.title || r.name || `Úkol ${r.id ?? ''}`;
        const meta = [r.status, r.assignee_name, r.due_date].filter(Boolean).join(' • ');
        const desc = r.description || r.note || '';
        return `
          <div class="search-item">
            <a href="${taskLink(r)}">${title}</a>
            ${meta ? `<div class="muted">${meta}</div>` : ``}
            ${desc ? `<div class="muted">${String(desc).slice(0, 120)}${String(desc).length > 120 ? '…' : ''}</div>` : ``}
          </div>
        `;
      }
      return '';
    }).join('');
  }

  async function runSearch(q) {
    const metaEl = document.getElementById('search-meta');
    const groupsEl = document.getElementById('search-groups');
    if (!metaEl || !groupsEl) return;

    if (!q) {
      metaEl.textContent = 'Zadej výraz do vyhledávání v horním panelu.';
      groupsEl.innerHTML = renderGroup('Zakázky', emptyHtml()) + renderGroup('Tým', emptyHtml()) + renderGroup('Úkoly', emptyHtml());
      return;
    }

    metaEl.textContent = `Vyhledávám: "${q}"`;

    let jobs = [];
    let employees = [];
    let tasks = [];

    // Paralelní načtení, ať je UI rychlé
    const calls = [
      fetchJSON('/api/jobs').then(d => { jobs = (d.jobs || d || []); }).catch(() => {}),
      fetchJSON('/api/employees').then(d => { employees = (d.employees || d || []); }).catch(() => {}),
      fetchJSON('/api/tasks').then(d => { tasks = (d.tasks || d || []); }).catch(() => {}),
    ];

    await Promise.allSettled(calls);

    const qn = norm(q);

    const jobsFound = jobs.filter(j => {
      return includesAny(j.name, qn) || includesAny(j.title, qn) || includesAny(j.customer, qn) || includesAny(j.client, qn) || includesAny(j.code, qn) || includesAny(j.status, qn);
    });

    const employeesFound = employees.filter(e => {
      return includesAny(e.name, qn) || includesAny(e.full_name, qn) || includesAny(e.first_name, qn) || includesAny(e.last_name, qn) || includesAny(e.position, qn) || includesAny(e.role, qn) || includesAny(e.account_email, qn) || includesAny(e.account_role, qn);
    });

    const tasksFound = tasks.filter(t => {
      return includesAny(t.title, qn) || includesAny(t.name, qn) || includesAny(t.description, qn) || includesAny(t.note, qn) || includesAny(t.status, qn) || includesAny(t.assignee_name, qn);
    });

    const total = jobsFound.length + employeesFound.length + tasksFound.length;
    metaEl.textContent = `Výraz: "${q}" • Nalezeno: ${total}`;

    groupsEl.innerHTML =
      renderGroup(`Zakázky (${jobsFound.length})`, renderItems(jobsFound, 'jobs')) +
      renderGroup(`Tým (${employeesFound.length})`, renderItems(employeesFound, 'employees')) +
      renderGroup(`Úkoly (${tasksFound.length})`, renderItems(tasksFound, 'tasks'));
  }

  // initial
  runSearch(getQuery());

  // support header "global-search" event
  window.addEventListener('global-search', (e) => {
    const q = (e.detail && e.detail.q) ? e.detail.q : getQuery();
    runSearch(q);
  });
})();
