---
name: referral-link-promotion
description: "Promote referral links via honest short-form demos."
version: 1.0.0
license: MIT
---

# Referral Link Promotion

Turn affiliate/referral programs into short-form video promos that convert
without hype. The pitch is the creator's real setup: demo the product as it
is actually used, cite verifiable numbers, let the viewer opt in via the link.

## Always-on rules

- **No borrowed or invented stories.** Never script a journey the creator did
  not live ("I switched from $X to $Y"). A technical audience destroys
  fabricated claims in the comments, and one caught lie kills the account.
  State what the product is, what it beats, and what it loses.
- **Claims come from live primary sources.** Pull the vendor's own published
  benchmark/pricing table fresh each promo — pick the 2-3 rows where the
  product wins or sits within noise of a frontier rival. Vendor tables age
  monthly; citing from memory produces a wrong number burned into a video.
- **Price comparisons must not imply bundling.** Say "priced roughly the same
  as A and B" (each individually) — never "A and B combined" unless the
  products are literally sold as one bundle.
- **Referral mechanics come from the program's official rules page, live.**
  Extract before scripting: reward type (cash vs platform credits — most are
  credits, not money), payout unlock threshold, friend-side discount, claim
  window after click, and multi-link attribution rule. A promo promising cash
  for a credits-only program is a false claim.
- **The link goes in the caption AND a pinned comment** — pinned comments sit
  above the caption and survive scrolling. The discount line (e.g. "10% off
  first order") rides with the link, verified against the rules page.

## Procedure

1. Pull the program rules page (see extraction list above); note exact numbers
   for the caption.
2. Research the product's live benchmark table; choose the honest headline
   (a near-tie with a frontier model is itself the story — "close enough"
   converts without overclaiming).
3. Script ≤25s. Hook states what the product IS (never a price-shock story);
   mid-roll shows verified numbers as on-screen text; end card = link CTA.
   Budget ~1.6-2 words/second for TTS voiceover — a 25s short is ~40-50 VO
   words. Generate the VO file, measure it, and rescale the script if it
   overruns; never script to a word count on faith.
4. Generate visuals through the cloud-video-generation skill (vertical 9:16,
   budget gate applies). Two shots (15s+10s) chain into one short cleanly.
   TTS VO → proportional SRT with pinned last caption → duck ambient under VO
   → burn captions → frame-level vision QA.
6. Deliver the final mp4 + paste-ready caption to the creator for review.
   NEVER auto-post: the creator uploads from their own account and pins the
   link comment themselves. Auto-posting bypasses the account owner's final
   say on a public, monetized claim.

## Caption shape

```
[line 1: the honest hook — what it is + who it runs for]
[2-3 lines: the verified numbers / how it is actually used]
[discount line + link]
[5-8 niche hashtags]
```

Same link duplicated as pinned comment text. Hashtags: the tool names people
search for first, product/account tags last.
