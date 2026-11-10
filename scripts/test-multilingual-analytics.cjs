/* Regression tests for the browser-side analytics script; no external libraries. */
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");

const script = fs.readFileSync("static/js/site-preferences.js", "utf8");
const origin = "https://sqlmaniak.blog";

function simulate(source, destination, consent = "accepted") {
  const listeners = {};
  const inserted = [];
  const storage = new Map(consent ? [["sqlmaniak.analytics-consent.v1", consent]] : []);
  const config = {dataset: {measurementId: "G-LBVBW10S49"}};
  const banner = {hidden: true};
  const settings = {hidden: true};
  const openButton = {addEventListener() {}};
  const document = {
    getElementById(id) {
      return {"site-pref-config": config, "site-pref-banner": banner,
        "site-pref-settings": settings, "site-pref-open": openButton}[id] || null;
    },
    addEventListener(event, callback) {listeners[event] = callback;},
    querySelectorAll() {return [];},
    createElement() {return {};},
    head: {appendChild(element) {inserted.push(element);}}
  };
  const window = {dataLayer: []};
  const location = new URL(source, origin);
  const localStorage = {getItem(key) {return storage.get(key) || null;}, setItem(key, val) {storage.set(key, val);}};
  vm.runInNewContext(script, {document, window, location, localStorage, URL, Date, encodeURIComponent});
  assert.ok(listeners.click, "click handler must register");
  const target = {href: new URL(destination, origin).href};
  listeners.click({target: {closest(selector) {
    return selector === "a[href]" ? target : null;
  }}});
  const events = window.dataLayer.map(args => Array.from(args))
    .filter(args => args[0] === "event")
    .map(args => ({name: args[1], params: args[2]}));
  return {events, inserted, banner};
}

const scenarios = [
  ["/", "/contact/", "contact_click", "pl"],
  ["/posts/example/", "/oferta/", "offer_click", "pl"],
  ["/en/posts/example/", "/en/contact/", "contact_click", "en"],
  ["/en/posts/example/", "/en/services/", "offer_click", "en"],
  ["/de/posts/example/", "/de/contact/", "contact_click", "de"],
  ["/de/posts/example/", "/de/leistungen/", "offer_click", "de"],
  ["/en/about/", "mailto:marcin.pytlik@pracowniait.com", "contact_click", "en"],
];
for (const [source, target, eventName, lang] of scenarios) {
  const result = simulate(source, target);
  assert.equal(result.events.length, 1, source + " -> " + target);
  assert.equal(result.events[0].name, eventName);
  assert.equal(result.events[0].params.site_language, lang);
  assert.equal(result.events[0].params.source_path, source);
  assert.equal(result.inserted.length, 1, "GA must initialize after consent");
  console.log("PASS " + lang + " " + eventName + ": " + target);
}
for (const state of [null, "rejected"]) {
  const result = simulate("/de/posts/example/", "/de/contact/", state);
  assert.equal(result.events.length, 0, "Never track without consent");
  assert.equal(result.inserted.length, 0, "Never load GA before consent");
  console.log("PASS privacy: no GA before consent (" + state + ")");
}
const external = simulate("/en/", "https://example.net/");
assert.equal(external.events.length, 0, "Unrelated outbound links should not be counted as contact/offer");
console.log("All multilingual analytics regression tests passed.");
