import os

base_dir = os.getcwd()

# 1. Write the TechArticle JSON-LD Schema
schema_dir = os.path.join(base_dir, "layouts", "partials", "templates")
os.makedirs(schema_dir, exist_ok=True)
schema_path = os.path.join(schema_dir, "schema_json.html")

schema_content = """{{- if .IsPage }}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": {{ .Title | plainify }},
  "name": {{ .Title | plainify }},
  "description": {{ with .Description }}{{ . | plainify }}{{ else }}{{ .Summary | plainify }}{{ end }},
  "url": {{ .Permalink }},
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": {{ .Permalink }}
  },
  {{- with .Params.cover.image }}
  "image": {
    "@type": "ImageObject",
    "url": {{ . | absURL }}
  },
  {{- end }}
  "datePublished": {{ .PublishDate.Format "2006-01-02T15:04:05Z07:00" }},
  "dateModified": {{ .Lastmod.Format "2006-01-02T15:04:05Z07:00" }},
  "author": {
    "@type": "Organization",
    "name": "ColdCaseTech Intelligence Desk",
    "url": "https://coldcasetech.com"
  },
  "publisher": {
    "@type": "Organization",
    "name": "ColdCaseTech",
    "url": "https://coldcasetech.com",
    "logo": {
      "@type": "ImageObject",
      "url": "https://coldcasetech.com/images/cct_logo_final.png"
    }
  },
  "keywords": [
    {{- range $i, $tag := .Params.tags }}
      {{- if $i }}, {{ end }}{{ $tag | jsonify }}
    {{- end }}
  ],
  "articleSection": "Cybersecurity & Incident Post-Mortems",
  "inLanguage": "en-US"
}
</script>
{{- end }}
"""

with open(schema_path, "w", encoding="utf-8") as f:
    f.write(schema_content)
print("Created: layouts/partials/templates/schema_json.html")

# 2. Add contextual anchor instruction to generate_followup.py
py_path = os.path.join(base_dir, "scripts", "generate_followup.py")
if os.path.exists(py_path):
    with open(py_path, "r", encoding="utf-8") as f:
        py_code = f.read()

    target_phrase = "- Zero robotic AI filler words."
    replacement = """- Exactly ONE natural, in-text contextual anchor link woven into the root-cause or infrastructure section choosing the most relevant:
          * For breach/ransomware recovery: [immutable off-site storage](/go/contabo-storage.html) or [hardware security keys](/go/yubikey.html)
          * For infrastructure/outage/architecture: [bare-metal dedicated servers](/go/contabo-dedicated.html) or [isolated compute nodes](/go/contabo-vps6.html)
          * For surveillance/traffic monitoring: [encrypted tunnel routing](/go/surfshark-vpn.html)
        - Zero robotic AI filler words."""

    if "contextual anchor link" not in py_code and target_phrase in py_code:
        py_code = py_code.replace(target_phrase, replacement)
        with open(py_path, "w", encoding="utf-8") as f:
            f.write(py_code)
        print("Updated prompt in scripts/generate_followup.py with contextual anchor instructions.")

print("SUCCESS: Discoverability & in-text anchor setup complete.")