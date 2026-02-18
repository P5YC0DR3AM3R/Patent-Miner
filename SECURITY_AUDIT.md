# Security Audit

Date: 2026-02-18  
Scope: full repository review using `FILE_INVENTORY.md` as coverage baseline, plus post-refactor validation scans.

## Findings and Resolution Status

1. Critical - hardcoded secret in `.env:1` - Resolved  
   Recommended fix applied: replaced live secret with placeholder and documented runtime secret loading.

```diff
- PATENTSVIEW_API_KEY=<live-secret>
+ PATENTSVIEW_API_KEY=REPLACE_WITH_REAL_KEY  # placeholder only; inject real key via environment manager
```

2. High - dynamic HTML injection surface in `streamlit_app.py` - Resolved  
   Recommended fix applied: dynamic patent data now renders through Streamlit components (`st.dataframe`, `st.write`, `st.metric`), while `unsafe_allow_html=True` is limited to static CSS/mobile hint markup.

```diff
- st.markdown(f"<div>{patent['title']}</div>", unsafe_allow_html=True)
+ st.write(patent.get("title", ""))  # dynamic text rendered safely without raw HTML injection
```

3. Medium - missing access control in dashboard - Resolved  
   Recommended fix applied: optional server-side access gate with `PATENT_MINER_ACCESS_CODE`.

```diff
def enforce_access_control() -> None:
    required_code = os.getenv("PATENT_MINER_ACCESS_CODE", "").strip()
    if not required_code:
        return
    entered_code = st.text_input("Access code", type="password")
    # Security fix: compare against server-side env value only.
    if entered_code == required_code:
        st.session_state["patent_miner_auth_ok"] = True
```

4. Medium - sensitive local log artifact (`firebase-debug.log`) - Resolved  
   Recommended fix applied: file content redacted and ignore rule added.

```diff
- <full deployment log with account metadata>
+ [redacted]
+ Sensitive local deployment log data removed during security refactor.
```

```diff
.gitignore
+ firebase-debug.log
```

5. Medium - vulnerable dependency tree in baseline environment - Resolved  
   Recommended fix applied: core and optional dependencies split, high-risk optional stack removed from default install path.

```diff
- requirements.txt  # mixed baseline + optional AI stacks
+ requirements.txt           # baseline runtime only
+ requirements-optional.txt  # optional crew/model stacks
```

Validation:
- `pip-audit -r requirements.txt` -> `No known vulnerabilities found`.

6. Medium - plaintext exposure risk at runtime boundary - Mitigated  
   Recommended fix applied: local container binding restricted to loopback and local launcher pinned to localhost; production TLS remains an ingress responsibility.

```diff
docker-compose.yml
- "8501:8501"
+ "127.0.0.1:8501:8501"  # local-only host exposure
```

```diff
run_dashboard.sh
- streamlit run streamlit_app.py
+ streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Residual note: HTTPS termination must still be enforced by reverse proxy or cloud ingress in non-local deployments.

7. Low - brittle query encoding in fallback scraper (`patent_discovery.py:908`) - Resolved  
   Recommended fix applied: switched to parameterized request encoding.

```diff
- response = requests.get(f"{url}?q={query.replace(' ', '+')}", headers=headers, timeout=15)
+ response = requests.get(url, headers=headers, params=params, timeout=15)  # safe query encoding
```

8. Low - hardcoded workstation paths in runtime scripts - Resolved  
   Recommended fix applied: repository-relative execution and shared environment-driven model path configuration.

```diff
- os.chdir("/Users/<user>/.../Patent Miner")
- sys.path.insert(0, "/Users/<user>/.../Patent Miner")
+ project_root = Path(__file__).resolve().parent
+ sys.path.insert(0, str(project_root))  # portable repository-relative path
```

```diff
+ # summarization_config.py
+ model_dir = Path(os.getenv("PATENT_SUMMARY_MODEL_DIR", str(DEFAULT_MODEL_DIR))).expanduser()
+ model_filename = os.getenv("PATENT_SUMMARY_MODEL_FILENAME", DEFAULT_MODEL_FILENAME).strip() or DEFAULT_MODEL_FILENAME
```

## Explicit Non-Findings

- No `eval`, `exec`, dynamic shell execution from user input, or SQL query construction was found in application source.
- No direct credential transmission logic was found in dashboard rendering code.

## Coverage Statement

All files listed in `FILE_INVENTORY.md` were reviewed.  
Files not listed above had no actionable security defects in this audit pass and are acceptable as-is for security.
