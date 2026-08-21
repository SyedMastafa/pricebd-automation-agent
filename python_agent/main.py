"""
PriceBD Zero-Cost Full Automation Agent
Hybrid: n8n + Python LangGraph
Central Brain + SEO + Content + Social + Reply Agents
Free LLMs: Groq (primary) / Gemini (fallback)
Social auto-post: Telegram + Discord (free)
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from social_publisher import publish_social_posts, save_ready_to_post_file

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("PriceBD-Agent")

def extract_json(text: str) -> Any:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = re.sub(r"\s*```", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                continue
    logger.warning("Failed to parse JSON. Raw preview: %s", text[:300])
    return {"raw": text[:500], "error": "json_parse_failed"}

def safe_get(d: Dict, *keys, default=None):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d

def get_llm(temperature: float = 0.3, creative: bool = False):
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    temp = 0.6 if creative else temperature
    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    if provider == "groq" and os.getenv("GROQ_API_KEY"):
        return ChatGroq(
            model=model_name,
            temperature=temp,
            api_key=os.getenv("GROQ_API_KEY"),
            max_retries=2
        )
    elif os.getenv("GOOGLE_API_KEY"):
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=temp,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    else:
        raise ValueError("No LLM API key found. Set GROQ_API_KEY or GOOGLE_API_KEY in .env")

def get_brand_info() -> Dict[str, str]:
    return {
        "name": os.getenv("BRAND_NAME", "PriceBD"),
        "url": os.getenv("WEB_APP_URL", "https://pricebd.lovable.app"),
        "voice": os.getenv(
            "BRAND_VOICE",
            "Professional, clear, helpful, trustworthy, data-driven. "
            "Focus on helping Bangladeshi users find the best prices and deals."
        ),
        "description": os.getenv(
            "BRAND_DESCRIPTION",
            "PriceBD is a live price comparison platform for Bangladesh. "
            "It compares prices, stock and ratings across major stores like Daraz, Star Tech, Ryans and more. "
            "Prices refresh every few hours. Users can track price drops and find the best deals."
        )
    }

class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    current_goal: str
    seo_insights: Dict[str, Any]
    content_ideas: List[Dict]
    social_posts: List[Dict]
    reply_suggestions: List[Dict]
    actions_taken: List[str]
    final_report: str
    brand_info: Dict[str, str]
    error: Optional[str]
    publish_result: Optional[Dict]

def seo_agent(state: AgentState) -> AgentState:
    logger.info("Running SEO Agent...")
    brand = state.get("brand_info") or get_brand_info()

    prompt = f"""You are an expert SEO strategist for {brand['name']} ({brand['url']}).
Brand voice: {brand['voice']}
Product: {brand['description']}

Date: {datetime.now().strftime('%Y-%m-%d')}
Market: Bangladesh (English + Bangla searchers)

Focus on high-intent keywords:
- iPhone 16 price in Bangladesh
- best laptop under 50000 BD
- Daraz vs Star Tech
- Samsung TV price BD
- price drop alerts Bangladesh

Tasks:
1. 8 high-potential keywords with priority (high/medium).
2. Meta title + description for homepage, one brand page (Apple), one category (Laptops).
3. 4 technical SEO wins for a price comparison site.
4. Internal linking ideas.

IMPORTANT: Return ONLY a valid JSON object. No markdown, no explanation, no code fences.

