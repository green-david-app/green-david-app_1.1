/* calendar-tasks-patch.js: non-invasive helpers for editing/deleting tasks if #tasksList is present.
   Expected markup: <ul id="tasksList"><li class="task-item" data-id="..."><span class="task-title">...</span></li></ul>
   This script only activates if the container exists; otherwise it does nothing.
*/
(function(){
  const list = document.querySelector('#tasksList');
  if (!list) return;

  list.addEventListener('click', async (e) => {
    const a = e.target.closest('a');
    if (!a) return;
    e.preventDefault();
    const li = e.target.closest('.task-item');
    if (!li) return;
    const id = +li.dataset.id;
    if (a.classList.contains('task-del')) {
      if (!confirm('Smazat úkol?')) return;
      await fetch(`/gd/api/tasks?id=${id}`, { method:'DELETE' });
      li.remove();
    } else if (a.classList.contains('task-edit')) {
      const titleEl = li.querySelector('.task-title');
      const oldTitle = titleEl ? titleEl.textContent : '';
      const newTitle = prompt('Název úkolu:', oldTitle);
      if (newTitle === null) return;
      await fetch('/gd/api/tasks', {
        method:'PATCH',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ id, title: newTitle.trim() })
      });
      if (titleEl) titleEl.textContent = newTitle.trim();
    }
  });
})();
