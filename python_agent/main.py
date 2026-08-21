"""
PriceBD Zero-Cost Full Automation Agent
Hybrid: n8n + Python LangGraph
Central Brain + SEO + Content + Social + Reply Agents
Free LLMs: Groq (primary) / Gemini (fallback)
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

load_dotenv()

# ====================== LOGGING ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("PriceBD-Agent")

# ====================== HELPERS ======================
def extract_json(text: str) -> Any:
    """Robustly extract JSON object or array from LLM response."""
    if not text:
        return None
    try:
        return json.loads(text)
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
    cleaned = re.sub(r"```json\s*|\s*```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        logger.warning("Failed to parse JSON from LLM response")
        return {"raw": text, "error": "json_parse_failed"}

def safe_get(d: Dict, *keys, default=None):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d

# ====================== LLM SETUP (FREE) ======================
def get_llm(temperature: float = 0.3, creative: bool = False):
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    temp = 0.7 if creative else temperature

    if provider == "groq" and os.getenv("GROQ_API_KEY"):
        return ChatGroq(
            model="llama-3.3-70b-versatile",
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

# ====================== BRAND ======================
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

# ====================== STATE ======================
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

# ====================== SUB-AGENTS ======================

def seo_agent(state: AgentState) -> AgentState:
    logger.info("Running SEO Agent...")
    brand = state.get("brand_info") or get_brand_info()

    prompt = f"""You are an expert SEO strategist for {brand['name']} ({brand['url']}).
Brand voice: {brand['voice']}
Product: {brand['description']}

Date: {datetime.now().strftime('%Y-%m-%d')}
Market: Bangladesh (English + Bangla searchers)

Focus on high-intent keywords people actually search:
- "iPhone 16 price in Bangladesh"
- "best laptop under 50000 BD"
- "Daraz vs Star Tech"
- "Samsung TV price BD"
- Current deals, price drops, store comparisons

Tasks:
1. Give 8 high-potential keywords / topics with priority (high/medium).
2. Suggest meta title + meta description for:
   - Homepage
   - One brand page (e.g. Apple)
   - One category page (e.g. Laptops)
3. List 4 quick technical SEO wins for a price comparison site.
4. Internal linking ideas (deals ↔ brands ↔ stores ↔ products).

Return ONLY valid JSON:
{{
  "priority_keywords": [
    {{"keyword": "...", "intent": "transactional/informational", "priority": "high/medium"}}
  ],
  "content_topics": [
    {{"title": "...", "keyword": "...", "search_intent": "...", "priority": "high/medium"}}
  ],
  "meta_suggestions": [
    {{"page": "homepage", "title": "...", "description": "..."}}
  ],
  "technical_wins": ["...", "..."],
  "internal_linking": ["..."]
}}"""

    try:
        llm = get_llm(temperature=0.2)
        response = llm.invoke([HumanMessage(content=prompt)])
        insights = extract_json(response.content)
        if not isinstance(insights, dict):
            insights = {"error": "invalid_format", "raw": str(insights)}
    except Exception as e:
        logger.error(f"SEO Agent error: {e}")
        insights = {"error": str(e)}

    state["seo_insights"] = insights
    state["actions_taken"] = state.get("actions_taken", []) + ["SEO analysis completed"]
    return state

def content_agent(state: AgentState) -> AgentState:
    logger.info("Running Content Agent...")
    brand = state.get("brand_info") or get_brand_info()
    seo = state.get("seo_insights", {})
    topics = safe_get(seo, "content_topics", default=[])[:4]

    prompt = f"""You are a content marketing expert for {brand['name']}.
Brand voice: {brand['voice']}
Website: {brand['url']}
About: {brand['description']}

Audience: Bangladeshi shoppers looking for lowest prices on mobiles, laptops, electronics, appliances.

SEO topics to use:
{json.dumps(topics, ensure_ascii=False, indent=2)}

Generate high-quality content:

1. For top 3 topics → full blog outline (H2/H3) + 120-160 word introduction.
   Always mention the benefit of live price comparison on PriceBD.
2. 4 social media posts:
   - X/Twitter (max 260 chars, engaging)
   - LinkedIn (professional)
   - Facebook (friendly + call to action)
   - General / Instagram style
3. One newsletter:
   - Subject line (curiosity + urgency)
   - Short body outline focused on today's best price drops or weekly deals

