"""
Streamlit console for Centaurus.
Provides chat, confidence visualization, escalation banners, and identity inputs.
"""
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Centaurus Ops Console",
    page_icon="C",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp {
        background: linear-gradient(180deg, #0a1322 0%, #0e1930 100%);
        color: #edf3ff;
    }
    .stChatMessage {
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .stChatMessage.user {
        background: rgba(242, 194, 104, 0.10);
        border-left: 4px solid #f2c268;
    }
    .stChatMessage.assistant {
        background: rgba(82, 209, 255, 0.10);
        border-left: 4px solid #52d1ff;
    }
    .escalation-banner {
        background-color: rgba(255, 125, 125, 0.10);
        border-left: 4px solid #ff7d7d;
        padding: 10px;
        border-radius: 10px;
        color: #ffd3d3;
        font-weight: 600;
    }
    .confidence-high {
        color: #5ce0a7;
        font-weight: bold;
    }
    .confidence-low {
        color: #ffcf66;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("Centaurus Ops Console")
st.caption("Publishing operations copilot for launches, royalties, access, fulfillment, and reviewer handoff")

with st.sidebar:
    st.header("Identity Context")
    st.caption("Use any signal you have. Record-level answers are strongest when email or phone is present.")

    user_email = st.text_input(
        "Registered Email",
        placeholder="sara.johnson@xyz.com",
        help="Best signal for matching the correct profile.",
    )
    user_phone = st.text_input(
        "WhatsApp / Phone",
        placeholder="+91 9876543210",
        help="Useful fallback when email is missing.",
    )
    user_name = st.text_input(
        "Dashboard Name",
        placeholder="Sara J.",
        help="Display name used in the workspace.",
    )
    user_instagram = st.text_input(
        "Instagram Handle",
        placeholder="@sarapoetry23",
        help="Helpful when the conversation started on social.",
    )

    st.divider()
    st.markdown("**Note:** In mock mode you can test without API keys or external services.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("meta"):
            meta = msg["meta"]
            cols = st.columns([1, 1, 1])

            with cols[0]:
                conf = meta.get("confidence", 0)
                color_class = "confidence-high" if conf >= 0.8 else "confidence-low"
                st.markdown(
                    f"<span class='{color_class}'>Confidence: {conf:.0%}</span>",
                    unsafe_allow_html=True,
                )

            with cols[1]:
                if meta.get("escalated"):
                    st.markdown(
                        "<span class='escalation-banner'>Escalated to reviewer</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption(f"Intent: `{meta.get('intent', 'unknown')}`")

            with cols[2]:
                if meta.get("author_found"):
                    st.caption("Profile matched")
                elif not meta.get("escalated"):
                    st.caption("No profile match")

if prompt := st.chat_input("Ask about launch status, royalties, workspace access, service programs, copies, or sales..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Running Centaurus..."):
            try:
                payload = {
                    "channel": "web",
                    "message": prompt,
                    "user_email": user_email or None,
                    "user_phone": user_phone or None,
                    "user_name": user_name or None,
                    "user_instagram": user_instagram or None,
                }

                res = requests.post(f"{API_URL}/chat", json=payload, timeout=30)
                data = res.json()

                response_text = data.get("response", "Sorry, something went wrong.")
                st.write(response_text)

                meta = {
                    "confidence": data.get("confidence", 0),
                    "intent": data.get("intent", "unknown"),
                    "escalated": data.get("escalated", False),
                    "author_found": data.get("author_found", False),
                }

                cols = st.columns([1, 1, 1])
                with cols[0]:
                    conf = meta["confidence"]
                    color_class = "confidence-high" if conf >= 0.8 else "confidence-low"
                    st.markdown(
                        f"<span class='{color_class}'>Confidence: {conf:.0%}</span>",
                        unsafe_allow_html=True,
                    )

                with cols[1]:
                    if meta["escalated"]:
                        st.markdown(
                            "<span class='escalation-banner'>Escalated to reviewer</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption(f"Intent: `{meta['intent']}`")

                with cols[2]:
                    if meta["author_found"]:
                        st.caption("Profile matched")
                    elif not meta["escalated"]:
                        st.caption("No profile match")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "meta": meta,
                })

            except requests.exceptions.ConnectionError:
                err = "Cannot connect to the backend. Make sure FastAPI is running on port 8000."
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})

            except Exception as exc:
                err = f"An error occurred: {str(exc)}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
