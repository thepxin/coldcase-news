---
title: "Live Threat & CVE Intelligence Radar"
description: "Real-time vulnerability telemetry, newly published CVEs, and active infrastructure remediation tools."
layout: "single"
url: "/radar/"
summary: "Live feed of critical vulnerabilities and active threat telemetry."
ShowToc: false
---

Monitor newly indexed Common Vulnerabilities and Exposures (CVEs) and active exploit telemetry in real time. Every post-mortem on **ColdCaseTech** tracks what happens *after* these advisories hit production networks.

<div id="cct-radar-app" style="margin-top: 24px;">
  <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px;">
    <div style="flex: 1; min-width: 200px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px;">
      <div style="font-size: 12px; text-transform: uppercase; color: #8b949e; letter-spacing: 1px;">Telemetry Status</div>
      <div style="font-size: 20px; font-weight: 700; color: #3fb950; margin-top: 4px;">● LIVE FEED ACTIVE</div>
    </div>
    <div style="flex: 1; min-width: 200px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px;">
      <div style="font-size: 12px; text-transform: uppercase; color: #8b949e; letter-spacing: 1px;">Primary Data Source</div>
      <div style="font-size: 20px; font-weight: 700; color: #58a6ff; margin-top: 4px;">CISA / CIRCL CVE Feed</div>
    </div>
    <div style="flex: 1; min-width: 200px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px;">
      <div style="font-size: 12px; text-transform: uppercase; color: #8b949e; letter-spacing: 1px;">Perimeter Hardening</div>
      <div style="margin-top: 6px;"><a href="/go/surfshark-suite.html" target="_blank" rel="noopener noreferrer" style="color: #f0883e; font-weight: 600; text-decoration: underline;">Deploy Zero-Trust Suite →</a></div>
    </div>
  </div>

  <div id="cve-feed-container" style="background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 18px;">
    <p style="color: #8b949e; margin: 0;">Fetching latest vulnerability advisories from global CVE telemetry...</p>
  </div>
</div>

<script>
async function loadLiveCVEs() {
  const container = document.getElementById('cve-feed-container');
  try {
    const res = await fetch('https://cve.circl.lu/api/last');
    const data = await res.json();
    const items = data.slice(0, 10);
    let html = '<h3 style="margin-top:0; border-bottom:1px solid #30363d; padding-bottom:10px;">Latest 10 Indexed Vulnerabilities (Real-Time)</h3>';
    html += '<div style="display:flex; flex-direction:column; gap:12px;">';
    items.forEach(item => {
      const id = item.id || 'CVE-ADVISORY';
      const summary = (item.summary || 'Technical advisory details pending full NVD enrichment.').slice(0, 220) + '...';
      const cvss = item.cvss ? `CVSS: ${item.cvss}` : 'Severity: Active Audit';
      const badgeColor = (item.cvss && item.cvss >= 7.0) ? '#f85149' : '#d29922';
      html += `
        <div style="padding: 12px; background: #161b22; border-left: 4px solid ${badgeColor}; border-radius: 4px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <strong style="color:#58a6ff; font-family:monospace; font-size:15px;">${id}</strong>
            <span style="font-size:12px; background:#21262d; padding:2px 8px; border-radius:4px; color:#c9d1d9;">${cvss}</span>
          </div>
          <p style="margin:0; font-size:14px; color:#c9d1d9; line-height:1.5;">${summary}</p>
        </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<p style="color:#d29922;">Browser privacy shield blocked cross-origin telemetry request. <a href="https://www.cisa.gov/known-exploited-vulnerabilities-catalog" target="_blank" rel="noopener noreferrer">View CISA KEV Catalog Directly →</a></p>';
  }
}
document.addEventListener('DOMContentLoaded', loadLiveCVEs);
</script>