Return ONLY valid JSON:
{{
  "blog_drafts": [
    {{
      "title": "...",
      "keyword": "...",
      "outline": ["H2: ...", "H3: ..."],
      "introduction": "..."
    }}
  ],
  "social_captions": [
    {{"platform": "x", "text": "...", "hashtags": ["#PriceBD", "#Deal"]}},
    {{"platform": "linkedin", "text": "..."}},
    {{"platform": "facebook", "text": "..."}},
    {{"platform": "instagram", "text": "..."}}
  ],
  "newsletter": {{
    "subject": "...",
    "preview_text": "...",
    "outline": "..."
  }}
}}"""

    try:
        llm = get_llm(creative=True)
        response = llm.invoke([HumanMessage(content=prompt)])
        data = extract_json(response.content)
        if not isinstance(data, dict):
            data = {}
        state["content_ideas"] = data.get("blog_drafts", [])
        state["social_posts"] = data.get("social_captions", [])
        state["seo_insights"]["newsletter"] = data.get("newsletter", {})
    except Exception as e:
        logger.error(f"Content Agent error: {e}")
        state["content_ideas"] = []
        state["social_posts"] = []

    state["actions_taken"] = state.get("actions_taken", []) + ["Content generation completed"]
    return state

def social_agent(state: AgentState) -> AgentState:
    logger.info("Running Social Agent...")
    brand = state.get("brand_info") or get_brand_info()
    posts = state.get("social_posts", [])

    if not posts:
        state["actions_taken"] = state.get("actions_taken", []) + ["Social Agent skipped (no posts)"]
        return state

    prompt = f"""You are a social media expert for {brand['name']} ({brand['url']}).
Brand voice: {brand['voice']}

Current posts:
{json.dumps(posts, ensure_ascii=False, indent=2)}

Improve every post:
- Make them more engaging and click-worthy
- Keep platform character limits in mind
- Add 2-4 relevant hashtags maximum
- Suggest best time to post (Bangladesh time)
- Ensure call-to-action points to PriceBD

Return ONLY a valid JSON array:
[
  {{
    "platform": "x",
    "text": "...",
    "hashtags": ["#PriceBD", "#BDDeals"],
    "best_time_bst": "10:00 AM or 8:00 PM",
    "cta": "Compare now on PriceBD"
  }}
]"""

    try:
        llm = get_llm(creative=True)
        response = llm.invoke([HumanMessage(content=prompt)])
        refined = extract_json(response.content)
        if isinstance(refined, list):
            state["social_posts"] = refined
        else:
            state["social_posts"] = posts
    except Exception as e:
        logger.error(f"Social Agent error: {e}")

    state["actions_taken"] = state.get("actions_taken", []) + ["Social posts refined"]
    return state

def reply_agent(state: AgentState) -> AgentState:
    logger.info("Running Reply Agent...")
    brand = state.get("brand_info") or get_brand_info()

    prompt = f"""You are a customer success + support agent for {brand['name']}.
Brand voice: {brand['voice']}
Website: {brand['url']}
About: {brand['description']}

Create professional, helpful reply templates for these common situations:

1. User asks "Is this the lowest price?"
2. User reports wrong / outdated price
3. User wants price alert / notification
4. User asks how often prices are updated
5. User compares with another site
6. Positive feedback / thank you
7. User asks about a specific product availability
8. General inquiry about how PriceBD works

For each:
- Write a complete, ready-to-send reply
- Keep it professional yet friendly
- Include a soft call-to-action when relevant

Return ONLY valid JSON:
{{
  "templates": [
    {{
      "situation": "...",
      "reply": "...",
      "follow_up_action": "optional next step"
    }}
  ]
}}"""

    try:
        llm = get_llm(temperature=0.3)
        response = llm.invoke([HumanMessage(content=prompt)])
        data = extract_json(response.content)
        if isinstance(data, dict):
            state["reply_suggestions"] = data.get("templates", [])
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

# ====================== CENTRAL BRAIN ======================

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

    workflow.add_conditional_edges(
        "brain",
        route_after_brain,
        {
            "seo": "seo",
            "content": "content",
            "social": "social",
            "reply": "reply"
        }
    )

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
        "error": None
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

    report_path = "last_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(output.get("report", ""))
    print(f"\n✅ Report saved → {report_path}")
    print(f"✅ Success: {output.get('success')}")
