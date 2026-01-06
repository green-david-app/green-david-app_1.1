(() => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  const DEFAULT_LANG = "cs-CZ";

  function eligible(el) {
    if (!el) return false;
    if (el.dataset && el.dataset.voice === "off") return false;
    if (el.disabled || el.readOnly) return false;

    const tag = el.tagName ? el.tagName.toLowerCase() : "";
    if (tag === "textarea") return true;
    if (tag === "input") {
      const type = (el.getAttribute("type") || "text").toLowerCase();
      return ["text", "search", "email", "tel", "url"].includes(type);
    }
    return false;
  }

  function hasMic(el) {
    const p = el.parentElement;
    if (!p) return false;
    return !!p.querySelector(':scope > button.voice-mic-btn[data-for="' + el.name + '"]') ||
           !!p.querySelector(':scope > button.voice-mic-btn[data-for-id="' + el.id + '"]') ||
           !!p.querySelector(':scope > button.voice-mic-btn[data-for-el]');
  }

  function attach(el) {
    if (!eligible(el)) return;
    const p = el.parentElement;
    if (!p) return;

    // Ensure stable anchor
    p.classList.add("voice-parent");
    el.classList.add("voice-input-enabled");

    if (hasMic(el)) return;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "voice-mic-btn";
    btn.setAttribute("aria-label", "Hlasové zadávání");
    btn.title = "Hlasové zadávání";

    // Mark association (best-effort; some fields have no id/name)
    if (el.id) btn.dataset.forId = el.id;
    else if (el.name) btn.dataset.for = el.name;
    else btn.dataset.forEl = "1";

    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
           xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Z"
              stroke="currentColor" stroke-width="2"/>
        <path d="M19 11a7 7 0 0 1-14 0" stroke="currentColor" stroke-width="2"/>
        <path d="M12 18v3" stroke="currentColor" stroke-width="2"/>
        <path d="M8 21h8" stroke="currentColor" stroke-width="2"/>
      </svg>
    `;

    let recognition = null;
    let listening = false;

    function setListening(on) {
      listening = on;
      btn.classList.toggle("is-listening", on);
    }

    function stop() {
      try { recognition && recognition.stop(); } catch (e) {}
      setListening(false);
    }

    btn.addEventListener("click", () => {
      if (listening) return stop();

      recognition = new SpeechRecognition();
      recognition.lang = (el.dataset && el.dataset.voiceLang) ? el.dataset.voiceLang : DEFAULT_LANG;
      recognition.interimResults = true;
      recognition.continuous = false;

      let finalText = "";

      recognition.onstart = () => setListening(true);
      recognition.onerror = () => stop();
      recognition.onend = () => setListening(false);

      recognition.onresult = (event) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i];
          const txt = (res && res[0] && res[0].transcript) ? res[0].transcript : "";
          if (res.isFinal) finalText += txt;
          else interim += txt;
        }

        const base = el.value || "";
        const combined = (base + " " + (finalText + interim)).replace(/\s+/g, " ").trim();
        el.value = combined;

        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
      };

      try { recognition.start(); } catch (e) { stop(); }
    });

    el.addEventListener("blur", () => { if (listening) stop(); });

    p.appendChild(btn);
  }

  function scan(root) {
    const nodes = (root || document).querySelectorAll("input, textarea");
    nodes.forEach(attach);
  }

  scan(document);

  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const node of m.addedNodes) {
        if (!(node instanceof HTMLElement)) continue;
        if (node.matches && (node.matches("input") || node.matches("textarea"))) {
          attach(node);
        } else {
          scan(node);
        }
      }
    }
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();