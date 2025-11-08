import streamlit as st

st.title("AI Dev Team — Control Panel")
user_spec = st.text_area("What would you like to build?", height=240, placeholder="Describe the app…")

col1, col2 = st.columns(2)
with col1:
    start = st.button("Start Build")
with col2:
    show_docs = st.button("Show Architecture Docs")

if start and user_spec.strip():
    st.info("Submitting spec to orchestrator… (stub)")
    st.json({"prompt": user_spec, "status": "queued"})  # Replace with real API call

if show_docs:
    st.markdown("### Architecture Overview")
    try:
        st.markdown(open("../docs/ARCHITECTURE_OVERVIEW.md", "r", encoding="utf-8").read())
    except Exception as e:
        st.warning("Docs not found in this runtime environment.")
