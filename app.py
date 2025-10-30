# app.py
import streamlit as st
from utils.github_analyzer import analyze_github_profile
from utils.exatools import fetch_linkedin_profile
from utils.agent_runner import run_single_candidate_agent, run_multi_candidate_agent
from utils.scorer import extract_score_and_verdict
import pandas as pd

st.set_page_config(page_title="Candilyzer", page_icon="⚙️", layout="wide")
st.title("⚙️ Candilyzer — Streamlit Prototype")
st.markdown("Ruthless, evidence-first technical candidate analyzer")

mode = st.sidebar.radio("Mode", ["Single Candidate", "Multi-Candidate"])

if mode == "Single Candidate":
    st.header("Single Candidate Profiler")
    github_username = st.text_input("GitHub username (required)")
    linkedin_url = st.text_input("LinkedIn URL (optional)")
    analyze_btn = st.button("Analyze Candidate")

    if analyze_btn:
        if not github_username.strip():
            st.error("Provide a GitHub username.")
        else:
            with st.spinner("Fetching GitHub data..."):
                gh_data = analyze_github_profile(github_username.strip())
            with st.spinner("Verifying LinkedIn (if provided)..."):
                li_data = fetch_linkedin_profile(linkedin_url.strip()) if linkedin_url.strip() else None

            with st.spinner("Running forensic AI agent..."):
                agent_response = run_single_candidate_agent(github_data=gh_data, linkedin_data=li_data)
            score, verdict = extract_score_and_verdict(agent_response)
            st.success(f"Final Score: **{score}/100** — **{verdict}**")
            st.markdown("### AI Report")
            st.markdown(agent_response)

elif mode == "Multi-Candidate":
    st.header("Multi-Candidate Analyzer (side-by-side)")
    raw_usernames = st.text_area("Enter GitHub usernames (one per line)", height=120)
    linkedin_urls = st.text_area("Optional LinkedIn URLs (one per line, align by line with usernames)", height=120)
    analyze_btn = st.button("Analyze All Candidates")

    if analyze_btn:
        usernames = [u.strip() for u in raw_usernames.splitlines() if u.strip()]
        linkedin_lines = [l.strip() for l in linkedin_urls.splitlines()]
        if not usernames:
            st.error("Provide at least one GitHub username.")
        else:
            results = []
            for i, user in enumerate(usernames):
                st.info(f"Processing {user} ({i+1}/{len(usernames)})")
                gh_data = analyze_github_profile(user)
                li_url = linkedin_lines[i] if i < len(linkedin_lines) else None
                li_data = fetch_linkedin_profile(li_url) if li_url else None
                agent_resp = run_multi_candidate_agent(candidate_username=user, github_data=gh_data, linkedin_data=li_data)
                score, verdict = extract_score_and_verdict(agent_resp)
                results.append({
                    "username": user,
                    "score": score,
                    "verdict": verdict,
                    "report": agent_resp,
                    "public_repos": gh_data.get("public_repos"),
                    "stars": gh_data.get("total_stars"),
                    "languages": ", ".join(gh_data.get("languages") or [])
                })

            df = pd.DataFrame(results).sort_values("score", ascending=False).reset_index(drop=True)
            st.markdown("### Comparative Table")
            st.dataframe(df[["username", "score", "verdict", "public_repos", "stars", "languages"]])

            st.markdown("### Detailed Reports (Top → Down)")
            for _, row in df.iterrows():
                st.subheader(f"{row['username']} — {row['score']}/100 — {row['verdict']}")
                st.markdown(row["report"])
