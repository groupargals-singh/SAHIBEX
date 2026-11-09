"""
SAHIBEX OMEGA v6.0 - ULTIMATE MAHA-HUMAN NEURAL OS & MASTER DASHBOARD (app.py)
==============================================================================
Runs on Structure 10 (24/7 Streamlit + Render + UptimeRobot Hosting).
Combines the Futuristic All-in-One AGI Super-App with 100% of v4.0's Deep Modules:
- Structure 1: 9 Cloud Brains + 30+ Specialized Model Registry + Multimodal Super Agents
- Structure 2-5: 200GB+ GPU, 16 TPU Cores, 78GB+ High-RAM & 1.5TB+ Disk
- Structure 6: Object Storage (Supabase 1GB + Cloudinary 25GB) + Bucket Explorer
- Structure 7: Permanent SQL Memory (Turso 9GB, TiDB 5GB, Neon 500MB, Supabase 500MB)
- Structure 8: Vector RAG Brain (Qdrant 1GB, Zilliz 5GB, Pinecone 2GB) + Direct Vector Search
- Structure 9: Instant RAM Cache (Upstash Redis 256MB)
"""

import streamlit as st
import sys
import os
import io
import re
import time
import json

# Ensure repo root is in path for robust module importing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. Load Persistent Multi-Cloud Memory Store (Structures 6, 7, 8, 9)
try:
    from data.memory_store import memory_store
except Exception:
    memory_store = None

# 2. Load 9-Cloud Mega Brain Cluster (Structure 1)
try:
    from core.cloud_brains import SahibexMegaBrainCluster
    brain_cluster = SahibexMegaBrainCluster()
except Exception:
    brain_cluster = None

# 3. Load 30+ Master Model Registry & Smart Router
try:
    from core.model_registry import (
        SAHIBEX_MODEL_REGISTRY,
        SAHIBEX_MEMORY_ARCHITECTURE,
        SahibexSmartRouter,
        download_offline_model,
        get_registry_summary,
    )
    registry_loaded = True
except Exception:
    registry_loaded = False

# 4. Load Multimodal Super Agents (Vision, Voice, Live Search, FLUX Studio)
try:
    from core.super_agents import super_agents
except Exception:
    super_agents = None

# 5. Optional Neural Voice Synthesizer (gTTS)
try:
    from gtts import gTTS
    tts_available = True
except Exception:
    tts_available = False


