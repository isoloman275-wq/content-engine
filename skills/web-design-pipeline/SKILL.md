---
name: web-design-pipeline
description: "AI-automated web design build system. Ornith generates HTML/CSS/JS from client briefs. Handles freelance gigs (Fiverr/Upwork), Gumroad template products, and affiliate landing pages. Load when processing the Web Design cron."
category: devops
---

# Web Design Pipeline

## Cron: Mon/Wed/Fri 10:00 NZT

## Directory Structure

```
/path/to/projects
  queue/          <- drop BRIEF.md or JSON job here
  completed/      <- delivered builds (zip or GitHub Pages link)
  processed/      <- job file after completion
  templates/      <- reusable base templates
```

## Job Types

1. **Freelance gig** — client brief from Fiverr/Upwork, custom build, 1-3 page website
2. **Gumroad template** — no client, Ornith picks niche from trend data, builds template, sells on Gumroad
3. **Affiliate landing page** — promote specific AI tool, SEO-optimised, Ornith writes copy

## Job JSON Schema

```json
{
  "type": "freelance | template | affiliate",
  "brief": "[Full client description or template concept]",
  "pages": ["landing", "about", "pricing"],
  "style": "minimal dark | SaaS light | creative bold | corporate clean",
  "tech": "vanilla HTML/CSS/JS",
  "output_dir": "/path/to/projects]/",
  "deploy_to": "github-pages | zip | vercel",
  "price_nzd": 85
}
```

## Delegating to Ornith

```bash
# Read the job
cat /path/to/projects

# Delegate to Ornith via curl to localhost:11434
curl -s http://localhost:11434/api/generate \
  -d '{"model":"<mid-local-model>","prompt":"Build a complete responsive landing page for: [brief]. Output complete HTML, CSS, and JS as separate files. Save to [output_dir]. Include: semantic HTML5, mobile-first CSS, smooth scroll, contact form (static). No frameworks.","stream":false,"think":false,"options":{"num_predict":4096}}'
```

Or use `delegate_task` with tool access:
```python
delegate_task(
  goal="Build complete website per brief. Brief: {brief}. Save HTML/CSS/JS to {output_dir}.",
  toolsets=["file", "terminal"]
)
```

## Output Validation

```bash
# Check all expected files exist
ls /path/to/projects]/
# Expect: index.html, style.css, script.js (minimum)

# Check HTML validity (basic)
python3 -c "from html.parser import HTMLParser; HTMLParser().feed(open('index.html').read()); print('HTML OK')"

# Check mobile viewport meta tag present
grep -i 'viewport' index.html && echo 'viewport OK' || echo 'MISSING viewport meta'

# Check CSS has media queries
grep -c '@media' style.css
```

## GitHub Pages Deploy

```bash
cd /path/to/projects]/
git init
git checkout -b main
git add .
git commit -m 'Initial build'
git remote add origin git@github.com:<github-user>/[slug].git
git push -u origin main
# Then enable GitHub Pages in repo settings -> source: main branch / root
# Live URL: https://<github-user>.github.io/[slug]
```

## Gumroad Template Automation

For template products (no client), Ornith picks a niche based on trend data:

```
1. Read /path/to/projects].json
2. Identify a SaaS or product category with high Product Hunt votes
3. Brief: "Build a [niche] SaaS landing page template. Style: modern minimal. Include: hero, features, pricing (3 tiers), FAQ, CTA."
4. Delegate to Ornith
5. Package as zip
6. Gumroad listing copy: "[Niche] SaaS Landing Page Template — Fully responsive HTML/CSS/JS. No frameworks. Customise in minutes."
7. Price: NZD $15-29
```

## Pricing Reference

| Job type | Price (NZD) | Delivery |
|----------|-------------|----------|
| 1-page landing | $65-85 | 2 days |
| 3-page site | $120-180 | 3 days |
| 5-page + contact | $200-280 | 5 days |
| Gumroad template | $15-29 | digital |

