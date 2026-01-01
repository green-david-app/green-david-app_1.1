// Export utilities for Green David App
// Excel export functionality with filters

function exportToExcel(data, filename, options = {}) {
  // Create CSV content
  let csv = '';
  
  // Add headers
  if (options.headers && options.headers.length > 0) {
    csv += options.headers.map(h => `"${h}"`).join(',') + '\n';
  }
  
  // Add data rows
  data.forEach(row => {
    const values = options.columns ? 
      options.columns.map(col => row[col] || '') :
      Object.values(row);
    
    csv += values.map(val => {
      // Escape quotes and wrap in quotes
      const str = String(val || '').replace(/"/g, '""');
      return `"${str}"`;
    }).join(',') + '\n';
  });
  
  // Create blob and download
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename || 'export.csv');
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // Show success message
  if (window.showToast) {
    window.showToast('Export dokončen', 'success');
  } else {
    alert('Export dokončen!');
  }
}

function exportTimesheetsToExcel(timesheets, filters = {}) {
  const filtered = timesheets.filter(ts => {
    if (filters.employeeIds && filters.employeeIds.length > 0) {
      if (!filters.employeeIds.includes(ts.employee_id)) return false;
    }
    if (filters.projectIds && filters.projectIds.length > 0) {
      if (!filters.projectIds.includes(ts.job_id)) return false;
    }
    if (filters.dateFrom) {
      if (new Date(ts.date) < new Date(filters.dateFrom)) return false;
    }
    if (filters.dateTo) {
      if (new Date(ts.date) > new Date(filters.dateTo)) return false;
    }
    return true;
  });
  
  const headers = ['Datum', 'Zaměstnanec', 'Projekt', 'Hodiny', 'Popis'];
  const columns = ['date', 'employee_name', 'project_name', 'hours', 'description'];
  
  const data = filtered.map(ts => ({
    date: ts.date,
    employee_name: ts.employee_name || 'Neznámý',
    project_name: ts.project_name || 'Bez projektu',
    hours: ts.hours || 0,
    description: ts.description || ''
  }));
  
  exportToExcel(data, `vykazy_${new Date().toISOString().split('T')[0]}.csv`, {
    headers,
    columns
  });
}

function exportEmployeesToExcel(employees, filters = {}) {
  const filtered = employees.filter(emp => {
    if (filters.role && filters.role.length > 0) {
      if (!filters.role.includes(emp.role)) return false;
    }
    if (filters.status && filters.status.length > 0) {
      if (!filters.status.includes(emp.status)) return false;
    }
    return true;
  });
  
  const headers = ['Jméno', 'Email', 'Telefon', 'Role', 'Status', 'Hodiny tento týden', 'Aktivní projekty'];
  const columns = ['name', 'email', 'phone', 'role', 'status', 'hours_week', 'active_projects'];
  
  exportToExcel(filtered, `zamestnanci_${new Date().toISOString().split('T')[0]}.csv`, {
    headers,
    columns
  });
}

function exportJobsToExcel(jobs, filters = {}) {
  const filtered = jobs.filter(job => {
    if (filters.status && filters.status.length > 0) {
      if (!filters.status.includes(job.status)) return false;
    }
    if (filters.client && filters.client.length > 0) {
      if (!filters.client.some(c => job.client && job.client.includes(c))) return false;
    }
    return true;
  });
  
  const headers = ['Název', 'Klient', 'Status', 'Deadline', 'Pokrok %', 'Rozpočet'];
  const columns = ['title', 'client', 'status', 'deadline', 'progress', 'budget'];
  
  const data = filtered.map(job => ({
    title: job.title || job.name || '',
    client: job.client || '',
    status: job.status || '',
    deadline: job.deadline || '',
    progress: job.progress || 0,
    budget: job.budget || 0
  }));
  
  exportToExcel(data, `zakazky_${new Date().toISOString().split('T')[0]}.csv`, {
    headers,
    columns
  });
}

// Make functions globally available
window.exportToExcel = exportToExcel;
window.exportTimesheetsToExcel = exportTimesheetsToExcel;
window.exportEmployeesToExcel = exportEmployeesToExcel;
window.exportJobsToExcel = exportJobsToExcel;




