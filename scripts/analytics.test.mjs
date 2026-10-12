import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

function setup(profile = "", initialUrl = "https://browseawesome.com/repos/?q=private@example.com") {
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
  const location = new URL(initialUrl);
  const document = {
    currentScript: { dataset: { posthogKey: "phc_test", posthogHost: "https://us.i.posthog.com", posthogProfile: profile } },
    addEventListener: (name, callback) => { handlers[name] = callback; },
  };
  vm.runInNewContext(readFileSync("frontend/src/js/modules/analytics.js", "utf8"), {
    window: { posthog: ph, location }, document, URL, URLSearchParams,
  });
  const client = { ...ph, capture: (event, properties) => events.push({ event, properties }) };
  ph.capture = () => { throw new Error("bootstrap queue used after SDK loaded"); };
  options.loaded(client);
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

test("SDK nullable properties survive scrubbing and preserve only the public routing token", () => {
  const { options } = setup();
  const event = options.before_send({ properties: {
    token: "phc_test", $set: null, nested: { value: null, token: "secret" },
    values: [null, { password: "secret" }], authorization: "secret",
  } });
  assert.equal(event.properties.token, "phc_test");
  assert.equal(event.properties.$set, null);
  assert.equal(event.properties.nested.value, null);
  assert.equal(event.properties.nested.token, undefined);
  assert.ok(!JSON.stringify(event).includes("secret"));
  assert.equal(options.before_send({ properties: { token: "private-token" } }).properties.token, undefined);
});

test("task shortcuts emit fixed labels without link text, URLs or query input", () => {
  const { events, handlers } = setup();
  const actions = {
    "awesome-selfhosted/awesome-selfhosted": "directory_self_hosted",
    "vinta/awesome-python": "directory_python",
    "agarrharr/awesome-cli-apps": "directory_cli",
    "public-apis/public-apis": "directory_apis",
    directory_checklist: "directory_checklist",
    selfhosted_bookmarks: "selfhosted_bookmarks",
    selfhosted_checklist: "selfhosted_checklist",
  };
  for (const [input, output] of Object.entries(actions)) {
    const link = {
      href: "https://browseawesome.com/lists/renamed-list/?q=secret@example.com#private",
      textContent: "private link label",
      dataset: { discoveryAction: input },
    };
    handlers.click({ target: { closest: () => link } });
    const captured = events.at(-1);
    assert.equal(captured.event, "discovery_action_clicked");
    assert.deepEqual(JSON.parse(JSON.stringify(captured.properties)), { action: output });
  }
  assert.equal(events.filter((e) => e.event === "discovery_action_clicked").length, 7);
  assert.ok(!JSON.stringify(events).includes("secret@example.com"));
  assert.ok(!JSON.stringify(events).includes("private link label"));
});

test("unknown, inherited, unmarked and external actions are not task events", () => {
  const { events, handlers } = setup();
  for (const action of [undefined, "secret@example.com", "__proto__", "toString"]) {
    handlers.click({ target: { closest: () => ({ href: "https://browseawesome.com/lists/", dataset: { discoveryAction: action } }) } });
  }
  handlers.click({ target: { closest: () => null } });
  handlers.click({ target: { closest: () => ({ href: "https://github.com/example/repo?token=secret", dataset: { discoveryAction: "selfhosted_bookmarks" } }) } });
  assert.equal(events.filter((e) => e.event === "discovery_action_clicked").length, 0);
  assert.equal(events.at(-1).event, "github_link_clicked");
  assert.equal(events.at(-1).properties.destination, "https://github.com/example/repo");
});

test("catalog parameter names and sort values are allowlisted on load and HTMX navigation", () => {
  const { events, handlers, location } = setup("", "https://browseawesome.com/lists/?q=private@example.com&private@example.com=x&sort=secret@example.com&language=Python&language=Go&page=-1");
  const first = events.find((e) => e.event === "catalog_browsed").properties;
  assert.equal(first.has_query, true);
  assert.equal(first.sort, "default");
  assert.equal(first.page, 1);
  assert.deepEqual(Array.from(first.filter_names), ["language", "page", "sort"]);
  for (const page of ["Infinity", "NaN", "1.5", "9007199254740992"]) {
    location.href = `https://browseawesome.com/lists/?sort=scanned&page=${page}`;
    handlers["htmx:pushedIntoHistory"]();
    assert.equal(events.at(-1).properties.sort, "scanned");
    assert.equal(events.at(-1).properties.page, 1);
  }
  location.href = "https://browseawesome.com/repos/?sort=stars&page=2&topic=secret@example.com";
  handlers["htmx:historyRestore"]();
  assert.equal(events.at(-1).properties.page, 2);
  assert.equal(events.at(-1).properties.sort, "stars");
  assert.ok(!JSON.stringify(events).includes("@example.com"));
});
