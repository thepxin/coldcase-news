import os
import glob

base_dir = os.getcwd()
go_dir = os.path.join(base_dir, "static", "go")
os.makedirs(go_dir, exist_ok=True)

# 1. Define Contabo affiliate endpoints using your verified CJ links
endpoints = {
    "contabo": "https://www.anrdoezrs.net/click-101908427-17165311",
    "contabo-vps": "https://www.anrdoezrs.net/click-101908427-17165311",
    "contabo-dedicated": "https://www.tkqlhce.com/click-101908427-13796481",
    "contabo-storage": "https://www.kqzyfj.com/click-101908427-15239531"
}

for name, target_url in endpoints.items():
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Redirecting to Contabo Cloud...</title>
  <meta name="robots" content="noindex, nofollow">
  <script>
    (function() {{
      var target = "{target_url}";
      try {{ navigator.sendBeacon('https://coldcasetech.goatcounter.com/count?p=/go/{name}&t=Affiliate_Click_{name}'); }} catch(e) {{}}
      window.location.replace(target);
    }})();
  </script>
</head>
<body style="background:#0d1117;color:#c9d1d9;font-family:monospace;padding:40px;text-align:center;">
  <p>Routing securely to Contabo Cloud... <a href="{target_url}" style="color:#58a6ff;">Click here if not redirected</a>.</p>
</body>
</html>
"""
    file_path = os.path.join(go_dir, f"{name}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Created endpoint: static/go/{name}.html")

# 2. Patch scripts/generate_followup.py
py_path = os.path.join(base_dir, "scripts", "generate_followup.py")
if os.path.exists(py_path):
    with open(py_path, "r", encoding="utf-8") as f:
        py_code = f.read()

    if "including Contabo," not in py_code:
        py_code = py_code.replace("including Surfshark,", "including Contabo, Surfshark,")
        py_code = py_code.replace("including Surfshark, ", "including Contabo, Surfshark, ")

    storage_bullet = "- **Air-Gapped Cloud Backups:** Prevent ransomware encryption from destroying local archives — [Deploy Contabo Storage VPS]({BASE_URL}/go/contabo-storage.html)\n"
    dedicated_bullet = "- **High-Availability Failover:** Migrate mission-critical databases to isolated bare-metal hardware — [Deploy Contabo Dedicated Servers]({BASE_URL}/go/contabo-dedicated.html)\n"
    vps_bullet = "- **Isolated Cloud Sandbox:** Spin up disposable Linux environments for malware analysis and secure routing — [Deploy Contabo Core VPS]({BASE_URL}/go/contabo-vps.html)\n"

    if "go/contabo-storage.html" not in py_code:
        py_code = py_code.replace("### Verified Security & Incident Toolkit\n", "### Verified Security & Incident Toolkit\n" + storage_bullet)
    if "go/contabo-dedicated.html" not in py_code:
        py_code = py_code.replace("### Infrastructure & Network Resilience Toolkit\n", "### Infrastructure & Network Resilience Toolkit\n" + dedicated_bullet)
    if "go/contabo-vps.html" not in py_code:
        py_code = py_code.replace("### Recommended Privacy & Research Tools\n", "### Recommended Privacy & Research Tools\n" + vps_bullet)

    # Lock gemini-3.8-flash
    py_code = py_code.replace('model="gemini-2.5-flash"', 'model="gemini-3.8-flash"')
    py_code = py_code.replace('model="gemini-2.0-flash"', 'model="gemini-3.8-flash"')

    with open(py_path, "w", encoding="utf-8") as f:
        f.write(py_code)
    print("Updated scripts/generate_followup.py")

# 3. Retro-patch all existing Markdown posts
post_files = glob.glob(os.path.join(base_dir, "content", "posts", "*.md"))
for p in post_files:
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()

    changed = False
    if "including Contabo," not in content:
        content = content.replace("including Surfshark,", "including Contabo, Surfshark,")
        content = content.replace("including Surfshark, ", "including Contabo, Surfshark, ")
        changed = True

    if "contabo-" not in content and "contabo.html" not in content:
        if "### Verified Security & Incident Toolkit\n" in content:
            content = content.replace(
                "### Verified Security & Incident Toolkit\n",
                "### Verified Security & Incident Toolkit\n- **Air-Gapped Cloud Backups:** Prevent ransomware encryption from destroying local archives — [Deploy Contabo Storage VPS](https://coldcasetech.com/go/contabo-storage.html)\n"
            )
            changed = True
        if "### Infrastructure & Network Resilience Toolkit\n" in content:
            content = content.replace(
                "### Infrastructure & Network Resilience Toolkit\n",
                "### Infrastructure & Network Resilience Toolkit\n- **High-Availability Failover:** Migrate mission-critical databases to isolated bare-metal hardware — [Deploy Contabo Dedicated Servers](https://coldcasetech.com/go/contabo-dedicated.html)\n"
            )
            changed = True
        if "### Recommended Privacy & Research Tools\n" in content:
            content = content.replace(
                "### Recommended Privacy & Research Tools\n",
                "### Recommended Privacy & Research Tools\n- **Isolated Cloud Sandbox:** Spin up disposable Linux environments for malware analysis and secure routing — [Deploy Contabo Core VPS](https://coldcasetech.com/go/contabo-vps.html)\n"
            )
            changed = True

    if changed:
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Patched: {os.path.basename(p)}")

print("SUCCESS: Contabo integration complete.")