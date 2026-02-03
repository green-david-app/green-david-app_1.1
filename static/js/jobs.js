// static/js/jobs.js
// Kompletní přepsání logiky zakázek tak, aby:
// - detail zůstal otevřený
// - URL používá ?tab=jobs&jobId=XX
// - reload stránky zůstane na stejné zakázce
// - nic neskáče zpět na hlavní stránku

(function () {
  // Pomocné funkce pro práci s URL
  function getQueryParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
  }

  function setQueryParams(paramsObj) {
    const url = new URL(window.location.href);
    const params = url.searchParams;

    Object.keys(paramsObj).forEach((key) => {
      const value = paramsObj[key];
      if (value === null || value === undefined) {
        params.delete(key);
      } else {
        params.set(key, value);
      }
    });

    // Použijeme pushState, aby se stránka nerefreshovala
    window.history.pushState({}, "", url.toString());
  }

  // DOM prvky – ID se musí shodovat s tvým HTML
  const jobsTableBody = document.querySelector("#jobs-table-body");
  const jobDetailContainer = document.querySelector("#job-detail-container");
  const jobDetailForm = document.querySelector("#job-detail-form");
  const jobBackButton = document.querySelector("#job-detail-back");
  const jobsTabButton = document.querySelector('[data-tab="jobs"]');

  if (!jobsTableBody) {
    // Jobs tab není na této stránce – nic neděláme
    return;
  }

  let jobsCache = [];
  let employeesCache = [];

  // Načtení zakázek a členů teamu
  async function loadJobsAndEmployees() {
    const [jobsRes, employeesRes] = await Promise.all([
      fetch("/api/jobs"),
      fetch("/api/employees"),
    ]);

    if (!jobsRes.ok) {
      console.error("Chyba při načítání zakázek");
      return;
    }
    if (!employeesRes.ok) {
      console.error("Chyba při načítání členů teamu");
      return;
    }

    jobsCache = await jobsRes.json();
    employeesCache = await employeesRes.json();

    renderJobsTable();

    // po prvním načtení zkusíme z URL otevřít konkrétní job
    const jobIdFromUrl = getQueryParam("jobId");
    if (jobIdFromUrl) {
      openJobDetail(jobIdFromUrl);
    }
  }

  // Vykreslení seznamu zakázek
  function renderJobsTable() {
    jobsTableBody.innerHTML = "";

    jobsCache.forEach((job) => {
      const tr = document.createElement("tr");
      tr.dataset.jobId = job.id;

      tr.innerHTML = `
        <td>${job.id}</td>
        <td>${job.customer_name || ""}</td>
        <td>${job.vehicle || ""}</td>
        <td>${job.status || ""}</td>
        <td>${job.created_at ? new Date(job.created_at).toLocaleDateString() : ""}</td>
        <td class="jobs-actions">
          <button class="btn-small btn-detail" data-job-id="${job.id}">Detail</button>
          <button class="btn-small btn-edit" data-job-id="${job.id}">Upravit</button>
          <button class="btn-small btn-delete" data-job-id="${job.id}">Smazat</button>
        </td>
      `;

      jobsTableBody.appendChild(tr);
    });
  }

  // Pomocná funkce pro označení aktivního řádku
  function highlightSelectedRow(jobId) {
    document
      .querySelectorAll("#jobs-table-body tr")
      .forEach((row) => row.classList.remove("selected-job"));

    const row = document.querySelector(`#jobs-table-body tr[data-job-id="${jobId}"]`);
    if (row) {
      row.classList.add("selected-job");
    }
  }

  // Otevření detailu konkrétní zakázky
  async function openJobDetail(jobId) {
    if (!jobDetailContainer || !jobDetailForm) {
      console.warn("Detail zakázky nemá potřebné DOM prvky");
      return;
    }

    // Nejprve aktualizuj URL – tab=jobs + jobId
    setQueryParams({ tab: "jobs", jobId: jobId });

    try {
      const res = await fetch(`/api/jobs/${jobId}`);
      if (!res.ok) {
        console.error("Chyba při načítání detailu zakázky", jobId);
        return;
      }

      const job = await res.json();

      // vyplnit formulář / detail
      fillJobDetailForm(job);

      // zobrazit panel detailu
      jobDetailContainer.classList.remove("hidden");

      // označit řádek v tabulce
      highlightSelectedRow(jobId);
    } catch (err) {
      console.error("Výjimka při načítání detailu zakázky", err);
    }
  }

  function fillJobDetailForm(job) {
    // Zde PŘIZPŮSOB podle tvých názvů inputů!
    // Příklad:
    const idInput = jobDetailForm.querySelector('[name="id"]');
    const customerInput = jobDetailForm.querySelector('[name="customer_name"]');
    const vehicleInput = jobDetailForm.querySelector('[name="vehicle"]');
    const statusInput = jobDetailForm.querySelector('[name="status"]');
    const descriptionInput = jobDetailForm.querySelector('[name="description"]');
    const employeeSelect = jobDetailForm.querySelector('[name="employee_id"]');

    if (idInput) idInput.value = job.id ?? "";
    if (customerInput) customerInput.value = job.customer_name ?? "";
    if (vehicleInput) vehicleInput.value = job.vehicle ?? "";
    if (statusInput) statusInput.value = job.status ?? "";
    if (descriptionInput) descriptionInput.value = job.description ?? "";

    if (employeeSelect) {
      employeeSelect.innerHTML = "";
      const emptyOpt = document.createElement("option");
      emptyOpt.value = "";
      emptyOpt.textContent = "---";
      employeeSelect.appendChild(emptyOpt);

      employeesCache.forEach((emp) => {
        const opt = document.createElement("option");
        opt.value = emp.id;
        opt.textContent = emp.name;
        if (job.employee_id && Number(job.employee_id) === Number(emp.id)) {
          opt.selected = true;
        }
        employeeSelect.appendChild(opt);
      });
    }
  }

  // Uložení úprav zakázky
  async function saveJob(event) {
    event.preventDefault();

    const formData = new FormData(jobDetailForm);
    const jobId = formData.get("id");

    try {
      const res = await fetch(`/api/jobs/${jobId}`, {
        method: "PUT",
        body: formData,
      });

      if (!res.ok) {
        console.error("Chyba při ukládání zakázky");
        return;
      }

      // aktualizovat cache
      const updatedJob = await res.json();
      const idx = jobsCache.findIndex((j) => Number(j.id) === Number(updatedJob.id));
      if (idx !== -1) {
        jobsCache[idx] = updatedJob;
      }

      renderJobsTable();
      highlightSelectedRow(updatedJob.id);

      // detail necháme otevřený
      fillJobDetailForm(updatedJob);
    } catch (err) {
      console.error("Výjimka při ukládání zakázky", err);
    }
  }

  // Smazání zakázky
  async function deleteJob(jobId) {
    if (!confirm("Opravdu smazat tuto zakázku?")) return;

    try {
      const res = await fetch(`/api/jobs/${jobId}`, { method: "DELETE" });
      if (!res.ok) {
        console.error("Chyba při mazání zakázky");
        return;
      }

      // odstranit z cache
      jobsCache = jobsCache.filter((j) => Number(j.id) !== Number(jobId));
      renderJobsTable();

      // pokud byl otevřen detail právě této zakázky, schováme panel a smažeme jobId z URL
      const currentJobId = getQueryParam("jobId");
      if (currentJobId && Number(currentJobId) === Number(jobId)) {
        if (jobDetailContainer) {
          jobDetailContainer.classList.add("hidden");
        }
        setQueryParams({ tab: "jobs", jobId: null });
      }
    } catch (err) {
      console.error("Výjimka při mazání zakázky", err);
    }
  }

  // Reakce na kliknutí v tabulce zakázek
  jobsTableBody.addEventListener("click", (e) => {
    const detailBtn = e.target.closest(".btn-detail");
    const editBtn = e.target.closest(".btn-edit");
    const deleteBtn = e.target.closest(".btn-delete");

    if (detailBtn) {
      const jobId = detailBtn.dataset.jobId;
      openJobDetail(jobId);
    } else if (editBtn) {
      const jobId = editBtn.dataset.jobId;
      openJobDetail(jobId);
      // případně přepnout formulář do editačního režimu (pokud máš zvlášť)
    } else if (deleteBtn) {
      const jobId = deleteBtn.dataset.jobId;
      deleteJob(jobId);
    }
  });

  // Uložení z detail formuláře
  if (jobDetailForm) {
    jobDetailForm.addEventListener("submit", saveJob);
  }

  // Tlačítko "Zpět" v detailu – zůstane v záložce jobs, ale zavře panel detailu
  if (jobBackButton) {
    jobBackButton.addEventListener("click", (e) => {
      e.preventDefault();
      if (jobDetailContainer) {
        jobDetailContainer.classList.add("hidden");
      }
      // smažeme pouze jobId, tab necháme na "jobs"
      setQueryParams({ tab: "jobs", jobId: null });
      // zrušíme zvýraznění řádku
      document
        .querySelectorAll("#jobs-table-body tr")
        .forEach((row) => row.classList.remove("selected-job"));
    });
  }

  // Když uživatel přepne na záložku zakázek z hlavního menu, vynutíme ?tab=jobs
  if (jobsTabButton) {
    jobsTabButton.addEventListener("click", () => {
      setQueryParams({ tab: "jobs", jobId: getQueryParam("jobId") });
    });
  }

  // Reagujeme na změnu historie (např. zpět / dopředu v prohlížeči)
  window.addEventListener("popstate", () => {
    const tab = getQueryParam("tab");
    const jobId = getQueryParam("jobId");

    if (tab === "jobs") {
      if (jobId) {
        openJobDetail(jobId);
      } else {
        if (jobDetailContainer) {
          jobDetailContainer.classList.add("hidden");
        }
        document
          .querySelectorAll("#jobs-table-body tr")
          .forEach((row) => row.classList.remove("selected-job"));
      }
    }
  });

  // Start – když je stránka načtená a tab=jobs, natáhneme data
  document.addEventListener("DOMContentLoaded", () => {
    const tab = getQueryParam("tab");

    // pokud se stránka načetla s tab=jobs, natáhneme zakázky
    if (!tab || tab === "jobs") {
      loadJobsAndEmployees();
    }
  });
})();
