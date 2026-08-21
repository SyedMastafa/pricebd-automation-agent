# Everything Runs from GitHub (Zero Local Work)

তুমি শুধু একবার GitHub-এ setup করবে। তারপর সবকিছু automatic চলবে।

## 1. Repository already created

Repo: https://github.com/SyedMastafa/pricebd-automation-agent

## 2. Add Free API Key as Secret

1. Repo → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Name: `GROQ_API_KEY`
4. Value: তোমার Groq API key (https://console.groq.com)
5. (Optional) `GOOGLE_API_KEY`

## 3. Enable & Test GitHub Actions

1. Repo → **Actions** tab
2. Enable workflows if prompted
3. **PriceBD Daily Automation Agent** → **Run workflow** → full_daily_run
4. Report will appear in **Artifacts**

## 4. Automatic Daily Run

- প্রতিদিন সকাল ৯টা (Bangladesh time)
- Report GitHub Artifacts-এ সেভ হবে (৩০ দিন)

## 5. (Optional) Deploy API to Vercel from this repo

1. Vercel → New Project → Import this GitHub repo
2. Root Directory: `python_agent`
3. Environment Variables: `GROQ_API_KEY`
4. Deploy

---
**Status:** Code is already pushed. Just add the secret and run once.
