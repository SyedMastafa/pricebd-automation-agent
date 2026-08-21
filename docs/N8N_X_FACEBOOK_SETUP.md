# n8n: X + Facebook Auto-Post Setup (PriceBD)

এই guide দিয়ে **password ছাড়া** X ও Facebook-এ auto-post চালু করবে।

---

## Step 1 — n8n চালু করো (Free options)

### A) n8n Cloud (সহজ)
1. https://n8n.io → Sign up (free trial / starter)
2. Dashboard খুলো

### B) Self-host (সবসময় free)
```bash
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
```
Browser: `http://localhost:5678`

---

## Step 2 — Workflow import

1. n8n → **Workflows** → **Import from File**
2. File: `n8n_workflows/x_facebook_auto_post.json`  
   (repo থেকে download:  
   https://github.com/SyedMastafa/pricebd-automation-agent/blob/main/n8n_workflows/x_facebook_auto_post.json)
3. Import করো

---

## Step 3 — X (Twitter) credential

> ⚠️ ২০২৬-এ নতুন X developer account-এ posting **pay-per-use**।  
> পুরনো free/basic tier থাকলে সেটাই ব্যবহার করো।

1. https://developer.x.com → Developer Portal
2. Project + App তৈরি করো
3. App permissions: **Read and Write**
4. User authentication settings → OAuth 2.0 ON
5. Callback URL: n8n যেটা দেখায় (Credentials → X OAuth2 → copy callback)
6. n8n → **Credentials** → **Add** → **X OAuth2 API** (বা Twitter OAuth2)
7. Client ID + Client Secret দিয়ে Connect
8. Workflow-এর **Post to X** node-এ এই credential select করো

---

## Step 4 — Facebook Page credential

1. https://developers.facebook.com → My Apps → **Create App** → type: Business
2. Add product: **Facebook Login** + **pages_manage_posts**, `pages_read_engagement`
3. App → Tools → **Graph API Explorer**
4. User/Page token generate করো (Page select করে)
5. Permissions: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`
6. Token-কে **long-lived** করো (Access Token Tool)
7. n8n → Credentials → **Facebook Graph API** → paste Access Token
8. Workflow-এর **Post to Facebook Page** node:
   - Node/edge: `me/feed` (বা `{page-id}/feed`)
   - Message field: post text

**Note:** Personal profile-এ auto-post API দিয়ে করা যায় না — **Facebook Page** লাগবে।

---

## Step 5 — Webhook activate

1. Workflow-এ **Webhook** node খোলো
2. Production URL copy করো, যেমন:  
   `https://YOUR-N8N.app.n8n.cloud/webhook/pricebd-social`
3. Workflow **Active** করো (toggle ON)

---

## Step 6 — GitHub-এ webhook URL দাও

Repo → **Settings → Secrets → Actions**:

| Secret | Value |
|--------|-------|
| `N8N_WEBHOOK_URL` | তোমার n8n webhook URL |

Agent প্রতিদিন posts generate করে এই webhook-এ POST করবে → n8n X + FB-তে post করবে।

---

## Manual test

```bash
curl -X POST "https://YOUR-N8N/webhook/pricebd-social" \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [
      {
        "platform": "x",
        "text": "Test from PriceBD agent",
        "hashtags": ["#PriceBD"],
        "cta": "https://pricebd.lovable.app"
      },
      {
        "platform": "facebook",
        "text": "Test Facebook post from PriceBD",
        "hashtags": ["#PriceBD"]
      }
    ]
  }'
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| X 403 / paid | Developer portal-এ billing/credits আছে কিনা চেক |
| FB "(#200)" | Page token + `pages_manage_posts` permission |
| Webhook 404 | Workflow Active আছে কিনা |
| Duplicate posts | X/FB node-এ continueOnFail ON রাখো |

---

## Flow summary

```
GitHub Actions (daily 9 AM BST)
    → Agent generates social posts
    → POST to n8n webhook
    → n8n posts to X + Facebook Page
```

Password কখনো লাগে না — শুধু OAuth / Access Token।
