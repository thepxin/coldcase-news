// Cloudflare Pages Function: GET /api/status
// Stakeout > Outage watch: what each company's OWN status page says right now. Nothing else is used (no outage
// trackers, no guessing). Visitors' browsers only talk to coldcasetech.com; this function asks the status pages at
// most once every 2 minutes per Cloudflare location and shares the answer (Cloudflare cache).
// Anything that cannot be read shows as "unknown" (grey), never as fine (green).
// No secrets needed.

const CACHE_SECONDS = 120;
const TIMEOUT_MS = 6000;
const UA = "ColdCaseTech-status/1.0 (+https://coldcasetech.com/stakeout/)";

// Standard status pages (Atlassian Statuspage): <host>/api/v2/status.json
const STATUSPAGE = [
  ["Epic Games", "status.epicgames.com"],
  ["ChatGPT", "status.openai.com"],
  ["Claude", "status.claude.com"],
  ["GitHub", "www.githubstatus.com"],
  ["Cloudflare", "www.cloudflarestatus.com"],
  ["Discord", "discordstatus.com"],
  ["Reddit", "www.redditstatus.com"],
  ["Zoom", "status.zoom.us"],
  ["Dropbox", "status.dropbox.com"],
];

const OK_TEXT = "No problems reported";
const FAIL = (name) => ({ name, state: "unknown", text: "Couldn't read their page just now" });

async function get(url, as = "json") {
  const r = await fetch(url, {
    headers: { "user-agent": UA, accept: as === "json" ? "application/json" : "*/*" },
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return as === "json" ? r.json() : r.text();
}

async function statuspage(name, host) {
  try {
    const d = await get(`https://${host}/api/v2/status.json`);
    const ind = String((d.status || {}).indicator || "");
    const desc = String((d.status || {}).description || "").trim();
    const state = { none: "ok", minor: "minor", major: "major", critical: "critical", maintenance: "maintenance" }[ind];
    if (!state) return FAIL(name);
    return { name, state, text: state === "ok" ? OK_TEXT : desc || "Problem reported" };
  } catch (e) {
    return FAIL(name);
  }
}

// PlayStation Network: the data file behind status.playstation.com. Every "status" list is empty when all is well;
// any entry anywhere (region, country or service) means Sony is reporting something.
async function playstation() {
  const name = "PlayStation Network";
  let seen = 0;
  const services = new Set();
  let outage = false, maintenance = false;
  const note = (list, service) => {
    if (!Array.isArray(list) || !list.length) return;
    seen += 1;
    if (service) services.add(service);
    const txt = JSON.stringify(list).toLowerCase();
    if (txt.includes("outage")) outage = true;
    if (txt.includes("maintenance")) maintenance = true;
  };
  try {
    for (const region of ["SCEA", "SCEE"]) {
      let d;
      try { d = await get(`https://status.playstation.com/data/statuses/region/${region}.json`); }
      catch (e) { if (region === "SCEA") throw e; continue; }   // Americas must answer; Europe is a bonus
      if (!Array.isArray(d.countries)) throw new Error("unexpected format");
      note(d.status);
      for (const c of d.countries) {
        note(c.status);
        for (const s of c.services || []) note(s.status, s.serviceName);
      }
    }
  } catch (e) {
    return FAIL(name);
  }
  if (!seen) return { name, state: "ok", text: OK_TEXT };
  const what = [...services].slice(0, 2).join(", ");
  if (outage) return { name, state: "major", text: `Outage reported${what ? ": " + what : ""}` };
  if (maintenance && !outage) return { name, state: "maintenance", text: `Maintenance${what ? ": " + what : ""}` };
  return { name, state: "minor", text: `Problems reported${what ? ": " + what : ""}` };
}

// Xbox network: the data file behind support.xbox.com/xbox-live-status (XML). "None" means no problem.
async function xbox() {
  const name = "Xbox network";
  try {
    const x = await get("https://xnotify.xboxlive.com/servicestatusv6/US/en-US", "text");
    if (!x.includes("<ServiceStatus")) return FAIL(name);
    const incidents = (x.match(/<Incident[\s>]/g) || []).length;
    const states = [...x.matchAll(/<State>([^<]+)<\/State>/g)].map((m) => m[1].trim().toLowerCase());
    const bad = states.filter((s) => s !== "none");
    if (!incidents && !bad.length) return states.length ? { name, state: "ok", text: OK_TEXT } : FAIL(name);
    const major = bad.some((s) => /major|outage|down/.test(s));
    return { name, state: major ? "major" : "minor", text: major ? "Outage reported" : "Problems reported" };
  } catch (e) {
    return FAIL(name);
  }
}

// Rockstar: the data file behind support.rockstargames.com/servicestatus (GTA Online and, later, GTA 6).
async function rockstar() {
  const name = "Rockstar / GTA Online";
  try {
    const d = await get("https://support.rockstargames.com/services/status.json");
    const list = (d.statuses || []).filter((s) => /grand theft auto|rockstar games launcher|online services/i.test(s.name || ""));
    const values = [];
    for (const s of list) for (const p of s.services_platforms || []) values.push(String((p.service_status || {}).status || ""));
    if (!values.length) return { name, state: "link", text: "See Rockstar's own page" };
    if (values.some((v) => /down|outage/i.test(v))) return { name, state: "major", text: "Outage reported" };
    if (values.some((v) => /limited|degraded|partial|issue/i.test(v))) return { name, state: "minor", text: "Limited service reported" };
    if (values.every((v) => /up|operational|online/i.test(v))) return { name, state: "ok", text: OK_TEXT };
    return { name, state: "link", text: "See Rockstar's own page" };
  } catch (e) {
    return { name, state: "link", text: "See Rockstar's own page" };
  }
}

async function collect() {
  const jobs = [playstation(), xbox(), rockstar(), ...STATUSPAGE.map(([n, h]) => statuspage(n, h))];
  const out = await Promise.all(jobs);
  out.push({ name: "Steam", state: "none", text: "Valve publishes no status page" });
  return out;
}

export async function onRequestGet({ request, waitUntil }) {
  const cache = caches.default;
  const key = new Request(new URL("/api/status?cache=1", request.url).toString());
  const hit = await cache.match(key);
  if (hit) return hit;
  const body = JSON.stringify({ checked: new Date().toISOString(), services: await collect() });
  const res = new Response(body, {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": `public, max-age=${CACHE_SECONDS}` },
  });
  waitUntil(cache.put(key, res.clone()));
  return res;
}
