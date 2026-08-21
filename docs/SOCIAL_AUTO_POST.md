# Social Auto-Post Setup (Zero Cost)

X (Twitter) and Facebook APIs are **not free** for new accounts in 2026.
This agent uses **Telegram + Discord** for free automatic posting.

Posts are also always saved as `social_posts_ready.md` in Artifacts for manual copy-paste to X / Facebook / Instagram / LinkedIn.

---

## Option A — Telegram (Recommended, Free)

1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow steps → copy the **Bot Token**
3. Create a channel (or use a group)
4. Add the bot as **Admin** of the channel
5. Get Chat ID:
   - Forward any message from the channel to **@userinfobot** or **@getidsbot**
   - Or open: `https://api.telegram.org/bot<TOKEN>/getUpdates` after posting in the channel
   - Channel IDs look like `-100xxxxxxxxxx`

6. GitHub → repo **Settings → Secrets and variables → Actions** → New secret:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `TELEGRAM_CHAT_ID` = your channel/group id

Done. Next daily run will auto-post to Telegram.

---

## Option B — Discord (Free)

1. Discord Server → Channel Settings → Integrations → Webhooks → New Webhook
2. Copy the **Webhook URL**
3. GitHub Secret:
   - `DISCORD_WEBHOOK_URL` = the webhook URL

---

## X / Facebook (Paid / Complex)

- X API: pay-per-use for new developers (no free posting tier)
- Facebook: needs Meta App + Page Access Token

Until you have those, use `social_posts_ready.md` from Artifacts and post manually (takes 2 minutes).

---

## Test

After adding secrets, go to Actions → PriceBD Daily Automation Agent → Run workflow → goal `social_only`.
