"""
Quick local test (needs GROQ_API_KEY in .env)
Usage: python test_agent.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

from main import run_agent

def test():
    print("Testing PriceBD Agent (seo_only for speed)...")
    result = run_agent("seo_only")
    print("\nSuccess:", result["success"])
    print("Actions:", result["actions_taken"])
    print("\nSEO keywords sample:")
    print(result.get("seo_insights", {}).get("priority_keywords", [])[:3])
    print("\nReport preview (first 500 chars):")
    print(result.get("report", "")[:500])

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: Set GROQ_API_KEY or GOOGLE_API_KEY in .env first")
    else:
        test()