{{
  "priority_keywords": [{{"keyword": "...", "intent": "transactional", "priority": "high"}}],
  "content_topics": [{{"title": "...", "keyword": "...", "search_intent": "...", "priority": "high"}}],
  "meta_suggestions": [{{"page": "homepage", "title": "...", "description": "..."}}],
  "technical_wins": ["..."],
  "internal_linking": ["..."]
}}"""

    try:
        llm = get_llm(temperature=0.2)
        response = llm.invoke([HumanMessage(content=prompt)])
        insights = extract_json(response.content)
        if not isinstance(insights, dict) or insights.get("error"):
            insights = {"error": str(insights), "content_topics": []}
    except Exception as e:
        logger.error(f"SEO Agent error: {e}")
        insights = {"error": str(e), "content_topics": []}

    state["seo_insights"] = insights
    state["actions_taken"] = state.get("actions_taken", []) + ["SEO analysis completed"]
    return state

def content_agent(state: AgentState) -> AgentState:
    logger.info("Running Content Agent...")
    brand = state.get("brand_info") or get_brand_info()
    seo = state.get("seo_insights", {}) or {}
    topics = safe_get(seo, "content_topics", default=[]) or []
    topics = topics[:3]

    if not topics:
        topics = [
            {"title": "How to Find the Best iPhone Deals in Bangladesh", "keyword": "iPhone price in Bangladesh", "search_intent": "informational", "priority": "high"},
            {"title": "Best Laptops Under 50000 BDT in 2026", "keyword": "best laptop under 50000 BD", "search_intent": "informational", "priority": "high"},
            {"title": "Daraz vs Star Tech Price Comparison", "keyword": "Daraz vs Star Tech", "search_intent": "informational", "priority": "high"}
        ]

    prompt = f"""You are a content marketing expert for {brand['name']}.
Brand voice: {brand['voice']}
Website: {brand['url']}
About: {brand['description']}

Audience: Bangladeshi shoppers looking for lowest prices.

Use these topics:
{json.dumps(topics, ensure_ascii=False)}

Generate:
1. For each of the 3 topics: blog title, keyword, outline (3-5 H2s), and a 120-word introduction that mentions live price comparison on PriceBD.
2. Exactly 4 social captions (platforms: x, linkedin, facebook, instagram).
3. One newsletter with subject, preview_text, outline.

IMPORTANT: Return ONLY a valid JSON object. No markdown fences, no extra text.

{{
  "blog_drafts": [
    {{"title": "...", "keyword": "...", "outline": ["H2: ...", "H2: ..."], "introduction": "..."}}
  ],
  "social_captions": [
    {{"platform": "x", "text": "...", "hashtags": ["#PriceBD"]}},
    {{"platform": "linkedin", "text": "..."}},
    {{"platform": "facebook", "text": "..."}},
    {{"platform": "instagram", "text": "..."}}
  ],
  "newsletter": {{"subject": "...", "preview_text": "...", "outline": "..."}}
}}"""

    try:
        llm = get_llm(creative=True)
        response = llm.invoke([HumanMessage(content=prompt)])
        logger.info("Content Agent raw response length: %s", len(response.content or ""))
        data = extract_json(response.content)
        if not isinstance(data, dict):
            data = {}
        state["content_ideas"] = data.get("blog_drafts") or []
        state["social_posts"] = data.get("social_captions") or []
        if isinstance(state.get("seo_insights"), dict):
            state["seo_insights"]["newsletter"] = data.get("newsletter") or {}
        logger.info("Content ideas: %s | Social posts: %s", len(state["content_ideas"]), len(state["social_posts"]))
    except Exception as e:
        logger.error(f"Content Agent error: {e}")
        state["content_ideas"] = []
        state["social_posts"] = []

    state["actions_taken"] = state.get("actions_taken", []) + ["Content generation completed"]
    return state

def social_agent(state: AgentState) -> AgentState:
    logger.info("Running Social Agent...")
    brand = state.get("brand_info") or get_brand_info()
    posts = state.get("social_posts") or []

    if not posts:
        posts = [
            {"platform": "x", "text": f"Find the lowest prices in Bangladesh on {brand['name']}. Live comparison from Daraz, Star Tech & more. {brand['url']}", "hashtags": ["#PriceBD", "#BDDeals"]},
            {"platform": "facebook", "text": f"Tired of checking multiple sites for the best price? {brand['name']} compares live prices across major stores in Bangladesh. Start saving today! {brand['url']}", "hashtags": ["#PriceBD"]}
        ]
        state["social_posts"] = posts
        state["actions_taken"] = state.get("actions_taken", []) + ["Social posts generated (fallback)"]
    else:
        prompt = f"""You are a social media expert for {brand['name']} ({brand['url']}).
Brand voice: {brand['voice']}

Improve these posts. Keep them engaging, add max 3 hashtags, suggest best time (Bangladesh).
Always include the website URL in the text or CTA.

Current posts:
{json.dumps(posts, ensure_ascii=False)}

IMPORTANT: Return ONLY a valid JSON array. No markdown, no explanation.

