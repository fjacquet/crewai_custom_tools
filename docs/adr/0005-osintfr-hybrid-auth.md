# ADR 0005: Hybrid API Authentication (Free Fallback + Paid Upgrade)

**Date**: 2026-07-05  
**Author**: Gemini CLI & Collaborative Engineering Team  
**Status**: ACCEPTED  

---

## Context & Problem Statement

To incorporate premium intelligence sources from the **OSINTFR.com** directory (specifically **Epieos** reverse email lookup and **OpenCorporates** global company searches), we faced an authentication design challenge. Paid developer API keys provide high speeds and volume, but requiring them upfront restricts casual usage and raises friction for local developer checkouts. Conversely, relying strictly on free scraping is slow, fragile to web structural changes, and heavily rate-limited.

We needed an authentication strategy that provides immediate, frictionless out-of-the-box utility, while allowing enterprise-grade speed and volume upscales.

---

## Considered Alternatives

1. **Strictly Require Paid API Keys**: Fail execution instantly if `EPIEOS_API_KEY` or `OPENCORPORATES_API_KEY` are not set.
   - *Verdict*: Rejected. High barrier to entry; prevents quick testing and local developer onboarding.
2. **Strictly Rely on Free/Scraped Endpoints**: Avoid implementing official API key hooks.
   - *Verdict*: Rejected. Highly fragile; breaks under volume or when websites update their structural tags.
3. **Hybrid API Authentication** [Chosen]: Design the tools to support both modes natively. Execute keyless/scraped fallback retrievals by default with polite rate limits, and automatically upgrade to use the official, high-speed paid JSON API endpoints when API keys are available in the environment.

---

## Architectural Decisions

- **Epieos Email Lookup (`EpieosEmailLookupTool`)**: Uses a keyless scraped HTTP request by default, and automatically redirects queries to the official Epieos JSON endpoint `https://api.epieos.com/v1/reverse-lookup` when `EPIEOS_API_KEY` is present.
- **OpenCorporates Global Search (`OpenCorporatesSearchTool`)**: Conducts a keyless REST search by default, and automatically appends the `api_token` parameter when `OPENCORPORATES_API_KEY` is set.

---

## Implications & Consequences

- **Seamless Onboarding**: Tools are 100% operational immediately after editable installation with zero initial API key setups required.
- **Enterprise Ready**: Production environments can easily scale speed and request volumes simply by setting the environment variables, without requiring any modifications to the code.
