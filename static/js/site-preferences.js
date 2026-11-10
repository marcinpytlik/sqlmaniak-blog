(function () {
  "use strict";
  const config = document.getElementById("site-pref-config");
  if (!config) return;
  const measurementId = config.dataset.measurementId;
  if (!/^G-[A-Z0-9]+$/.test(measurementId || "")) return;
  const storageKey = "sqlmaniak.analytics-consent.v1";
  const banner = document.getElementById("site-pref-banner");
  const settings = document.getElementById("site-pref-settings");
  const openButton = document.getElementById("site-pref-open");
  let started = false;

  function getChoice() {
    try { return localStorage.getItem(storageKey); } catch (_) { return null; }
  }
  function setChoice(value) {
    try { localStorage.setItem(storageKey, value); } catch (_) { /* current session only */ }
  }
  function displayBanner() {
    if (banner) banner.hidden = false;
    if (settings) settings.hidden = true;
  }
  function hidePanels() {
    if (banner) banner.hidden = true;
    if (settings) settings.hidden = true;
  }
  function startAnalytics() {
    if (started) return;
    started = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", measurementId);
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(measurementId);
    document.head.appendChild(script);
  }
  function choose(choice) {
    setChoice(choice);
    hidePanels();
    if (choice === "accepted") startAnalytics();
    // On revocation, reload to stop any further GA events from this page.
    else if (started) window.location.reload();
  }
  function track(name, params) {
    if (getChoice() !== "accepted" || !started || !window.gtag) return;
    window.gtag("event", name, params || {});
  }
  document.addEventListener("click", function (event) {
    const action = event.target.closest("[data-site-preferences]");
    if (action) {
      choose(action.dataset.sitePreferences);
      return;
    }
    const link = event.target.closest("a[href]");
    if (!link) return;
    let target;
    try { target = new URL(link.href, location.href); } catch (_) { return; }
    if (!["http:", "https:", "mailto:", "tel:"].includes(target.protocol)) return;
    const path = location.pathname;
    const language = /^\/(en|de)(?:\/|$)/.exec(path)?.[1] || "pl";
    const internal = target.origin === location.origin;
    const isContact = internal && /^\/(?:(?:en|de)\/)?contact(?:\/|$)/.test(target.pathname);
    const isOffer = internal && /^\/(?:oferta|en\/services|de\/leistungen)(?:\/|$)/.test(target.pathname);
    if (target.protocol === "mailto:" || target.protocol === "tel:" || isContact) {
      track("contact_click", {
        link_type: target.protocol === "mailto:" ? "mailto" : target.protocol === "tel:" ? "tel" : "internal",
        site_language: language,
        source_path: path
      });
    } else if (/(^|\.)easy\.tools$/i.test(target.hostname) || /(^|\.)easytools\./i.test(target.hostname)) {
      track("easytools_click", {site_language: language, source_path: path});
    } else if (isOffer) {
      track("offer_click", {site_language: language, source_path: path});
    }
  });
  document.querySelectorAll("[data-site-pref-open-settings]").forEach(function (button) {
    button.addEventListener("click", function () {
      if (settings) settings.hidden = false;
      if (banner) banner.hidden = true;
    });
  });
  if (openButton) openButton.addEventListener("click", function () {
    if (settings) settings.hidden = false;
    if (banner) banner.hidden = true;
  });
  const choice = getChoice();
  if (choice === "accepted") startAnalytics();
  else if (choice !== "rejected") displayBanner();
})();