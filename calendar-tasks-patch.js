
/* calendar-tasks-patch.js
 * Ensures tasks created from the Notes tab send proper title derived from text.
 * If your page already sends 'title: "Poznámka"', this script intercepts fetch()
 * to /gd/api/tasks and replaces the body with a better title + description.
 */

(function(){
  const origFetch = window.fetch;
  window.fetch = function(input, init){
    try {
      const url = (typeof input === "string") ? input : (input?.url || "");
      if (url.includes("/gd/api/tasks") && init && typeof init.body === "string") {
        try {
          const body = JSON.parse(init.body);
          if (!body.description && body.text) body.description = body.text;
          if (!body.description && body.body) body.description = body.body;
          if (!body.title || (body.title||"").toLowerCase() === "poznámka") {
            const t = (body.description||"").trim().substring(0,40) || "Poznámka";
            body.title = t;
          }
          init.body = JSON.stringify(body);
        } catch(e){}
      }
    } catch(e){}
    return origFetch.apply(this, arguments);
  };
})();