[
  {{"platform": "x", "text": "...", "hashtags": ["#PriceBD"], "best_time_bst": "10:00 AM", "cta": "Compare on PriceBD"}}
]"""

        try:
            llm = get_llm(creative=True)
            response = llm.invoke([HumanMessage(content=prompt)])
            refined = extract_json(response.content)
            if isinstance(refined, list) and refined:
                state["social_posts"] = refined
            else:
                state["social_posts"] = posts
        except Exception as e:
            logger.error(f"Social Agent error: {e}")

        state["actions_taken"] = state.get("actions_taken", []) + ["Social posts refined"]

    # Always save ready-to-post file + auto-publish if credentials exist
    final_posts = state.get("social_posts") or []
    try:
        save_ready_to_post_file(final_posts, "social_posts_ready.md")
        pub = publish_social_posts(final_posts)
        state["publish_result"] = pub
        if pub.get("ok"):
            state["actions_taken"] = state.get("actions_taken", []) + ["Social posts auto-published"]
            logger.info("Social auto-publish OK: %s", pub)
        elif pub.get("configured"):
            state["actions_taken"] = state.get("actions_taken", []) + ["Social publish attempted (partial)"]
        else:
            state["actions_taken"] = state.get("actions_taken", []) + ["Social posts saved (no Telegram/Discord secrets)"]
            logger.info("No social secrets — posts saved to social_posts_ready.md only")
    except Exception as e:
        logger.error(f"Publish error: {e}")
        state["actions_taken"] = state.get("actions_taken", []) + [f"Publish error: {e}"]

    return state

def reply_agent(state: AgentState) -> AgentState:
    logger.info("Running Reply Agent...")
    brand = state.get("brand_info") or get_brand_info()

    prompt = f"""You are a customer success agent for {brand['name']}.
Brand voice: {brand['voice']}
Website: {brand['url']}
About: {brand['description']}

Create ready-to-send reply templates for:
1. "Is this the lowest price?"
2. Wrong / outdated price report
3. Price alert request
4. How often prices update
5. Comparison with another site
6. Positive feedback
7. Specific product availability
8. How PriceBD works

IMPORTANT: Return ONLY valid JSON. No markdown.

