// Deep-linking to Jobs tab + specific job detail from URL parameters.
// If URL looks like: /?tab=jobs&jobId=24, this script will:
//  1) switch to the Zakázky (jobs) tab
//  2) after the jobs list is rendered, automatically open the detail of job with ID = 24.

(function () {
  function getUrlParam(name) {
    var params = new URLSearchParams(window.location.search);
    var value = params.get(name);
    return value && value !== "" ? value : null;
  }

  var tabParam = getUrlParam("tab");
  var jobIdParam = getUrlParam("jobId");
  if (!jobIdParam) {
    return; // nothing to do
  }

  // Normalize to string & number version so we can match both.
  var jobIdStr = String(jobIdParam);
  var jobIdNum = parseInt(jobIdParam, 10);
  if (isNaN(jobIdNum)) {
    jobIdNum = null;
  }

  function clickIfExists(selector) {
    var el = document.querySelector(selector);
    if (el) {
      el.click();
      return true;
    }
    return false;
  }

  // On DOM ready, optionally switch to Jobs tab first.
  document.addEventListener("DOMContentLoaded", function () {
    if (tabParam === "jobs") {
      // Try several reasonable selectors for the Zakázky tab button/link.
      var clicked =
        clickIfExists('[data-gd-tab="jobs"]') ||
        clickIfExists("#gd-tab-jobs") ||
        clickIfExists('button[role="tab"][data-target="#gd-pane-jobs"]') ||
        clickIfExists('a[href="#jobs"]') ||
        clickIfExists('a[href="#gd-pane-jobs"]');

      // If nothing was clicked, we still continue – maybe Jobs is default tab.
    }

    var attempts = 0;
    var maxAttempts = 40; // ~10s total (40 * 250ms)

    var intervalId = setInterval(function () {
      attempts += 1;

      // Candidate selectors for job rows / tiles.
      var candidates = [
        // generic rows with data-job-id
        '[data-job-id="' + jobIdStr + '"]',
        '[data-job-id="' + jobIdNum + '"]',

        // table rows
        'tr[data-job-id="' + jobIdStr + '"]',
        'tr[data-job-id="' + jobIdNum + '"]',

        // list items or cards
        'li[data-job-id="' + jobIdStr + '"]',
        'li[data-job-id="' + jobIdNum + '"]',
        'div[data-job-id="' + jobIdStr + '"]',
        'div[data-job-id="' + jobIdNum + '"]'
      ];

      var target = null;
      for (var i = 0; i < candidates.length; i++) {
        var el = document.querySelector(candidates[i]);
        if (el) {
          target = el;
          break;
        }
      }

      if (target) {
        // Prefer an explicit "detail" button/link inside the row/card.
        var detail =
          target.querySelector('[data-action="detail"]') ||
          target.querySelector(".btn-detail") ||
          target.querySelector(".job-detail") ||
          target.querySelector('a[href*="/jobs/"]') ||
          target.querySelector("a") ||
          target.querySelector("button");

        (detail || target).click();
        clearInterval(intervalId);
        return;
      }

      if (attempts >= maxAttempts) {
        clearInterval(intervalId);
      }
    }, 250);
  });
})();
