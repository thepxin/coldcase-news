// ColdCaseTech timer (a Cloudflare Worker).
// GitHub's own schedule often starts runs hours late. This Worker wakes up on time and presses "Run workflow"
// on GitHub for us, so the articles and the live feeds start on time. GitHub's own schedule stays as a backup.
//
// Setup (once): paste this whole file into a Cloudflare Worker, add the secret GITHUB_TOKEN (a GitHub token that can
// only run Actions on thepxin/coldcase-news), and add ONE cron trigger:  17,41,47 * * * *
// The Worker wakes 3 times an hour and only acts at the times in JOBS below (UTC). It has no web page: opening its
// address does nothing, so nobody can start a run from outside.

const REPO = "thepxin/coldcase-news";

// Times are UTC (India is UTC + 5:30). Keep them the same as the cron lines in the workflow files.
const JOBS = [
  { name: "daily article (08:11, 14:11 and 20:11 IST)", hours: [2, 8, 14], minute: 41,
    workflow: "daily_news.yml", inputs: { desk: "auto", run_kind: "slot" } },
  { name: "catch-up run (23:17 IST)", hours: [17], minute: 47,
    workflow: "daily_news.yml", inputs: { desk: "auto", run_kind: "catchup" } },
  { name: "live feeds (every 3 hours)", hours: [0, 3, 6, 9, 12, 15, 18, 21], minute: 17,
    workflow: "feeds.yml", inputs: null },
];

function jobsAt(date) {
  const h = date.getUTCHours(), m = date.getUTCMinutes();
  return JOBS.filter((j) => j.minute === m && j.hours.includes(h));
}

async function start(job, env, wait = (ms) => new Promise((r) => setTimeout(r, ms))) {
  if (!env.GITHUB_TOKEN) {
    console.error("Not started: the secret GITHUB_TOKEN is missing in this Worker's settings.");
    return "no-token";
  }
  const body = { ref: "main" };
  if (job.inputs) body.inputs = job.inputs;
  for (let attempt = 1; attempt <= 3; attempt++) {
    let status = 0, text = "";
    try {
      const r = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${job.workflow}/dispatches`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "coldcasetech-timer",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      status = r.status;
      if (r.ok) {
        console.log(`Started on GitHub: ${job.name}`);
        return "started";
      }
      text = (await r.text()).slice(0, 300);
    } catch (e) {
      text = String(e).slice(0, 300);
    }
    console.error(`GitHub did not start "${job.name}" (try ${attempt}): ${status || "no answer"} ${text}`);
    // 401 = token wrong or expired, 403 = token lacks "Actions: Read and write", 404 = wrong repo or file,
    // 422 = workflow input not accepted. Trying again will not help with those.
    if (status >= 400 && status < 500 && status !== 429) return "failed";
    if (attempt < 3) await wait(20000);
  }
  return "failed";
}

export default {
  async scheduled(event, env, ctx) {
    for (const job of jobsAt(new Date(event.scheduledTime))) ctx.waitUntil(start(job, env));
  },
  async fetch() {
    return new Response("Nothing here.", { status: 404 });
  },
};
