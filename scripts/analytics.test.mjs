import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

function setup(profile = "") {
  const events = [];
  const handlers = {};
  let options;
  const ph = {
    init: (_key, opts) => { options = opts; },
    capture: (event, properties) => events.push({ event, properties }),
    identify: (id) => events.push({ event: "identify", id }),
    register: () => {},
    get_property: () => null,
    get_distinct_id: () => "anon-id",
    get_session_id: () => "session-id",
  };
  const location = { origin: "https://browseawesome.com", pathname: "/repos/", search: "?q=private@example.com", href: "https://browseawesome.com/repos/?q=private@example.com" };
  const document = {
    currentScript: { dataset: { posthogKey: "phc_test", posthogHost: "https://us.i.posthog.com", posthogProfile: profile } },
    addEventListener: (name, callback) => { handlers[name] = callback; },
  };
  vm.runInNewContext(readFileSync("frontend/src/js/modules/analytics.js", "utf8"), {
    window: { posthog: ph, location }, document, URL, URLSearchParams,
  });
  options.loaded(ph);
  return { events, handlers, location, options };
}

test("one pageview per HTMX URL transition, no raw query", () => {
  const { events, handlers, location } = setup();
  handlers["htmx:pushedIntoHistory"]();
  assert.equal(events.filter((e) => e.event === "$pageview").length, 1);
  location.href = "https://browseawesome.com/repos/?q=other";
  handlers["htmx:pushedIntoHistory"]();
  assert.equal(events.filter((e) => e.event === "$pageview").length, 2);
  assert.ok(!JSON.stringify(events).includes("private@example.com"));
});

test("profile identification and private URL redaction", () => {
  const { events, options } = setup("123");
  assert.equal(events[0].id, "123");
  const event = options.before_send({ properties: { $current_url: "https://browseawesome.com/accounts/confirm/secret?token=secret" } });
  assert.equal(event.properties.$current_url, "https://browseawesome.com/[private]");
});
