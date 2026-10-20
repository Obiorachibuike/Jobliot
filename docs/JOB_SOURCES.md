# Job Sources
Implemented & verified against public docs:
- **Remotive** (`https://remotive.com/api/remote-jobs`) — no key, remote jobs.
- **Greenhouse** (`https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`) — no key; needs the company's board token (from their careers URL).
- **Lever** (`https://api.lever.co/v0/postings/{company}?mode=json`) — no key; needs company slug.
- **URL import** — any public job page (SSRF-protected), with manual-correction step.
- **Manual entry** — always available.
Not implemented (and intentionally so): LinkedIn/Indeed etc. require partner agreements and ban scraping. CareerPilot never bypasses logins/CAPTCHAs/anti-bot. Dedup uses normalized URL + source id + title/company fingerprint. Scheduled discovery runs only while the app is open (stated in UI).
