// Cloudflare Pages Function: POST /api/follow   body: {"email": "...", "slug": "2026-10-27-some-case"}
// "Email me the verdict" on open case pages. The reader's browser has already sent the normal ColdCase Weekly
// signup to Kit (that sends the confirmation email and the free guide). This function only adds one Kit tag,
// "Verdict: <slug>", so scripts/verdict_alerts.py can email that reader the verdict when the case closes.
// Needs the Cloudflare Pages secret KIT_API_KEY (Settings > Variables and Secrets). Without it, signup still works
// and the verdict simply arrives in ColdCase Weekly.
const KIT = "https://api.kit.com/v4";
const SLUG = /^\d{4}-\d{2}-\d{2}-[a-z0-9-]{3,120}$/;
const EMAIL = /^[^\s@<>"]{1,64}@[^\s@<>"]{1,250}\.[^\s@<>"]{2,24}$/;

function reply(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}

async function openCases(request, env) {
  // Only real, open cases can be followed. The site publishes their list at /follow/index.json.
  const url = new URL("/follow/index.json", request.url);
  try {
    const r = env.ASSETS ? await env.ASSETS.fetch(url) : await fetch(url);
    return r.ok ? ((await r.json()).open || []) : [];
  } catch (e) {
    return [];
  }
}

export async function onRequestPost({ request, env }) {
  const key = String(env.KIT_API_KEY || "").trim();
  if (!key) return reply({ ok: false, reason: "not-configured" }, 503);
  let data;
  try {
    data = await request.json();
  } catch (e) {
    return reply({ ok: false, reason: "bad-request" }, 400);
  }
  const email = String(data.email || "").trim().toLowerCase();
  const slug = String(data.slug || "").trim();
  if (!EMAIL.test(email) || !SLUG.test(slug)) return reply({ ok: false, reason: "bad-request" }, 400);
  if (!(await openCases(request, env)).includes(slug)) return reply({ ok: false, reason: "not-open" }, 404);

  const headers = { "X-Kit-Api-Key": key, "Content-Type": "application/json", "Accept": "application/json" };
  // Kit returns the existing tag when one with this name already exists, so this is safe to repeat.
  const t = await fetch(`${KIT}/tags`, { method: "POST", headers, body: JSON.stringify({ name: `Verdict: ${slug}` }) });
  if (t.status === 401) return reply({ ok: false, reason: "kit-key" }, 502);
  if (!t.ok) return reply({ ok: false, reason: "kit-tag" }, 502);
  const tagId = ((await t.json()).tag || {}).id;
  if (!tagId) return reply({ ok: false, reason: "kit-tag" }, 502);

  // The browser's signup created the subscriber a moment ago; give Kit a few seconds if it is not there yet.
  for (let i = 0; i < 5; i++) {
    const r = await fetch(`${KIT}/tags/${tagId}/subscribers`, {
      method: "POST", headers, body: JSON.stringify({ email_address: email }),
    });
    if (r.status === 200 || r.status === 201) return reply({ ok: true });
    if (r.status === 401) return reply({ ok: false, reason: "kit-key" }, 502);
    await new Promise((done) => setTimeout(done, 1500));
  }
  return reply({ ok: false, reason: "subscriber-not-found-yet" }, 202);
}

export async function onRequest() {
  return reply({ ok: false, reason: "use POST" }, 405);
}
