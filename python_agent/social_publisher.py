"""
PriceBD Social Auto-Publisher
- Telegram Bot (free)
- Discord Webhook (free)
- n8n Webhook → X + Facebook (OAuth in n8n)
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

import httpx

logger = logging.getLogger("PriceBD-Social")

def _format_post(post: Dict[str, Any]) -> str:
    platform = post.get("platform", "general").upper()
    text = post.get("text", "")
    hashtags = post.get("hashtags") or []
    cta = post.get("cta", "")
    best_time = post.get("best_time_bst", "")

    lines = [f"[{platform}]", text]
    if hashtags:
        tags = " ".join(h if str(h).startswith("#") else f"#{h}" for h in hashtags)
        if tags not in text:
            lines.append(tags)
    if cta:
        lines.append(f"→ {cta}")
    if best_time:
        lines.append(f"Best time (BST): {best_time}")
    return "\n".join(lines)

def publish_to_telegram(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return {"ok": False, "skipped": True, "reason": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set"}

    results = []
    with httpx.Client(timeout=30) as client:
        for post in posts:
            body = _format_post(post)
            if len(body) > 4000:
                body = body[:3990] + "..."
            try:
                r = client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": body, "disable_web_page_preview": False},
                )
                data = r.json()
                results.append({
                    "platform": post.get("platform"),
                    "ok": data.get("ok", False),
                    "message_id": (data.get("result") or {}).get("message_id"),
                    "error": data.get("description"),
                })
            except Exception as e:
                logger.error("Telegram exception: %s", e)
                results.append({"platform": post.get("platform"), "ok": False, "error": str(e)})
    return {"ok": any(r.get("ok") for r in results), "results": results}

def publish_to_discord(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        return {"ok": False, "skipped": True, "reason": "DISCORD_WEBHOOK_URL not set"}

    results = []
    with httpx.Client(timeout=30) as client:
        for post in posts:
            body = _format_post(post)
            if len(body) > 1900:
                body = body[:1890] + "..."
            try:
                r = client.post(webhook, json={"content": body, "username": "PriceBD Agent"})
                ok = r.status_code in (200, 204)
                results.append({"platform": post.get("platform"), "ok": ok, "status": r.status_code})
            except Exception as e:
                logger.error("Discord exception: %s", e)
                results.append({"platform": post.get("platform"), "ok": False, "error": str(e)})
    return {"ok": any(r.get("ok") for r in results), "results": results}

def publish_to_n8n(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Send posts to n8n webhook → n8n posts to X + Facebook via OAuth."""
    url = os.getenv("N8N_WEBHOOK_URL", "").strip()
    if not url:
        return {"ok": False, "skipped": True, "reason": "N8N_WEBHOOK_URL not set"}

    payload = {"posts": posts, "source": "pricebd-agent", "site": "https://pricebd.lovable.app"}
    try:
        with httpx.Client(timeout=60) as client:
            r = client.post(url, json=payload)
            ok = r.status_code < 400
            logger.info("n8n webhook status=%s body=%s", r.status_code, r.text[:300])
            return {
                "ok": ok,
                "status": r.status_code,
                "response": r.text[:500],
                "posts_sent": len(posts),
            }
    except Exception as e:
        logger.error("n8n webhook exception: %s", e)
        return {"ok": False, "error": str(e)}

def publish_social_posts(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not posts:
        return {"ok": False, "reason": "No posts to publish"}

    summary = {
        "n8n_x_facebook": publish_to_n8n(posts),
        "telegram": publish_to_telegram(posts),
        "discord": publish_to_discord(posts),
    }

    any_ok = any(v.get("ok") for v in summary.values() if not v.get("skipped"))
    any_configured = any(not v.get("skipped") for v in summary.values())

    return {"ok": any_ok, "configured": any_configured, "details": summary}

def save_ready_to_post_file(posts: List[Dict[str, Any]], path: str = "social_posts_ready.md") -> str:
    lines = [
        "# PriceBD – Ready to Post Social Content",
        "Generated for: https://pricebd.lovable.app",
        "",
        "Copy-paste these to X, Facebook, LinkedIn, Instagram.",
        "",
    ]
    for i, post in enumerate(posts, 1):
        platform = post.get("platform", "general").upper()
        lines.append(f"## {i}. {platform}")
        lines.append("")
        lines.append(post.get("text", ""))
        hashtags = post.get("hashtags") or []
        if hashtags:
            lines.append("")
            lines.append(" ".join(h if str(h).startswith("#") else f"#{h}" for h in hashtags))
        if post.get("cta"):
            lines.append("")
            lines.append(f"CTA: {post['cta']}")
        if post.get("best_time_bst"):
            lines.append(f"Best time (BST): {post['best_time_bst']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Saved ready-to-post file → %s", path)
    return path
