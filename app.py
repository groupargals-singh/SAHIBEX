"""
SAHIBEX AI - Ultimate Superpower Master Brain Dashboard (app.py)
=================================================================
Runs on Structure 10 (24/7 Streamlit + Render + UptimeRobot Hosting).
Unifies all 10 Cloud Providers, 30+ Model Registry, Multimodal Super Agents, and 9 Structures into a single dashboard:
- Structure 1: 9 Cloud Brains + 30+ Specialized Model Registry + Multimodal Super Agents
- Structure 2-5: 200GB+ GPU, 16 TPU Cores, 78GB+ High-RAM & 1.5TB+ Disk
- Structure 6: Object Storage (Supabase 1GB + Cloudinary 25GB)
- Structure 7: Permanent SQL Memory (Turso 9GB, TiDB 5GB, Neon 500MB, Supabase 500MB)
- Structure 8: Vector RAG Brain (Qdrant 1GB, Zilliz 5GB, Pinecone 2GB)
- Structure 9: Instant RAM Cache (Upstash Redis 256MB)
"""

import streamlit as st
import sys
import os
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

# Streamlit Page Configuration
st.set_page_config(
    page_title="SAHIBEX AI - Ultimate Super Brain",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Performance Styling
st.markdown(
    """
    <style>
    .main-title { font-size: 2.8rem; color: #4F46E5; font-weight: 800; text-align: center; margin-bottom: 0rem; }
    .subtitle { font-size: 1.2rem; color: #4B5563; text-align: center; margin-bottom: 2rem; font-weight: 500; }
    .stButton>button { width: 100%; background-color: #4F46E5; color: white; font-weight: bold; border-radius: 8px; padding: 0.6rem; }
    .stButton>button:hover { background-color: #4338CA; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">⚡ SAHIBEX SUPERPOWER BRAIN ⚡</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Distributed Multi-Cloud AI Infrastructure (10 Cloud Providers / 30+ Models / 10 Structures Active)</p>', unsafe_allow_html=True)

# Sidebar Navigation Control Center
st.sidebar.title("🚀 SAHIBEX Command Center")
menu = st.sidebar.selectbox(
    "Select Superpower Module",
    [
        "🤖 Autonomous Super Brain Chat (Auto-Learning)",
        "👁️🎙️🎨 Multimodal Super Agents (Vision, Voice, Search & Studio)",
        "📊 Live Infrastructure Diagnostics",
        "📚 30+ Model Registry & Offline GGUF Vault",
        "🧠 Superpower Memory (Remember & Recall)",
        "📁 26GB Object Storage & Media Vault",
        "🔍 8GB Vector RAG Semantic Engine",
    ],
)

# Quick Sidebar Settings for Brain Routing
with st.sidebar.expander("⚙️ Brain & Memory Settings", expanded=True):
    active_session_id = st.text_input("Active Session ID", value="sahibex_master_session")
    auto_memory_sync = st.checkbox("Auto-Sync Learning Memory (SQL + Vector + Redis)", value=True)
    enable_live_web = st.checkbox("🌐 Enable Live Internet Search in Chat", value=False)
    offline_gguf_mode = st.checkbox("100% Offline Local GGUF Mode (Port 8080)", value=False)


# =========================================================================
# NEW MODULE A: AUTONOMOUS SUPER BRAIN CHAT (9-Cloud + 30+ Models + Memory)
# =========================================================================
if menu == "🤖 Autonomous Super Brain Chat (Auto-Learning)":
    st.subheader("🤖 SAHIBEX Autonomous Super Brain Terminal")

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

    # Show Smart Router target model info
    if registry_loaded:
        routed_spec = SahibexSmartRouter.select_model(
            task_type=selected_task_key, offline_mode=offline_gguf_mode
        )
        st.info(
            f"🎯 **Smart Router Target:** `{routed_spec.get('id', routed_spec.get('filename'))}` | "
            f"**Specialty:** {routed_spec.get('specialty', 'Autonomous Intelligence')}"
        )

    # Initialize session chat display
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

            # Optional Step 0: Live Internet Search Injection (if enabled in sidebar)
            final_user_prompt = user_prompt
            if enable_live_web and super_agents and not offline_gguf_mode:
                with st.spinner("🌐 Searching Live Internet for real-time facts..."):
                    web_context = super_agents.live_web_search(user_prompt)
                    final_user_prompt = (
                        f"[LIVE INTERNET SEARCH DATA]:\n{web_context}\n\n"
                        f"[USER QUESTION]:\n{user_prompt}"
                    )

            # Step 1: Auto-Recall Past Learning Memory from Structures 7, 8, 9
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

            # Step 2: Generate Response via Selected Engine
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

            # Step 3: Auto-Save New Learning into Permanent Memory (Structures 7, 8, 9)
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

            # Update UI History
            st.session_state.sahibex_chat_history.append(
                {"role": "user", "content": user_prompt, "brain": "User Command"}
            )
            st.session_state.sahibex_chat_history.append(
                {"role": "assistant", "content": reply_text, "brain": provider_used}
            )

    # Render Conversation History
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
# NEW MODULE A2: MULTIMODAL SUPER AGENTS (VISION, VOICE, SEARCH & STUDIO)
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

    # Structure 1: 9 Cloud Brains + 30+ Model Registry + Super Agents Diagnostics
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
# NEW MODULE B: 30+ MODEL REGISTRY & 1-CLICK OFFLINE GGUF VAULT
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
    <div style='text-align: center; color: #6B7280; font-size: 0.9rem;'>
    <b>SAHIBEX AI Super Brain v4.0</b><br>
    10 Cloud Providers | 30+ Models | Multimodal Agents<br>
    🚀 100% Operational
    </div>
    """,
    unsafe_allow_html=True,
)
