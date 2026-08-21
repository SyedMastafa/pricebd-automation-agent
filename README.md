# PriceBD Zero-Cost Full Automation Agent

**Everything runs from GitHub. You do almost nothing.**

- **Brand:** PriceBD  
- **URL:** https://pricebd.lovable.app  
- **Tone:** Professional, clear, helpful, trustworthy, data-driven  
- **Cost:** ৳0 (GitHub Actions + Groq free tier + Vercel free)

## How it works

```
GitHub Actions (daily 9 AM BST)
        ↓
Python LangGraph Agent
        ├── SEO Agent
        ├── Content Agent
        ├── Social Agent
        └── Reply Agent
        ↓
Report saved as GitHub Artifact
```

Optional: Same code also deploys as API on Vercel.

## One-time Setup (5–10 minutes)

Follow this guide → **[docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md)**

Summary:
1. Create a new GitHub repository
2. Upload this entire folder
3. Add `GROQ_API_KEY` as repository secret
4. Run the workflow once manually to test
5. Done — it will run automatically every day

## Folder Structure

```
zero-cost-automation-agent/
├── .github/workflows/
│   └── daily-agent.yml          ← Daily automatic run
├── python_agent/
│   ├── main.py                  ← Full multi-agent brain
│   ├── api.py                   ← FastAPI (for Vercel)
│   ├── requirements.txt
│   ├── test_agent.py
│   └── vercel.json
├── n8n_workflows/               ← Optional visual orchestrator
├── config/
│   └── .env.example
├── docs/
│   ├── GITHUB_SETUP.md          ← Start here
│   ├── SETUP_GUIDE.md
│   └── VERCEL_DEPLOY.md
└── README.md
```

## Available Goals

| Goal              | What it does                              |
|-------------------|-------------------------------------------|
| full_daily_run    | SEO → Content → Social → Reply → Report   |
| seo_only          | Only SEO analysis                         |
| content_only      | Only content + social captions            |
| social_only       | Only refine social posts                  |
| reply_only        | Only reply templates                      |

## Free Services Used

- GitHub Actions (2000 minutes/month free)
- Groq API (generous free tier)
- Vercel (optional, free hobby plan)
- No credit card needed

## Next Improvements (just ask)

- Bangla content generation
- Real Google Search Console data
- Auto-post to X (Twitter)
- HubSpot lead replies
- Email the daily report to you

---
**Status:** Fully ready for GitHub. Just push and add the secret.