{{
  "templates": [
    {{"situation": "...", "reply": "...", "follow_up_action": "..."}}
  ]
}}"""

    try:
        llm = get_llm(temperature=0.3)
        response = llm.invoke([HumanMessage(content=prompt)])
        data = extract_json(response.content)
        if isinstance(data, dict):
            state["reply_suggestions"] = data.get("templates") or []
        else:
            state["reply_suggestions"] = []
    except Exception as e:
        logger.error(f"Reply Agent error: {e}")
        state["reply_suggestions"] = []

    state["actions_taken"] = state.get("actions_taken", []) + ["Reply templates generated"]
    return state

def report_agent(state: AgentState) -> AgentState:
    logger.info("Generating final report...")
    brand = state.get("brand_info") or get_brand_info()
    now = datetime.now().strftime("%Y-%m-%d %H:%M BST")

    report_lines = [
        f"# PriceBD Daily Automation Report",
        f"**Date:** {now}",
        f"**Website:** {brand['url']}",
        "",
        "## Actions Completed",
    ]
    for action in state.get("actions_taken", []):
        report_lines.append(f"- {action}")

    pub = state.get("publish_result") or {}
    if pub:
        report_lines += ["", "## Social Auto-Publish", "```json", json.dumps(pub, ensure_ascii=False, indent=2), "```"]

    report_lines += [
        "",
        "## SEO Insights",
        "```json",
        json.dumps(state.get("seo_insights", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Content Ideas (Blog Drafts)",
        "```json",
        json.dumps(state.get("content_ideas", []), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Social Posts Ready to Publish",
        "```json",
        json.dumps(state.get("social_posts", []), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Reply Templates",
        "```json",
        json.dumps(state.get("reply_suggestions", []), ensure_ascii=False, indent=2),
        "```",
        "",
        "---",
        "*Generated by PriceBD Zero-Cost Automation Agent*"
    ]

    state["final_report"] = "\n".join(report_lines)
    return state

def central_brain(state: AgentState) -> AgentState:
    goal = state.get("current_goal", "full_daily_run")
    logger.info(f"Central Brain started | Goal: {goal}")
    state["brand_info"] = get_brand_info()
    state["actions_taken"] = [f"Central brain started with goal: {goal}"]
    state["error"] = None
    return state

def route_after_brain(state: AgentState) -> str:
    goal = state.get("current_goal", "full_daily_run")
    mapping = {
        "seo_only": "seo",
        "content_only": "content",
        "social_only": "social",
        "reply_only": "reply",
        "full_daily_run": "seo"
    }
    return mapping.get(goal, "seo")

def should_continue_to_content(state: AgentState) -> str:
    goal = state.get("current_goal", "full_daily_run")
    if goal in ("full_daily_run", "content_only"):
        return "content"
    return "report"

def should_continue_to_social(state: AgentState) -> str:
    goal = state.get("current_goal", "full_daily_run")
    if goal in ("full_daily_run", "social_only"):
        return "social"
    return "report"

def should_continue_to_reply(state: AgentState) -> str:
    goal = state.get("current_goal", "full_daily_run")
    if goal in ("full_daily_run", "reply_only"):
        return "reply"
    return "report"

def build_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("brain", central_brain)
    workflow.add_node("seo", seo_agent)
    workflow.add_node("content", content_agent)
    workflow.add_node("social", social_agent)
    workflow.add_node("reply", reply_agent)
    workflow.add_node("report", report_agent)
    workflow.set_entry_point("brain")
    workflow.add_conditional_edges("brain", route_after_brain, {"seo": "seo", "content": "content", "social": "social", "reply": "reply"})
    workflow.add_conditional_edges("seo", should_continue_to_content, {"content": "content", "report": "report"})
    workflow.add_conditional_edges("content", should_continue_to_social, {"social": "social", "report": "report"})
    workflow.add_conditional_edges("social", should_continue_to_reply, {"reply": "reply", "report": "report"})
    workflow.add_edge("reply", "report")
    workflow.add_edge("report", END)
    return workflow.compile()

def run_agent(goal: str = "full_daily_run") -> Dict[str, Any]:
    logger.info(f"=== Starting PriceBD Agent | Goal: {goal} ===")
    app = build_agent()
    initial_state: AgentState = {
        "messages": [HumanMessage(content=f"Run agent with goal: {goal}")],
        "current_goal": goal,
        "seo_insights": {},
        "content_ideas": [],
        "social_posts": [],
        "reply_suggestions": [],
        "actions_taken": [],
        "final_report": "",
        "brand_info": get_brand_info(),
        "error": None,
        "publish_result": None,
    }
    try:
        result = app.invoke(initial_state)
        logger.info("Agent finished successfully")
        return {
            "success": True,
            "report": result.get("final_report", ""),
            "seo_insights": result.get("seo_insights", {}),
            "content_ideas": result.get("content_ideas", []),
            "social_posts": result.get("social_posts", []),
            "reply_suggestions": result.get("reply_suggestions", []),
            "actions_taken": result.get("actions_taken", []),
            "publish_result": result.get("publish_result"),
            "brand": result.get("brand_info", {})
        }
    except Exception as e:
        logger.exception("Agent failed")
        return {
            "success": False,
            "error": str(e),
            "report": f"Agent failed: {e}",
            "seo_insights": {},
            "content_ideas": [],
            "social_posts": [],
            "reply_suggestions": [],
            "actions_taken": [],
            "brand": get_brand_info()
        }

if __name__ == "__main__":
    import sys
    goal = sys.argv[1] if len(sys.argv) > 1 else "full_daily_run"
    print(f"\n🚀 Starting PriceBD Automation Agent (goal={goal})...\n")
    output = run_agent(goal)
    print("\n" + "=" * 70)
    print(output.get("report", "No report generated"))
    print("=" * 70)
    with open("last_report.md", "w", encoding="utf-8") as f:
        f.write(output.get("report", ""))
    print(f"\n✅ Report saved → last_report.md")
    if os.path.exists("social_posts_ready.md"):
        print("✅ Social posts ready → social_posts_ready.md")
    print(f"✅ Success: {output.get('success')}")