The `curl http://localhost:11434/api/generate -d '{"model":"<mid-local-model>"...}'` recipe above
ASSUMES an Ollama serving `<mid-local-model>` on the local host. As of this session that is NOT true:
- MAIN-NODE (WSL/Windows) has **no `ollama` binary and no Ollama service** — `localhost:11434` is dead.
- GPU-NODE (gpu-node:11434) IS up but its model list is `gpt-oss:20b, <cloud-model>,
  qwen3-coder:30b, <thinking-model>` — **no `<mid-local-model>`**.
- AUX-NODE (aux-node:11434) has only `qwen3.5:0.8b, qwen3.5:2b-q4_K_M`.

So the curl-to-ornith build will fail with a connection error. WORKING FALLBACK (used to
build the first Gumroad template): delegate the build to a Hermes subagent that has
`file`+`terminal` tools and uses the currently-available coder model (verify with `ollama list` / current routing — do NOT hardcode a model name; model inventories change) to generate
the files. Pattern:

```python
delegate_task(
  goal=("Build a complete responsive website per this brief. Brief: {brief}. "
        "Pages: {pages}. Style: {style}. Tech: vanilla HTML/CSS/JS, no frameworks. "
        "Save index.html, style.css, script.js to {output_dir}. "
        "Include: semantic HTML5, mobile-first CSS with @media queries, viewport meta, "
        "smooth scroll, a STATIC contact form (no backend). Validate HTML parses and "
        "run `node --check script.js` before finishing. Strip any <think>...</think> blocks."),
  toolsets=["file", "terminal"]
)
```

If you specifically want Ornith, you must FIRST stand it up (install Ollama on MAIN-NODE and pull
`<mid-local-model>`, or add it to GPU-NODE's Ollama) — that is a setup task, not a build task. Until then,
use the subagent path; it produces the same HTML/CSS/JS deliverables.

Existing reference builds already in `completed/` (design_001/002/003) confirm the output
standard: semantic HTML5, viewport meta, animated CSS, no frameworks. Match that bar.

## Pitfalls

- Ornith outputs `<think>...</think>` blocks before code. Strip them from any display to client.
- Ornith may hallucinate JavaScript errors. Always run basic syntax check: `node --check script.js`
- GitHub Pages: repo must be public OR GitHub Pro for private page. Use public for client deliveries with slug that doesn't reveal client info.
- Freelance gigs: Fiverr order arrives as manual input — T1 cannot auto-ingest Fiverr orders (no API). Drop a brief manually.
- **Private-source + public-site (free)**: GitHub Pages Free 422s on private repos. For a client billboard you want to keep private, use Cloudflare Pages direct-upload — see the `cloudflare-pages-deploy` skill (handles the `production_branch` 404 pitfall + token auth). Public client-delivery repos still work on GitHub Pages.
- Always check output_dir exists before Ornith writes: `mkdir -p`
- **Cultural IP (Māori / iwi / hapū sites)**: when building for iwi, hapū, marae or any Indigenous client, NEVER reproduce a specific group's emblem, tukutuku pattern, or other intellectual property. Create ORIGINAL, generic te ao Māori-inspired motifs (koru-like curves, chevrons) and embed an IP-respect note on the site. This is a hard studio rule (HARD IP RULE) — see memory. A "studio service offering" site (e.g. the lab Web Design for iwi/hapū/local business) is a valid job type alongside freelance/Gumroad/affiliate.

- **This user's web-design directive (2026-07-30): no separate cheap HTML hub; the main WebGL site is the hub; demo REAL products, both tiers, stepped up.** When asked to "show our streams/templates", do NOT build a plain `hub.html` — integrate the hub INTO the existing WebGL main site (TE PūmanaWA) as an isolated panel (see `webgl-experience` skill, "This user's design directive"). For template products, build a REAL demo page per tier (a fictional site built *with* the template) at a "next level" aesthetic — the user was unhappy with plain, under-showcased templates. Use the `webgl-experience` skill for any showcase/build that should impress; plain HTML is a miss for this user.

## Support files
  file layout, build notes, contact-form secret requirement.