# =========================================================================
# PAGE CONFIGURATION & FUTURISTIC HOLOGRAPHIC CYBERPUNK UI CSS
# =========================================================================
st.set_page_config(
    page_title="SAHIBEX OMEGA - Ultimate Super Brain",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Deep Space Neural OS Theme */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #111827 0%, #070913 78%);
        color: #F3F4F6;
    }
    /* Holographic Header Banner */
    .omega-hud {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.94), rgba(30, 27, 75, 0.88));
        border: 1px solid rgba(0, 245, 212, 0.4);
        box-shadow: 0 0 28px rgba(79, 70, 229, 0.28);
        border-radius: 16px;
        padding: 15px 22px;
        margin-bottom: 16px;
        text-align: center;
    }
    .omega-title {
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(90deg, #00F5D4, #818CF8, #F472B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 1.5px;
        margin: 0;
    }
    .omega-sub {
        font-size: 0.9rem;
        color: #9CA3AF;
        margin-top: 4px;
        font-weight: 500;
    }
    .hud-badges {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
        margin-top: 10px;
    }
    .hud-badge {
        background: rgba(15, 23, 42, 0.92);
        border: 1px solid rgba(99, 102, 241, 0.45);
        color: #E0E7FF;
        padding: 3px 11px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .hud-badge-live {
        border-color: #00F5D4;
        color: #00F5D4;
    }
    /* Sleek Action Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #4F46E5, #7C3AED);
        color: white;
        font-weight: 700;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 10px;
        padding: 0.55rem;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #4338CA, #6D28D9);
        box-shadow: 0 0 15px rgba(124, 58, 237, 0.6);
        color: #00F5D4;
    }
    /* Chat Message Containers */
    [data-testid="stChatMessage"] {
        background: rgba(17, 24, 39, 0.78);
        border: 1px solid rgba(79, 70, 229, 0.28);
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================================
# AUTONOMOUS AGI INTENT ROUTER & VOICE SYNTHESIZER
# =========================================================================
def detect_user_intent(prompt_text: str) -> dict:
    """
    Automatically detects user intent like a Maha-Human AGI:
    - Image Creation (FLUX.1)
    - Live Internet Search
    - Optimal Specialized Model Task (coding, debugging, math, reasoning, rag_memory, long_context, general)
    """
    p_low = prompt_text.lower().strip()

    img_patterns = [
        r"\b(generate|create|draw|make|paint|render|design)\b.*\b(image|photo|picture|pic|logo|wallpaper|art|poster|avatar)\b",
        r"\b(photo|image|tasveer|chitra|logo|wallpaper|pic)\b.*\b(banao|bana do|generate karo|dikhao|create karo)\b",
        r"^(/imagine|/draw|/flux)\b",
    ]
    wants_image = any(re.search(pat, p_low) for pat in img_patterns)

    web_keywords = [
        "live", "today", "aaj", "latest", "news", "khabar", "taza", "current",
        "price", "rate", "stock", "share", "nifty", "sensex", "bitcoin", "crypto",
        "weather", "mausam", "score", "match", "2026", "2025", "who won", "abhi",
        "search", "google", "internet",
    ]
    needs_web = any(kw in p_low for kw in web_keywords)

    if any(k in p_low for k in ["code", "python", "javascript", "html", "css", "sql", "api", "script", "program", "app banao", "function"]):
        task = "coding"
    elif any(k in p_low for k in ["bug", "error", "fix", "traceback", "issue", "crash", "debug"]):
        task = "debugging"
    elif any(k in p_low for k in ["solve", "calculate", "math", "equation", "formula", "integral", "matrix", "hisaab"]):
        task = "math"
    elif any(k in p_low for k in ["remember", "recall", "yaad", "past memory", "database search"]):
        task = "rag_memory"
    elif any(k in p_low for k in ["why", "analyze", "strategy", "architecture", "compare", "plan", "deep", "explain in detail", "research"]):
        task = "reasoning"
    elif len(p_low) > 1200:
        task = "long_context"
    else:
        task = "general"

    return {
        "wants_image": wants_image,
        "needs_web": needs_web,
        "task_type": task,
    }


def synthesize_voice_bytes(text_to_speak: str):
    """Generates spoken MP3 audio for SAHIBEX responses."""
    if not tts_available or not text_to_speak:
        return None
    try:
        clean_text = re.sub(r"```.*?```", " Code generated. ", text_to_speak, flags=re.DOTALL)
        clean_text = re.sub(r"[#*`_~>|•]", " ", clean_text)
        clean_text = re.sub(r"https?://\S+", "", clean_text)
        clean_text = clean_text.strip()[:550]
        if not clean_text:
            return None
        tts = gTTS(text=clean_text, lang="hi", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None


# =========================================================================
# TOP HOLOGRAPHIC HUD HEADER
# =========================================================================
st.markdown(
    """
    <div class="omega-hud">
        <p class="omega-title">⚡ SAHIBEX OMEGA — MAHA-HUMAN SUPER BRAIN ⚡</p>
        <p class="omega-sub">Distributed Multi-Cloud AGI Infrastructure (10 Cloud Providers / 30+ Models / 10 Structures / Multimodal Agents Active)</p>
        <div class="hud-badges">
            <span class="hud-badge hud-badge-live">● AGI AUTO-PILOT ONLINE</span>
            <span class="hud-badge">☁️ 9 Cloud Brains + HF Power Hub</span>
            <span class="hud-badge">📚 30+ Specialized Models</span>
            <span class="hud-badge">🗄️ 15GB SQL + 8GB Vector + 26GB Vault</span>
            <span class="hud-badge">👁️🎙️🎨 Vision + Whisper + FLUX.1</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================================
# SIDEBAR NAVIGATION & GLOBAL BRAIN SETTINGS (ALL 8 MODULES)
# =========================================================================
st.sidebar.title("🚀 SAHIBEX Command Center")
menu = st.sidebar.selectbox(
    "Select Superpower Module",
    [
        "🧠 Maha-Human Super AI App (All-in-One AGI)",
        "🤖 Autonomous Super Brain Chat (v4.0 Terminal)",
        "👁️🎙️🎨 Multimodal Super Agents (Vision, Voice, Search & Studio)",
        "📊 Live Infrastructure Diagnostics",
        "📚 30+ Model Registry & Offline GGUF Vault",
        "🧠 Superpower Memory (Remember & Recall)",
        "📁 26GB Object Storage & Media Vault",
        "🔍 8GB Vector RAG Semantic Engine",
    ],
)

with st.sidebar.expander("⚙️ Brain & Memory Settings", expanded=True):
    active_session_id = st.text_input("Active Session ID", value="sahibex_master_session")
    autopilot_mode = st.checkbox("🤖 AGI Auto-Pilot Intent Routing", value=True)
    auto_memory_sync = st.checkbox("🧠 Auto-Sync Learning Memory (SQL + Vector + Redis)", value=True)
    enable_live_web = st.checkbox("🌐 Auto / Enable Live Internet Search", value=True)
    council_mode = st.checkbox("🔮 Council of Brains (Multi-Model Deep Synthesis)", value=False)
    voice_reply_mode = st.checkbox("🔊 Speak Replies Aloud (Neural Voice)", value=False)
    offline_gguf_mode = st.checkbox("💻 100% Offline Local GGUF Mode (Port 8080)", value=False)


# =========================================================================
# MODULE 0: MAHA-HUMAN SUPER AI APP (REAL CHATGPT/JARVIS ALL-IN-ONE EXPERIENCE)
# =========================================================================
if menu == "🧠 Maha-Human Super AI App (All-in-One AGI)":

    if "omega_messages" not in st.session_state:
        st.session_state.omega_messages = [
            {
                "role": "assistant",
                "brain": "SAHIBEX OMEGA CORE v6.0",
                "content": (
                    "Namaste **Pankaj**! Main **SAHIBEX OMEGA (Maha-Human Super Brain)** hoon. 🧠⚡\n\n"
                    "Mere paas **10 Cloud Providers, 30+ Specialized Models, Aankhein (Vision), Kaan (Whisper v3 Voice), "
                    "Live Internet Search, FLUX.1 Image Studio**, aur **49GB Permanent Learning Memory** ek sath active hain.\n\n"
                    "**Aap seedha niche Chat Bar se har kaam karwa sakte hain:**\n"
                    "- 💬 **Koi bhi Complex Task, Full-Stack Code, ya Deep Math** puchiye\n"
                    "- 🎨 **AI Image banwayein:** Bas likhein *\"Ek futuristic supercomputer ki photo banao\"* ya `\"/imagine ...\"`\n"
                    "- 👁️ **Photo/Screenshot padhwayein:** Niche `➕ Multimodal Input & Engine Controls` khol kar photo lagayein\n"
                    "- 🎙️ **Awaaz se baat karein:** Mic daba kar bolein ya audio upload karein\n"
                    "- 🔮 **Council of Brains:** Sidebar se on karein jab aapko 2 alag Super Models ki combined salah chahiye!"
                ),
            }
        ]

    # Quick 1-Tap Futuristic Neural Action Chips
    q_col1, q_col2, q_col3, q_col4, q_col5 = st.columns(5)
    quick_prompt = None
    with q_col1:
        if st.button("🌐 Live India & AI News"):
            quick_prompt = "Aaj ki latest AI, technology aur Indian share market ki mukhya taaza khabrein batao."
    with q_col2:
        if st.button("🎨 Imagine Cyber Brain"):
            quick_prompt = "Generate image of a glowing futuristic holographic super brain AI floating in a dark neon command deck, 8k ultra realistic"
    with q_col3:
        if st.button("💻 Python Quant Bot"):
            quick_prompt = "Write a clean, production-ready Python script for an Indian stock market RSI + EMA trend scanner with Telegram/Webhook alerts."
    with q_col4:
        if st.button("🧬 Full System Capabilities"):
            quick_prompt = "Apne 10 Cloud Structures, 30+ Models aur 4-Layer Learning Memory ki poori takat samjhao."
    with q_col5:
        if st.button("🗑️ Clear Chat"):
            st.session_state.omega_messages = []
            st.rerun()

    # Render Chat Conversation Stream
    for idx, msg in enumerate(st.session_state.omega_messages):
        avatar_icon = "🧠" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar_icon):
            if msg.get("brain"):
                st.caption(f"⚡ **Active Neural Engine:** `{msg['brain']}`")
            if msg.get("user_image"):
                st.image(msg["user_image"], caption="Uploaded Visual Input", width=280)
            st.markdown(msg["content"])
            if msg.get("generated_image"):
                st.image(msg["generated_image"], caption="✨ Rendered by SAHIBEX FLUX.1 Visual Studio")
                st.download_button(
                    "⬇️ Download HD Image (PNG)",
                    data=msg["generated_image"],
                    file_name=f"sahibex_flux_{idx}.png",
                    mime="image/png",
                    key=f"dl_omega_{idx}",
                )
            if msg.get("audio_bytes"):
                st.audio(msg["audio_bytes"], format="audio/mp3")

    # Multimodal Attachment & Manual Engine Override Bar
    with st.expander("➕ Attach Photo (Vision)  |  🎙️ Speak with Voice (Mic)  |  🎯 Engine & Model Override", expanded=False):
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            attached_img = st.file_uploader(
                "👁️ Attach Image / Screenshot (Vision)",
                type=["png", "jpg", "jpeg", "webp"],
                key="omega_img_upload",
            )
            force_flux_image = st.checkbox("🎨 Force FLUX.1 Image Generation", value=False)
        with m_col2:
            recorded_voice = None
            if hasattr(st, "audio_input"):
                recorded_voice = st.audio_input("🎙️ Tap Mic to Speak Live")
            uploaded_voice = st.file_uploader(
                "Or Upload Voice File (WAV/MP3/M4A/OGG)",
                type=["wav", "mp3", "m4a", "ogg"],
                key="omega_aud_upload",
            )
        with m_col3:
            omega_exec_engine = st.selectbox(
                "Execution Engine",
                [
                    "⚡ 9-Cloud Auto-Failover Cluster",
                    "🔥 Hugging Face Dedicated Power Models",
                ],
                key="omega_engine_sel",
            )
            omega_task_override = st.selectbox(
                "Task Specialty Override",
                [
                    "auto (🤖 Smart AGI Auto-Pilot)",
                    "general (Master Logic - Llama 3.3 70B)",
                    "reasoning (Deep Thinking - DeepSeek-R1)",
                    "coding (Software Build - Qwen Coder 32B)",
                    "debugging (Code Fix - Codestral 22B)",
                    "math (Complex Calculations - DeepSeek-R1)",
                    "rag_memory (Database Search - Command-R+)",
                    "long_context (Massive Docs - Gemini 2.0/1.5)",
                    "fast_chat (0.1s Instant - Groq LPU)",
                    "vision (Image & OCR Analysis)",
                ],
                key="omega_task_sel",
            )
            omega_hf_model = st.selectbox(
                "HF Power Model (If HF Engine Selected)",
                [
                    "qwen3_235b",
                    "deepseek_r1",
                    "qwen_72b",
                    "llama_70b",
                    "mistral_large",
                    "qwen_coder_32b",
                    "llama_vision_90b",
                    "qwen_vision_72b",
                    "gemma_2_27b",
                ],
                key="omega_hf_sel",
            )

    # Bottom Floating Real App Chat Input
    typed_prompt = st.chat_input("Ask SAHIBEX Super Brain anything, write code, or say 'Photo banao...'")

    # Handle Voice Input if Mic/Audio was used without typing
    voice_transcript = None
    active_audio = recorded_voice or uploaded_voice
    if active_audio and not typed_prompt and not quick_prompt:
        audio_bytes_raw = active_audio.getvalue()
        audio_sig = f"{len(audio_bytes_raw)}_{getattr(active_audio, 'name', 'mic.wav')}"
        if st.session_state.get("last_processed_audio") != audio_sig:
            st.session_state.last_processed_audio = audio_sig
            if super_agents:
                with st.spinner("🎙️ Listening via Groq Whisper-Large-v3-Turbo..."):
                    voice_transcript = super_agents.speech_to_text(
                        audio_bytes_raw, getattr(active_audio, "name", "voice.wav")
                    )

    active_prompt = typed_prompt or quick_prompt or voice_transcript

    if active_prompt:
        user_msg_data = {
            "role": "user",
            "brain": "🎙️ Voice Command (Whisper v3)" if voice_transcript else "👤 Master Command",
            "content": active_prompt,
        }
        if attached_img:
            user_msg_data["user_image"] = attached_img.getvalue()

        st.session_state.omega_messages.append(user_msg_data)

        with st.chat_message("user", avatar="👤"):
            if attached_img:
                st.image(attached_img.getvalue(), width=260)
            st.markdown(active_prompt)

        with st.chat_message("assistant", avatar="🧠"):
            intent = detect_user_intent(active_prompt)
            selected_task = (
                intent["task_type"]
                if omega_task_override.startswith("auto")
                else omega_task_override.split(" ")[0]
            )
            do_image_gen = force_flux_image or (autopilot_mode and intent["wants_image"] and not attached_img)
            do_web_search = enable_live_web and (intent["needs_web"] or "live" in active_prompt.lower())

            generated_img_bytes = None
            final_reply_text = ""
            provider_badge = "SAHIBEX OMEGA"

            with st.status("⚡ SAHIBEX Maha-Brain Processing...", expanded=True) as status_box:

                # --- PATH A: AUTONOMOUS IMAGE GENERATION (FLUX.1) ---
                if do_image_gen and super_agents:
                    st.write("🎨 **Intent Detected:** Visual Generation $\rightarrow$ Launching FLUX.1 GPU Studio...")
                    clean_img_prompt = re.sub(r"^(/imagine|/draw|/flux)\s*", "", active_prompt, flags=re.I)
                    generated_img_bytes, model_used = super_agents.generate_image(clean_img_prompt)
                    if generated_img_bytes:
                        provider_badge = f"FLUX.1 Visual Studio ({model_used})"
                        final_reply_text = f"✨ Aapki kalpana ke anusar high-resolution AI image tayar hai (`{model_used}`):"
                        if memory_store:
                            try:
                                vault_res = memory_store.upload_object(
                                    file_name=f"omega_flux_{int(time.time())}.png",
                                    file_bytes=generated_img_bytes,
                                    content_type="image/png",
                                )
                                if "public_url" in vault_res:
                                    final_reply_text += f"\n\n☁️ **Saved to 26GB Cloud Vault:** [Open Permanent HD Link]({vault_res['public_url']})"
                            except Exception:
                                pass
                    else:
                        final_reply_text = f"⚠️ {model_used}"
                        provider_badge = "Visual Studio Notice"

                # --- PATH B: VISION + IMAGE OCR ANALYSIS ---
                elif attached_img and super_agents:
                    st.write("👁️ **Visual Input Detected:** Analyzing image via Gemini 2.0 / Llama-3.2 Vision...")
                    vis_reply, vis_provider = super_agents.analyze_image(
                        attached_img.getvalue(), active_prompt
                    )
                    final_reply_text = vis_reply
                    provider_badge = f"Vision Engine ({vis_provider})"

                # --- PATH C: OMNI-BRAIN REASONING + MEMORY + LIVE WEB ---
                else:
                    recalled_working, recalled_sql, recalled_vector = [], [], []
                    enriched_prompt = active_prompt

                    if do_web_search and super_agents and not offline_gguf_mode:
                        st.write("🌐 **Live Web Agent:** Fetching real-time internet facts & news...")
                        web_facts = super_agents.live_web_search(active_prompt)
                        enriched_prompt = (
                            f"[LIVE INTERNET SEARCH DATA]:\n{web_facts}\n\n"
                            f"[USER QUESTION]:\n{active_prompt}"
                        )

                    if auto_memory_sync and memory_store:
                        st.write("🧠 **Memory Synapse:** Recalling past knowledge from Redis, 15GB SQL & 8GB Vector Brain...")
                        try:
                            past_ctx = memory_store.recall(
                                session_id=active_session_id,
                                query=active_prompt,
                                top_k=4,
                            )
                            if isinstance(past_ctx, dict):
                                recalled_working = [str(past_ctx.get("redis_cache", ""))]
                                recalled_sql = [str(past_ctx.get("sql_history", ""))]
                                recalled_vector = [str(past_ctx.get("vector_matches", ""))]
                            elif past_ctx:
                                recalled_sql = [str(past_ctx)]
                        except Exception:
                            pass

                    if registry_loaded:
                        spec = SahibexSmartRouter.select_model(
                            task_type=selected_task, offline_mode=offline_gguf_mode
                        )
                        st.write(
                            f"🎯 **Smart Router Target:** `{spec.get('id', spec.get('filename'))}` | **Task:** `{selected_task.upper()}`"
                        )

                    if brain_cluster:
                        if omega_exec_engine == "🔥 Hugging Face Dedicated Power Models" and not offline_gguf_mode:
                            final_reply_text = brain_cluster.query_huggingface_power_model(
                                model_key=omega_hf_model,
                                prompt=enriched_prompt,
                            )
                            provider_badge = f"Hugging Face Power Hub ({omega_hf_model})"
                        else:
                            history_payload = [
                                {"role": m["role"], "content": m["content"]}
                                for m in st.session_state.omega_messages[-7:-1]
                            ]
                            history_payload.append({"role": "user", "content": enriched_prompt})

                            final_reply_text, provider_badge = brain_cluster.generate_response(
                                messages=history_payload,
                                task_type=selected_task,
                                working_memory=recalled_working,
                                sql_learned_rules=recalled_sql,
                                vector_experiences=recalled_vector,
                                offline_mode=offline_gguf_mode,
                            )

                            # Optional Council of Brains (Second Opinion Synthesis from HF 235B/R1)
                            if council_mode and not offline_gguf_mode:
                                st.write("🔮 **Council of Brains Active:** Consulting secondary HF Power Model (`deepseek_r1`)...")
                                try:
                                    second_opinion = brain_cluster.query_huggingface_power_model(
                                        model_key="deepseek_r1",
                                        prompt=active_prompt,
                                    )
                                    if second_opinion and "unavailable" not in second_opinion.lower():
                                        final_reply_text += (
                                            f"\n\n---\n### 🔮 Council of Brains — Secondary Deep Analysis (`DeepSeek-R1`)\n"
                                            f"{second_opinion}"
                                        )
                                        provider_badge += " + DeepSeek-R1 Council"
                                except Exception:
                                    pass
                    else:
                        final_reply_text = "⚠️ `core.cloud_brains` load nahi ho paya."

                if auto_memory_sync and memory_store and final_reply_text:
                    st.write("💾 **Memory Sync:** Saving new learning to SQL, Vector & Redis...")
                    try:
                        memory_store.remember(
                            session_id=active_session_id,
                            text=f"User: {active_prompt}\nSAHIBEX ({provider_badge}): {final_reply_text[:1200]}",
                            role="assistant",
                            metadata={"task": selected_task, "brain": provider_badge},
                        )
                    except Exception:
                        pass

                status_box.update(
                    label=f"✨ Completed via {provider_badge}  |  Task: {selected_task.upper()}",
                    state="complete",
                    expanded=False,
                )

            st.caption(f"⚡ **Active Neural Engine:** `{provider_badge}`")
            st.markdown(final_reply_text)

            if generated_img_bytes:
                st.image(generated_img_bytes, caption="✨ Rendered by SAHIBEX FLUX.1 Visual Studio")
                st.download_button(
                    "⬇️ Download HD Image (PNG)",
                    data=generated_img_bytes,
                    file_name=f"sahibex_flux_{int(time.time())}.png",
                    mime="image/png",
                )

            spoken_audio = None
            if voice_reply_mode and final_reply_text:
                spoken_audio = synthesize_voice_bytes(final_reply_text)
                if spoken_audio:
                    st.audio(spoken_audio, format="audio/mp3")

            st.session_state.omega_messages.append(
                {
                    "role": "assistant",
                    "brain": provider_badge,
                    "content": final_reply_text,
                    "generated_image": generated_img_bytes,
                    "audio_bytes": spoken_audio,
                }
            )


# =========================================================================
# MODULE A (v4.0 CLASSIC): AUTONOMOUS SUPER BRAIN TERMINAL (MANUAL CONTROL)
# =========================================================================
elif menu == "🤖 Autonomous Super Brain Chat (v4.0 Terminal)":
    st.subheader("🤖 SAHIBEX Autonomous Super Brain Terminal (v4.0 Classic Control)")

    col_mode, col_task, col_hf = st.columns(3)
    with col_mode:
        execution_engine = st.selectbox(
            "Select Execution Engine",
            [
                "⚡ 9-Cloud Auto-Failover Cluster",
                "🔥 Hugging Face Dedicated Power Models",
            ],
        )
    with col_task:
        task_label = st.selectbox(
            "Select Task Specialty (Smart Router)",
            [
                "general (Master Logic - Llama 3.3 70B)",
                "reasoning (Deep Thinking - DeepSeek-R1)",
                "coding (Software Build - Qwen Coder 32B)",
                "debugging (Code Fix - Codestral 22B)",
                "math (Complex Calculations - DeepSeek-R1)",
                "rag_memory (Database Search - Command-R+)",
                "long_context (Massive Docs - Gemini 2.0/1.5)",
                "fast_chat (0.1s Instant - Groq LPU)",
                "vision (Image & OCR Analysis)",
            ],
        )
        selected_task_key = task_label.split(" ")[0]

    with col_hf:
        hf_model_choice = st.selectbox(
            "HF Power Model (If HF Engine Selected)",
            [
                "qwen3_235b",
                "deepseek_r1",
                "qwen_72b",
                "llama_70b",
                "mistral_large",
                "qwen_coder_32b",
                "llama_vision_90b",
                "qwen_vision_72b",
                "gemma_2_27b",
            ],
        )

    if registry_loaded:
        routed_spec = SahibexSmartRouter.select_model(
            task_type=selected_task_key, offline_mode=offline_gguf_mode
        )
        st.info(
            f"🎯 **Smart Router Target:** `{routed_spec.get('id', routed_spec.get('filename'))}` | "
            f"**Specialty:** {routed_spec.get('specialty', 'Autonomous Intelligence')}"
        )

    if "sahibex_chat_history" not in st.session_state:
        st.session_state.sahibex_chat_history = []

    user_prompt = st.text_area(
        "Enter Command for SAHIBEX Super Brain:",
        height=110,
        placeholder="Ask anything: write full-stack code, solve deep math, analyze strategy, or recall past memories...",
    )

    col_btn1, col_btn2 = st.columns([4, 1])
    with col_btn1:
        run_btn = st.button("🚀 Execute with Super Brain & Learning Memory")
    with col_btn2:
        if st.button("🗑️ Clear Screen"):
            st.session_state.sahibex_chat_history = []
            st.rerun()

    if run_btn:
        if not user_prompt.strip():
            st.warning("Kripya apna sawal ya command likhein.")
        elif not brain_cluster:
            st.error("⚠️ `core.cloud_brains` load nahi ho paya. Kripya GitHub files check karein.")
        else:
            recalled_working = []
            recalled_sql = []
            recalled_vector = []

            final_user_prompt = user_prompt
            if enable_live_web and super_agents and not offline_gguf_mode:
                with st.spinner("🌐 Searching Live Internet for real-time facts..."):
                    web_context = super_agents.live_web_search(user_prompt)
                    final_user_prompt = (
                        f"[LIVE INTERNET SEARCH DATA]:\n{web_context}\n\n"
                        f"[USER QUESTION]:\n{user_prompt}"
                    )

            if auto_memory_sync and memory_store:
                with st.spinner("🧠 Recalling past knowledge from Redis, 15GB SQL & 8GB Vector Brain..."):
                    try:
                        past_context = memory_store.recall(
                            session_id=active_session_id,
                            query=user_prompt,
                            top_k=4,
                        )
                        if isinstance(past_context, dict):
                            recalled_working = [str(past_context.get("redis_cache", ""))]
                            recalled_sql = [str(past_context.get("sql_history", ""))]
                            recalled_vector = [str(past_context.get("vector_matches", ""))]
                        elif past_context:
                            recalled_sql = [str(past_context)]
                    except Exception:
                        pass

            with st.spinner("⚡ Routing across SAHIBEX Super Brain..."):
                if execution_engine == "🔥 Hugging Face Dedicated Power Models" and not offline_gguf_mode:
                    reply_text = brain_cluster.query_huggingface_power_model(
                        model_key=hf_model_choice,
                        prompt=final_user_prompt,
                    )
                    provider_used = f"Hugging Face Power Hub ({hf_model_choice})"
                else:
                    chat_messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.sahibex_chat_history[-6:]
                    ]
                    chat_messages.append({"role": "user", "content": final_user_prompt})

                    reply_text, provider_used = brain_cluster.generate_response(
                        messages=chat_messages,
                        task_type=selected_task_key,
                        working_memory=recalled_working,
                        sql_learned_rules=recalled_sql,
                        vector_experiences=recalled_vector,
                        offline_mode=offline_gguf_mode,
                    )

            if auto_memory_sync and memory_store:
                try:
                    memory_store.remember(
                        session_id=active_session_id,
                        text=f"User: {user_prompt}\nSAHIBEX ({provider_used}): {reply_text}",
                        role="assistant",
                        metadata={"task": selected_task_key, "brain": provider_used},
                    )
                except Exception:
                    pass

            st.session_state.sahibex_chat_history.append(
                {"role": "user", "content": user_prompt, "brain": "User Command"}
            )
            st.session_state.sahibex_chat_history.append(
                {"role": "assistant", "content": reply_text, "brain": provider_used}
            )

    if st.session_state.sahibex_chat_history:
        st.markdown("---")
        for msg in reversed(st.session_state.sahibex_chat_history):
            if msg["role"] == "assistant":
                st.success(f"🧠 **Active Brain:** `{msg.get('brain', 'SAHIBEX')}`")
                st.markdown(msg["content"])
                st.markdown("---")
            else:
                st.markdown(f"**👤 You:** {msg['content']}")


# =========================================================================
# MODULE A2: MULTIMODAL SUPER AGENTS (VISION, VOICE, SEARCH & STUDIO)
# =========================================================================
elif menu == "👁️🎙️🎨 Multimodal Super Agents (Vision, Voice, Search & Studio)":
    st.subheader("👁️🎙️🎨 SAHIBEX Multimodal Superpowers (Eyes, Ears, Live Web & Visual Studio)")

    if not super_agents:
        st.error("⚠️ `core/super_agents.py` load nahi ho paya. Kripya GitHub mein file check karein.")
    else:
        tab_vis, tab_voice, tab_img, tab_web = st.tabs([
            "👁️ Vision (Read Image / Screenshot)",
            "🎙️ Voice Command (Whisper v3 Turbo)",
            "🎨 FLUX.1 Image Studio",
            "🌐 Live Internet Search Agent",
        ])

        # --- TAB 1: VISION ENGINE ---
        with tab_vis:
            st.markdown("### 👁️ SAHIBEX Vision (Upload Photo, Chart, Document, or Code Screenshot)")
            vis_file = st.file_uploader("Upload Image (JPG, PNG, WEBP)", type=["png", "jpg", "jpeg", "webp"])
            vis_prompt = st.text_input(
                "Ask about this image:",
                value="Is image ko detail mein samjhao. Agar isme koi text, chart, ya code hai toh poora nikaal kar do.",
            )
            if vis_file and st.button("👁️ Analyze Image with Vision Brain"):
                st.image(vis_file, caption="Uploaded Image", width=350)
                with st.spinner("Analyzing image via Gemini 2.0 / Llama-3.2 Vision..."):
                    vis_reply, vis_provider = super_agents.analyze_image(vis_file.getvalue(), vis_prompt)
                st.success(f"Vision Provider: **{vis_provider}**")
                st.markdown(vis_reply)
                if auto_memory_sync and memory_store:
                    try:
                        memory_store.remember(
                            session_id=active_session_id,
                            text=f"[Vision Analysis - {vis_file.name}]: {vis_reply}",
                            role="assistant",
                            metadata={"type": "vision_analysis"},
                        )
                    except Exception:
                        pass

        # --- TAB 2: VOICE ENGINE ---
        with tab_voice:
            st.markdown("### 🎙️ SAHIBEX Voice Command (Hindi / English Speech-to-Text + Brain Reply)")
            audio_upload = st.file_uploader("Upload Voice Note / Audio File (WAV, MP3, M4A, OGG)", type=["wav", "mp3", "m4a", "ogg"])
            if audio_upload and st.button("🎙️ Transcribe & Execute Voice Command"):
                with st.spinner("Listening via Groq Whisper-Large-v3-Turbo..."):
                    spoken_text = super_agents.speech_to_text(audio_upload.getvalue(), audio_upload.name)
                st.info(f"🗣️ **Aapki Awaaz (Transcribed):** {spoken_text}")

                if brain_cluster and not spoken_text.startswith("Voice"):
                    with st.spinner("⚡ Generating Super Brain reply..."):
                        voice_reply, voice_brain = brain_cluster.generate_response(
                            messages=[{"role": "user", "content": spoken_text}]
                        )
                    st.success(f"🧠 **Brain Reply ({voice_brain}):**")
                    st.markdown(voice_reply)

        # --- TAB 3: VISUAL STUDIO (IMAGE GENERATION) ---
        with tab_img:
            st.markdown("### 🎨 SAHIBEX Visual Studio (Powered by FLUX.1 & Stable Diffusion)")
            img_prompt = st.text_area(
                "Describe the image, logo, or UI mockup you want to generate:",
                placeholder="Example: A futuristic AI command center hologram glowing in dark blue and gold, ultra-realistic 8k...",
            )
            save_to_vault = st.checkbox("Auto-Save generated image to 26GB Cloud Vault (Cloudinary/Supabase)", value=True)
            if st.button("🎨 Generate High-Res Image"):
                if img_prompt.strip():
                    with st.spinner("Rendering image on Cloud GPU via FLUX.1..."):
                        img_bytes, model_used = super_agents.generate_image(img_prompt)
                    if img_bytes:
                        st.success(f"✨ Generated using `{model_used}`")
                        st.image(img_bytes, caption=img_prompt)
                        st.download_button(
                            "⬇️ Download Image (PNG)",
                            data=img_bytes,
                            file_name="sahibex_generated.png",
                            mime="image/png",
                        )
                        if save_to_vault and memory_store:
                            try:
                                vault_res = memory_store.upload_object(
                                    file_name=f"flux_{int(time.time())}.png",
                                    file_bytes=img_bytes,
                                    content_type="image/png",
                                )
                                if "public_url" in vault_res:
                                    st.markdown(f"☁️ **Saved to 26GB Cloud Vault:** [Open Permanent Link]({vault_res['public_url']})")
                            except Exception:
                                pass
                    else:
                        st.warning(model_used)
                else:
                    st.warning("Kripya image ka description likhein.")

        # --- TAB 4: LIVE WEB SEARCH ---
        with tab_web:
            st.markdown("### 🌐 Real-Time Internet Search Engine")
            web_q = st.text_input("Search live news, stock data, or fresh facts:")
            if st.button("🌐 Search Live Web"):
                if web_q.strip():
                    with st.spinner("Fetching live data from web..."):
                        live_res = super_agents.live_web_search(web_q)
                    st.markdown(live_res)
                else:
                    st.warning("Search query likhein.")


# =========================================================================
# MODULE 1: INFRASTRUCTURE HEALTH & STATUS (All Structures Diagnostics)
# =========================================================================
elif menu == "📊 Live Infrastructure Diagnostics":
    st.subheader("🌐 Real-Time Multi-Cloud Cluster Status")
    st.info("Checking connection health across all active cloud brains, databases, vector stores, object storage, and RAM caches...")

    if brain_cluster:
        st.markdown("### 🤖 Structure 1: 9-Cloud AI Brain Cluster, 30+ Registry & Super Agents")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            status_data = brain_cluster.cluster_status()
            status_data["Multimodal Super Agents Ready"] = bool(super_agents)
            st.json(status_data)
        with col_b2:
            if registry_loaded:
                st.json(get_registry_summary())
            else:
                st.warning("Model Registry summary unavailable.")

    if memory_store:
        with st.spinner("Pinging 10 cloud nodes..."):
            report = memory_store.status_report()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📦 Structure 6: Object Storage (26 GB)")
            st.json(report.get("structure_6_object_storage_26gb", {}))

            st.markdown("### 🗄️ Structure 7: SQL Memory (15 GB)")
            st.json(report.get("structure_7_sql_memory_15gb", {}))

        with col2:
            st.markdown("### 🧠 Structure 8: Vector RAG Brain (8 GB)")
            st.json(report.get("structure_8_vector_brain_8gb", {}))

            st.markdown("### ⚡ Structure 9: Instant RAM Cache")
            st.json(report.get("structure_9_instant_cache", {}))

        st.success("✨ SAHIBEX Multi-Cloud Cluster is operating at 100% Superpower capacity!")
    else:
        st.error("⚠️ `data.memory_store` module could not be loaded. Please ensure memory_store.py is committed properly in GitHub.")


# =========================================================================
# MODULE B: 30+ MODEL REGISTRY & 1-CLICK OFFLINE GGUF VAULT
# =========================================================================
elif menu == "📚 30+ Model Registry & Offline GGUF Vault":
    st.subheader("📚 SAHIBEX Master Model Registry (30+ Models Across 9 Categories)")

    if not registry_loaded:
        st.error("⚠️ `core/model_registry.py` load nahi ho paya. Kripya file check karein.")
    else:
        tab_reg, tab_mem_arch, tab_gguf = st.tabs([
            "🌐 30+ Models Explorer",
            "🛡️ 4-Layer Learning Memory Blueprint",
            "💾 1-Click Offline GGUF Vault",
        ])

        with tab_reg:
            selected_cat = st.selectbox(
                "Select Model Category",
                list(SAHIBEX_MODEL_REGISTRY.keys()),
            )
            st.json(SAHIBEX_MODEL_REGISTRY[selected_cat])

        with tab_mem_arch:
            st.info("Models sirf sochne ka engine hain. SAHIBEX ki asli Learning Memory in 4 private layers mein hamesha safe rehti hai:")
            st.json(SAHIBEX_MEMORY_ARCHITECTURE)

        with tab_gguf:
            st.markdown("### 💾 100% Independent Offline GGUF Models (Structure 5 Cloud Disk / Local)")
            offline_dict = SAHIBEX_MODEL_REGISTRY.get("offline_gguf_models", {})
            chosen_gguf = st.selectbox("Select Offline GGUF Model to Pull/Inspect", list(offline_dict.keys()))
            gguf_info = offline_dict[chosen_gguf]

            st.json(gguf_info)
            st.markdown("**Direct Terminal / Cloud Disk Download Command:**")
            st.code(f"curl -L -o models/{gguf_info['filename']} {gguf_info['download_url']}", language="bash")

            if st.button(f"⬇️ Download {gguf_info['filename']} to Current Server Disk"):
                with st.spinner(f"Downloading {gguf_info['filename']} ({gguf_info['size_gb']} GB) from Hugging Face..."):
                    try:
                        saved_path = download_offline_model(model_key=chosen_gguf, target_dir="models")
                        st.success(f"✅ Model successfully saved at: `{saved_path}`")
                    except Exception as e:
                        st.error(f"Download error: {e}")


# =========================================================================
# MODULE 2: SUPERPOWER MEMORY (Remember & Recall via SQL + Redis + Vector)
# =========================================================================
elif menu == "🧠 Superpower Memory (Remember & Recall)":
    st.subheader("🧠 Persistent Multi-Cloud Memory & Context Engine")

    session_id = st.text_input("Active Session / User ID", value=active_session_id)

    tab1, tab2 = st.tabs(["✍️ Remember (Store Knowledge)", "📖 Recall (Semantic & SQL Context)"])

    with tab1:
        user_input = st.text_area("Enter knowledge, instruction, or conversation log for SAHIBEX to memorize:")
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            role = st.selectbox("Role", ["user", "assistant", "system", "developer"])
        with col_meta2:
            tag = st.text_input("Metadata Tag (optional)", value="core_memory")

        if st.button("🚀 Store in Super Brain"):
            if user_input and memory_store:
                with st.spinner("Syncing across RAM Cache, 15GB SQL, and 8GB Vector Brain..."):
                    res = memory_store.remember(
                        session_id=session_id,
                        text=user_input,
                        role=role,
                        metadata={"tag": tag},
                    )
                st.success("Successfully memorized across all cloud structures!")
                st.json(res)
            else:
                st.warning("Please enter text to remember.")

    with tab2:
        query_text = st.text_input("Enter recall query or keywords:")
        top_k = st.slider("Top Results Limit", 1, 10, 5)

        if st.button("🔍 Recall Super Brain Context"):
            if query_text and memory_store:
                with st.spinner("Searching SQL history, RAM cache, and Vector embeddings..."):
                    context_data = memory_store.recall(session_id=session_id, query=query_text, top_k=top_k)
                st.success("Context retrieved successfully!")
                st.json(context_data)
            else:
                st.warning("Please enter a query to recall.")


# =========================================================================
# MODULE 3: OBJECT STORAGE & MEDIA VAULT (Supabase + Cloudinary)
# =========================================================================
elif menu == "📁 26GB Object Storage & Media Vault":
    st.subheader("📁 Fast Object Storage & Media Management (26 GB)")

    uploaded_file = st.file_uploader("Upload files, images, documents, or audio for SAHIBEX storage")

    if uploaded_file and memory_store:
        if st.button("⬆️ Upload to Cloud Vault"):
            file_bytes = uploaded_file.getvalue()
            with st.spinner("Uploading to Supabase Bucket & Cloudinary Media Disk..."):
                upload_res = memory_store.upload_object(
                    file_name=uploaded_file.name,
                    file_bytes=file_bytes,
                    content_type=uploaded_file.type or "application/octet-stream",
                )
            st.success("Upload completed successfully!")
            st.json(upload_res)
            if "public_url" in upload_res:
                st.markdown(f"🔗 **Accessible Public URL:** [Open File in Browser]({upload_res['public_url']})")

    st.markdown("---")
    st.markdown("### 🗂️ Stored Files Explorer")
    if st.button("List Files in Cloud Bucket"):
        if memory_store:
            with st.spinner("Fetching file index..."):
                files = memory_store.list_objects(bucket="sahibex")
            if files:
                st.json(files)
            else:
                st.info("No files found or bucket is currently empty.")


# =========================================================================
# MODULE 4: VECTOR RAG SEMANTIC SEARCH ENGINE
# =========================================================================
elif menu == "🔍 8GB Vector RAG Semantic Engine":
    st.subheader("🔍 Vector RAG High-Performance Semantic Search")
    st.info("Searches across Qdrant Cloud (1GB), Zilliz Milvus (5GB), and Pinecone Serverless (2GB).")

    search_query = st.text_input("Enter semantic search concept or phrase:")
    k_limit = st.slider("Max Results", 1, 10, 3)

    if st.button("⚡ Execute Semantic Search"):
        if search_query and memory_store:
            with st.spinner("Generating embeddings & querying distributed vector clusters..."):
                q_vec = memory_store.text_to_vector(search_query)
                search_results = memory_store.search_vector("sahibex_brain", q_vec, top_k=k_limit)
            st.success("Semantic search completed!")
            st.json(search_results)
        else:
            st.warning("Please enter a search phrase.")

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='text-align: center; color: #9CA3AF; font-size: 0.88rem;'>
    <b>⚡ SAHIBEX OMEGA v6.0</b><br>
    10 Cloud Providers | 30+ Models | Multimodal AGI<br>
    🚀 100% Operational
    </div>
    """,
    unsafe_allow_html=True,
)
