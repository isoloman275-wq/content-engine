# the lab Web Design — product line (2026-07-30)

Live: https://the-lab-web-design.pages.dev  (Cloudflare Pages, account aa814bdf...)

## Tiers
| Tier | Type | Price | Notes |
|------|------|-------|-------|
| Base | Template product | $49 +GST | Undercut tier, re-themeable in one CSS file |
| Polished | Template product | $179 +GST | Expert/creative, animated, original artwork |
| Korowai | Custom build 1-pg | $480 +GST | Done-for-you |
| Whare | Custom build ≤5pg | $1,200 +GST | WCAG AA, .nz help |

## Deploy source layout (_deploy/)
index.html            <- service site (custom builds + template products)
style.css, script.js
templates/base/       <- Base template demo
templates/polished/   <- Polished template demo
iwi-hapu-demo/        <- sample hapū site (fictional "Te Hapū o Ngā Wai")
functions/contact.js  <- enquiry capture → Discord webhook

## Build notes
- Original motifs only (generic te ao Māori-inspired geometry). HARD IP RULE: no copied
  iwi/hapū emblems or tukutuku patterns.
- Assemble the canonical bundle in a fresh `_deploy/` dir; let ONE session run the deploy
  to avoid parallel-session write clashes (see cloudflare-pages-deploy skill pitfalls).
- Contact form delivery requires the DISCORD_WEBHOOK secret — see
  cloudflare-pages-deploy `references/pages-functions-contact.md`.
