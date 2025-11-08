
import streamlit as st
from ai_dev_team_moe.core.router import MoERouter
from ai_dev_team_moe.agents.ceo import Agent as CEO
from ai_dev_team_moe.agents.architect import Agent as Architect
from ai_dev_team_moe.agents.vp_engineering import Agent as VPE
from ai_dev_team_moe.agents.cto_innovation import Agent as CTO
from ai_dev_team_moe.agents.cfo import Agent as CFO
from ai_dev_team_moe.agents.solutions_architect import Agent as SA
from ai_dev_team_moe.agents.ux_designer import Agent as UX

st.title("AI Dev Team — MoE Orchestrator")

user_prompt = st.text_area("What would you like to build?", height=180, value="Build a chat app with auth and realtime.")
if st.button("Plan & Route"):
    router = MoERouter("config/models.yaml", "config/settings.yaml")
    decisions = router.plan_assignment()
    st.subheader("Routing Decisions")
    for role, decision in decisions.items():
        st.write(f"**{role.upper()}** → {decision.suggested}")
    st.subheader("Agent Stubs")
    ceo = CEO(decisions["ceo"].suggested).run(user_prompt)
    arch = Architect(decisions["architect"].suggested).run(user_prompt)
    vpe = VPE(decisions["vp_eng"].suggested).run(user_prompt)
    cto = CTO(decisions["cto"].suggested).run(user_prompt)
    cfo = CFO(decisions["cfo"].suggested).run(user_prompt)
    sa = SA(decisions["architect"].suggested).run(user_prompt)
    ux = UX(decisions["ceo"].suggested).run(user_prompt)
    for res in [ceo, arch, vpe, cto, cfo, sa, ux]:
        st.write(res.role, res.model, res.summary)
