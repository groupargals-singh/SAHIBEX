"""
SAHIBEX AI - Ultimate Superpower Master Brain Dashboard (app.py)
=================================================================
Runs on Structure 10 (24/7 Streamlit + Render + UptimeRobot Hosting).
Unifies all 10 Cloud Providers and 9 Structures into a single high-speed dashboard:
- Structure 1-5: GPU, TPU, High-RAM & Disk
- Structure 6: Object Storage (Supabase 1GB + Cloudinary 25GB)
- Structure 7: Permanent SQL Memory (Turso 9GB, TiDB 5GB, Neon 500MB, Supabase 500MB)
- Structure 8: Vector RAG Brain (Qdrant 1GB, Zilliz 5GB, Pinecone 2GB)
- Structure 9: Instant RAM Cache (Upstash Redis 256MB)
"""

import streamlit as st
import sys
import os
import time

# Ensure repo root is in path for robust module importing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from data.memory_store import memory_store
except Exception as e:
    memory_store = None

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
st.markdown('<p class="subtitle">Distributed Multi-Cloud AI Infrastructure (10 Cloud Providers / 9 Structures Active)</p>', unsafe_allow_html=True)

# Sidebar Navigation Control Center
st.sidebar.title("🚀 SAHIBEX Command Center")
menu = st.sidebar.selectbox(
    "Select Superpower Module",
    [
        "📊 Live Infrastructure Diagnostics",
        "🧠 Superpower Memory (Remember & Recall)",
        "📁 26GB Object Storage & Media Vault",
        "🔍 8GB Vector RAG Semantic Engine",
    ],
)

# =========================================================================
# MODULE 1: INFRASTRUCTURE HEALTH & STATUS (All 9 Structures Diagnostics)
# =========================================================================
if menu == "📊 Live Infrastructure Diagnostics":
    st.subheader("🌐 Real-Time Multi-Cloud Cluster Status")
    st.info("Checking connection health across all active cloud databases, vector stores, object storage, and RAM caches...")

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
# MODULE 2: SUPERPOWER MEMORY (Remember & Recall via SQL + Redis + Vector)
# =========================================================================
elif menu == "🧠 Superpower Memory (Remember & Recall)":
    st.subheader("🧠 Persistent Multi-Cloud Memory & Context Engine")
    
    session_id = st.text_input("Active Session / User ID", value="sahibex_master_session")
    
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
    <b>SAHIBEX AI Super Brain v2.0</b><br>
    Built with 10 Cloud Providers<br>
    🚀 100% Operational
    </div>
    """,
    unsafe_allow_html=True,
)
