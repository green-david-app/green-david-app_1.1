
// employees-tabs-inject.js
// Turns the existing Employees page into two tabs (Employees + Brigádníci) on the client side.
// It preserves the original look by reusing the existing DOM for Employees.

(function() {
  function makeEl(html) {
    const t = document.createElement('template');
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  function buildTabsContainer() {
    return makeEl(`
      <div class="card" style="background:#1f2a27;color:#e9f6ef;border:none;border-radius:10px;margin-bottom:1rem">
        <div class="card-body">
          <ul class="nav nav-tabs" role="tablist" id="gd-tabs">
            <li class="nav-item" role="presentation">
              <button class="nav-link active" id="gd-tab-emps" data-bs-toggle="tab" data-bs-target="#gd-pane-emps" type="button" role="tab" aria-controls="gd-pane-emps" aria-selected="true">Zaměstnanci</button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" id="gd-tab-brigs" data-bs-toggle="tab" data-bs-target="#gd-pane-brigs" type="button" role="tab" aria-controls="gd-pane-brigs" aria-selected="false">Brigádníci</button>
            </li>
          </ul>
          <div class="tab-content pt-3">
            <div class="tab-pane fade show active" id="gd-pane-emps" role="tabpanel" aria-labelledby="gd-tab-emps"></div>
            <div class="tab-pane fade" id="gd-pane-brigs" role="tabpanel" aria-labelledby="gd-tab-brigs">
              <div id="gd-brigs-root"></div>
            </div>
          </div>
        </div>
      </div>
    `);
  }

  function renderBrigadniciRoot(root) {
    root.innerHTML = `
      <div class="card" style="background:#1f2a27;color:#e9f6ef;border:none;border-radius:10px;margin-bottom:1rem">
        <div class="card-header bg-transparent border-0"><strong>Nový brigádník</strong></div>
        <div class="card-body">
          <form class="row g-2 align-items-center" onsubmit="return false;">
            <div class="col-md">
              <input id="gd-brig-name" type="text" class="form-control" placeholder="Jméno">
            </div>
            <div class="col-md">
              <input id="gd-brig-role" type="text" class="form-control" value="Brigádník" placeholder="Role">
            </div>
            <div class="col-auto">
              <button id="gd-brig-add" class="btn btn-success">Přidat</button>
            </div>
          </form>
        </div>
      </div>

      <div class="card" style="background:#1f2a27;color:#e9f6ef;border:none;border-radius:10px;">
        <div class="card-header bg-transparent border-0"><strong>Seznam</strong></div>
        <div class="table-responsive">
          <table class="table table-dark table-striped table-hover m-0" id="gd-brigs-table">
            <thead>
              <tr>
                <th style="width:60px">ID</th>
                <th>Jméno</th>
                <th>Role</th>
                <th style="width:220px"></th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    `;

    async function load() {
      const res = await fetch('/gd/api/brigadnici');
      const data = await res.json();
      const tbody = root.querySelector('#gd-brigs-table tbody');
      tbody.innerHTML = '';
      for (const r of data) {
        const tr = document.createElement('tr');
        tr.innerHTML = \`
          <td>\${r.id}</td>
          <td>\${r.name}</td>
          <td>\${r.role}</td>
          <td class="text-end">
            <button class="btn btn-sm btn-outline-danger" data-del-id="\${r.id}">Smazat</button>
          </td>\`;
        tbody.appendChild(tr);
      }
    }

    async function add() {
      const name = root.querySelector('#gd-brig-name').value.trim();
      const role = root.querySelector('#gd-brig-role').value.trim() || 'Brigádník';
      if (!name) return;
      await fetch('/gd/api/brigadnici', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({name, role})
      });
      root.querySelector('#gd-brig-name').value='';
      await load();
    }

    async function del(id) {
      await fetch('/gd/api/brigadnici/'+id, { method:'DELETE' });
      await load();
    }

    root.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-del-id]');
      if (btn) del(btn.getAttribute('data-del-id'));
    });
    root.querySelector('#gd-brig-add').addEventListener('click', add);

    // auto load when pane becomes visible
    document.getElementById('gd-tab-brigs')?.addEventListener('shown.bs.tab', load);
  }

  function apply() {
    const container = document.querySelector('.container, .container-fluid, main, body');
    if (!container) return;

    // Collect the original Employees content
    const originalWrapper = document.createElement('div');
    // Move all direct children that are likely part of the page content.
    const markers = Array.from(container.children);
    markers.forEach(node => {
      // avoid moving <script> tags and the navbar/header if present
      if (node.tagName === 'SCRIPT' || node.tagName === 'NAV' ) return;
      originalWrapper.appendChild(node);
    });

    // Build tabs and insert
    const tabs = buildTabsContainer();
    container.appendChild(tabs);

    const paneEmps = tabs.querySelector('#gd-pane-emps');
    paneEmps.appendChild(originalWrapper);

    const brigsRoot = tabs.querySelector('#gd-brigs-root');
    renderBrigadniciRoot(brigsRoot);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', apply);
  } else {
    apply();
  }
})();
