"""
SAHIBEX AUTONOMOUS SUPER BRAIN - MASTER MODEL REGISTRY & LEARNING MEMORY VAULT
File: core/model_registry.py
Contains:
1. All 30+ Ultimate Models across 9 Specialized Categories
2. Direct Hugging Face GGUF Weights Vault for 100% Offline Survival
3. 4-Layer Learning Memory Bridge (Redis + 4-SQL + 3-Vector + Media Vault)
4. Autonomous Smart Task Router
"""

import os
import time
import urllib.request
from typing import Dict, List, Any, Optional


# ==============================================================================
# 1. MASTER 30+ MODEL REGISTRY (ALL 9 SUPERPOWERS)
# ==============================================================================

SAHIBEX_MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {

    # --- 1. CORE THINKING, REASONING & MASTER LOGIC (ASLI DIMAG) ---
    "reasoning_models": {
        "deepseek-r1": {
            "id": "deepseek-r1",
            "hf_id": "deepseek-ai/DeepSeek-R1",
            "openrouter_id": "deepseek/deepseek-r1",
            "nim_id": "deepseek-ai/deepseek-r1",
            "providers": ["NVIDIA NIM", "OpenRouter", "SambaNova", "Chutes AI"],
            "size_gb": 404.0,
            "location": "Structure 1 & 2 (Cloud API / GPU Cluster)",
            "specialty": "Step-by-step deep reasoning, complex math, and scientific logic"
        },
        "llama-3.3-70b-versatile": {
            "id": "llama-3.3-70b-versatile",
            "hf_id": "meta-llama/Llama-3.3-70B-Instruct",
            "nim_id": "meta/llama-3.3-70b-instruct",
            "providers": ["Groq", "NVIDIA NIM", "OpenRouter", "HuggingFace"],
            "size_gb": 42.5,
            "location": "Structure 1 (9-API Cloud Brain)",
            "specialty": "Main Master Brain for fast general intelligence and multi-tasking"
        },
        "qwen-2.5-72b-instruct": {
            "id": "Qwen/Qwen2.5-72B-Instruct",
            "openrouter_id": "qwen/qwen-2.5-72b-instruct",
            "providers": ["HuggingFace", "OpenRouter", "Hyperbolic"],
            "size_gb": 47.0,
            "location": "Structure 1 & 2 (Cloud API / Heavy GPU)",
            "specialty": "Heavy data processing, multilingual comprehension, and long-context analysis"
        },
        "claude-3-5-sonnet": {
            "id": "claude-3-5-sonnet",
            "openrouter_id": "anthropic/claude-3.5-sonnet",
            "providers": ["OpenRouter"],
            "size_gb": 0.0,
            "location": "Structure 1 (Cloud API Bridge)",
            "specialty": "Complex software architecture design and human-level reasoning"
        },
        "gemini-1.5-pro": {
            "id": "gemini-1.5-pro",
            "providers": ["Google AI Studio"],
            "size_gb": 0.0,
            "location": "Structure 1 (Google Cloud Brain)",
            "specialty": "2-Million token context window for massive books, codebases, and videos"
        },
        "mistral-large-latest": {
            "id": "mistral-large-latest",
            "providers": ["Mistral AI", "GitHub Models"],
            "size_gb": 73.0,
            "location": "Structure 1 (Cloud API Brain)",
            "specialty": "High-precision European flagship model for strict instruction following"
        }
    },

    # --- 2. DEDICATED CODING & SOFTWARE ENGINEERING (CODE MASTERMINDS) ---
    "coding_models": {
        "qwen-2.5-coder-32b": {
            "id": "Qwen/Qwen2.5-Coder-32B-Instruct",
            "openrouter_id": "qwen/qwen-2.5-coder-32b-instruct",
            "providers": ["HuggingFace", "OpenRouter", "Chutes AI"],
            "size_gb": 20.0,
            "location": "Structure 1 & 2 (Cloud / GPU Cluster)",
            "specialty": " #1 Open-source coding model for Python, JS, and full-stack software build"
        },
        "codestral-latest": {
            "id": "codestral-latest",
            "openrouter_id": "mistralai/codestral-2501",
            "providers": ["Mistral AI", "OpenRouter"],
            "size_gb": 13.5,
            "location": "Structure 1 (Mistral Coding Engine)",
            "specialty": "Ultra-fast code generation and completion across 80+ languages"
        },
        "deepseek-coder-v2": {
            "id": "deepseek-coder-v2",
            "openrouter_id": "deepseek/deepseek-chat",
            "providers": ["OpenRouter", "DeepSeek"],
            "size_gb": 16.0,
            "location": "Structure 1 & 2 (Cloud / GPU Cluster)",
            "specialty": "Large repository debugging and complex algorithm writing"
        }
    },

    # --- 3. ULTRA-FAST CHAT & RAG MEMORY MODELS (SPEED & DATABASE SEARCH) ---
    "fast_rag_models": {
        "llama-3.1-8b-instant": {
            "id": "llama-3.1-8b-instant",
            "providers": ["Groq LPU"],
            "size_gb": 4.9,
            "location": "Structure 1 (Groq High-Speed LPU)",
            "specialty": "0.1 second instant chat response and real-time UI interaction"
        },
        "command-r-plus": {
            "id": "command-r-plus",
            "api_id": "command-r-plus-08-2024",
            "providers": ["Cohere", "GitHub Models"],
            "size_gb": 60.0,
            "location": "Structure 1 & 8 (RAG Memory Synthesizer)",
            "specialty": "RAG Specialist: searches SQL & Vector databases and summarizes with citations"
        },
        "gemma-2-27b-it": {
            "id": "google/gemma-2-27b-it",
            "providers": ["NVIDIA NIM", "Groq", "HuggingFace"],
            "size_gb": 16.5,
            "location": "Structure 1 (NVIDIA NIM / Groq)",
            "specialty": "Fast factual verification and clean JSON structured output"
        }
    },

    # --- 4. 100% INDEPENDENT OFFLINE / LOCAL BACKUP MODELS (GGUF FORMAT) ---
    "offline_gguf_models": {
        "qwen3-4b-gguf": {
            "id": "Qwen3-4B-Q4_K_M.gguf",
            "filename": "Qwen3-4B-Q4_K_M.gguf",
            "hf_repo": "Qwen/Qwen2.5-3B-Instruct-GGUF",
            "download_url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
            "size_gb": 2.5,
            "ram_required_gb": 4.0,
            "location": "Structure 5 (1.5TB Cloud Disk / Local Server Port 8080)",
            "specialty": "Primary Local Brain: balanced reasoning and 100% offline execution"
        },
        "qwen3-1.7b-gguf": {
            "id": "Qwen3-1.7B-Q4_K_M.gguf",
            "filename": "Qwen3-1.7B-Q4_K_M.gguf",
            "hf_repo": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
            "download_url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
            "size_gb": 1.1,
            "ram_required_gb": 2.2,
            "location": "Structure 5 (1.5TB Cloud Disk / Local Server Port 8080)",
            "specialty": "Ultra-light emergency brain: runs 24/7 on minimum RAM"
        },
        "llama-3.2-3b-gguf": {
            "id": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "hf_repo": "bartowski/Llama-3.2-3B-Instruct-GGUF",
            "download_url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "size_gb": 2.0,
            "ram_required_gb": 3.8,
            "location": "Structure 5 (1.5TB Cloud Disk / Local Vault)",
            "specialty": "Offline general chat and autonomous local agent routing"
        },
        "phi-3.5-mini-gguf": {
            "id": "Phi-3.5-mini-instruct-Q4_K_M.gguf",
            "filename": "Phi-3.5-mini-instruct-Q4_K_M.gguf",
            "hf_repo": "bartowski/Phi-3.5-mini-instruct-GGUF",
            "download_url": "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf",
            "size_gb": 2.2,
            "ram_required_gb": 4.0,
            "location": "Structure 5 (1.5TB Cloud Disk / Local Vault)",
            "specialty": "Compact Microsoft logic model for offline calculations and quick tasks"
        },
        "deepseek-r1-7b-gguf": {
            "id": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
            "filename": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
            "hf_repo": "unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF",
            "download_url": "https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-7B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
            "size_gb": 4.7,
            "ram_required_gb": 7.5,
            "location": "Structure 2 & 5 (Dedicated GPU / Cloud Disk)",
            "specialty": "Offline deep step-by-step reasoning and complex problem solving"
        }
    },

    # --- 5. VISION & MULTIMODAL MODELS (SAHIBEX KI AANKHEIN) ---
    "vision_models": {
        "llama-3.2-90b-vision": {
            "id": "llama-3.2-90b-vision-instruct",
            "providers": ["Groq", "NVIDIA NIM", "OpenRouter"],
            "size_gb": 55.0,
            "location": "Structure 1 & 2 (Vision Cloud Cluster)",
            "specialty": "Reads images, charts, and UI screenshots to generate code or analysis"
        },
        "qwen2-vl-72b": {
            "id": "Qwen/Qwen2-VL-72B-Instruct",
            "providers": ["HuggingFace", "OpenRouter"],
            "size_gb": 45.0,
            "location": "Structure 1 & 2 (Multimodal Cluster)",
            "specialty": "High-precision OCR, handwritten notes, and complex diagram reading"
        },
        "pixtral-12b": {
            "id": "pixtral-12b-2409",
            "providers": ["Mistral AI"],
            "size_gb": 8.5,
            "location": "Structure 1 (Mistral Vision Engine)",
            "specialty": "Fast image recognition and multi-image comparison"
        }
    },

    # --- 6. SPEECH & AUDIO MODELS (SAHIBEX KE KAAN AUR ZUBAAN) ---
    "audio_models": {
        "whisper-large-v3-turbo": {
            "id": "whisper-large-v3-turbo",
            "providers": ["Groq", "HuggingFace"],
            "size_gb": 1.6,
            "location": "Structure 1 (Audio Speech Engine)",
            "specialty": "Speech-to-Text (STT): converts Hindi/English voice commands to text with 99% accuracy"
        },
        "kokoro-82m": {
            "id": "hexgrad/Kokoro-82M",
            "providers": ["HuggingFace", "Local"],
            "size_gb": 0.35,
            "location": "Structure 5 (Fast Voice Synthesizer)",
            "specialty": "Text-to-Speech (TTS): free and super-fast natural voice output"
        },
        "eleven-multilingual-v2": {
            "id": "eleven_multilingual_v2",
            "providers": ["ElevenLabs"],
            "size_gb": 0.0,
            "location": "Structure 1 (Voice API)",
            "specialty": "Human-like emotional Hindi and English voice synthesis"
        }
    },

    # --- 7. VECTOR EMBEDDING & RERANKING (8GB RAG MEMORY ENGINE) ---
    "embedding_models": {
        "bge-m3": {
            "id": "BAAI/bge-m3",
            "dimensions": 1024,
            "providers": ["HuggingFace", "NVIDIA NIM"],
            "size_gb": 2.2,
            "location": "Structure 8 (Zilliz + Pinecone + Qdrant Indexer)",
            "specialty": "Converts Hindi + English text into high-accuracy mathematical vectors"
        },
        "nomic-embed-text-v1.5": {
            "id": "nomic-ai/nomic-embed-text-v1.5",
            "dimensions": 768,
            "providers": ["HuggingFace", "Local"],
            "size_gb": 0.55,
            "location": "Structure 8 (Vector RAG Brain)",
            "specialty": "Fast embedding model for storing large documents in long-term memory"
        },
        "rerank-multilingual-v3.0": {
            "id": "rerank-multilingual-v3.0",
            "providers": ["Cohere"],
            "size_gb": 0.0,
            "location": "Structure 8 (Precision Memory Filter)",
            "specialty": "Filters top 3 most accurate memories out of 100 vector search results"
        }
    },

    # --- 8. IMAGE GENERATION MODELS (VISUAL STUDIO) ---
    "image_gen_models": {
        "flux-1-dev": {
            "id": "black-forest-labs/FLUX.1-dev",
            "providers": ["HuggingFace ZeroGPU", "Chutes AI"],
            "size_gb": 23.8,
            "location": "Structure 2 & 6 (GPU Cluster -> Saves to Cloudinary/Supabase)",
            "specialty": "Generates ultra-realistic photos and sharp typography images"
        },
        "stable-diffusion-3.5-large": {
            "id": "stabilityai/stable-diffusion-3.5-large",
            "providers": ["HuggingFace", "Stability AI"],
            "size_gb": 16.5,
            "location": "Structure 2 & 6 (GPU Cluster -> Saves to Cloudinary/Supabase)",
            "specialty": "Custom art, UI mockups, and graphic design generation"
        }
    },

    # --- 9. AUTONOMOUS AGENTS, LIVE SEARCH & SANDBOX TOOLS (HATH-PAIR) ---
    "agent_tools": {
        "langgraph-crewai": {
            "id": "LangGraph + CrewAI Orchestrator",
            "providers": ["Internal SAHIBEX Core"],
            "size_gb": 0.05,
            "location": "Structure 4 & 10 (78GB RAM Pool & Master Dashboard)",
            "specialty": "Creates multi-agent teams that plan and finish multi-step workflows autonomously"
        },
        "tavily-ddg-search": {
            "id": "Tavily AI + DuckDuckGo Live Search",
            "providers": ["Tavily API", "DuckDuckGo"],
            "size_gb": 0.01,
            "location": "Structure 1 (Live Internet Connector)",
            "specialty": "Fetches real-time stock market data, live news, and fresh web information"
        },
        "e2b-code-sandbox": {
            "id": "E2B Cloud Code Interpreter",
            "providers": ["E2B Sandbox", "Subprocess Virtual Env"],
            "size_gb": 0.02,
            "location": "Structure 4 (Isolated Execution Sandbox)",
            "specialty": "Runs and tests AI-written code in a safe box before delivering error-free results"
        }
    }
}


# ==============================================================================
# 2. SAHIBEX 4-LAYER LEARNING MEMORY ARCHITECTURE (HOW MEMORY STAYS SAFE)
# ==============================================================================

SAHIBEX_MEMORY_ARCHITECTURE: Dict[str, Dict[str, Any]] = {
    "layer_1_working_memory": {
        "structure": "Structure 9 (Instant RAM Cache)",
        "providers": ["Upstash Serverless Redis"],
        "capacity": "256 MB Ultra-Fast RAM",
        "latency": "0.001 seconds",
        "what_is_saved": "Active conversation context, last 20 messages, and live agent state."
    },
    "layer_2_episodic_rule_memory": {
        "structure": "Structure 7 (Permanent SQL Memory Cluster)",
        "providers": ["Turso SQLite (9GB)", "TiDB MySQL (5GB)", "Neon PostgreSQL (500MB)", "Supabase PostgreSQL (500MB)"],
        "capacity": "15.0 GB Distributed SQL",
        "replication": "4-Cloud Auto-Failover & Sync",
        "what_is_saved": "All chat history, Pankaj Singh Argal's personal rules, learned preferences, and project logs."
    },
    "layer_3_long_term_learning_rag": {
        "structure": "Structure 8 (Vector Semantic Brain)",
        "providers": ["Zilliz Cloud Milvus (5GB)", "Pinecone Serverless (2GB)", "Qdrant Cloud (1GB)"],
        "capacity": "8.0 GB Vector Storage",
        "embedding_engine": "BAAI/bge-m3 (1024-dim)",
        "what_is_saved": "Deep learned knowledge, code solutions, PDFs, and semantic experiences across all models."
    },
    "layer_4_media_and_model_vault": {
        "structure": "Structure 5 & 6 (Object & Mass Disk Storage)",
        "providers": ["Cloudinary (25GB)", "Supabase Storage (1GB)", "Cloud Hard Disk (1.5TB+)"],
        "capacity": "26 GB Fast Object + 1.5 TB Mass Disk",
        "what_is_saved": "Generated images, voice notes, documents, datasets, and offline .gguf model files."
    }
}


# ==============================================================================
# 3. SMART TASK ROUTER (AUTOMATICALLY PICKS THE BEST MODEL FOR EVERY TASK)
# ==============================================================================

class SahibexSmartRouter:
    """
    Selects the strongest model from SAHIBEX_MODEL_REGISTRY based on task type.
    Automatically switches to 100% Offline GGUF models if cloud APIs are disabled.
    """

    @staticmethod
    def select_model(task_type: str = "general", offline_mode: bool = False) -> Dict[str, Any]:
        task = task_type.lower().strip()

        # If 100% Offline Mode is active, route strictly to local/cloud-disk GGUF weights
        if offline_mode:
            if task in ["reasoning", "math", "logic", "coding", "debugging"]:
                return SAHIBEX_MODEL_REGISTRY["offline_gguf_models"]["deepseek-r1-7b-gguf"]
            elif task in ["ultra_light", "emergency"]:
                return SAHIBEX_MODEL_REGISTRY["offline_gguf_models"]["qwen3-1.7b-gguf"]
            return SAHIBEX_MODEL_REGISTRY["offline_gguf_models"]["qwen3-4b-gguf"]

        # Online Multi-Cloud Routing Map
        routing_table = {
            "reasoning": SAHIBEX_MODEL_REGISTRY["reasoning_models"]["deepseek-r1"],
            "math": SAHIBEX_MODEL_REGISTRY["reasoning_models"]["deepseek-r1"],
            "general": SAHIBEX_MODEL_REGISTRY["reasoning_models"]["llama-3.3-70b-versatile"],
            "heavy_data": SAHIBEX_MODEL_REGISTRY["reasoning_models"]["qwen-2.5-72b-instruct"],
            "architecture": SAHIBEX_MODEL_REGISTRY["reasoning_models"]["claude-3-5-sonnet"],
            "long_context": SAHIBEX_MODEL_REGISTRY["reasoning_models"]["gemini-1.5-pro"],
            "coding": SAHIBEX_MODEL_REGISTRY["coding_models"]["qwen-2.5-coder-32b"],
            "debugging": SAHIBEX_MODEL_REGISTRY["coding_models"]["codestral-latest"],
            "fast_chat": SAHIBEX_MODEL_REGISTRY["fast_rag_models"]["llama-3.1-8b-instant"],
            "rag_memory": SAHIBEX_MODEL_REGISTRY["fast_rag_models"]["command-r-plus"],
            "vision": SAHIBEX_MODEL_REGISTRY["vision_models"]["llama-3.2-90b-vision"],
            "ocr": SAHIBEX_MODEL_REGISTRY["vision_models"]["qwen2-vl-72b"],
            "voice_stt": SAHIBEX_MODEL_REGISTRY["audio_models"]["whisper-large-v3-turbo"],
            "voice_tts": SAHIBEX_MODEL_REGISTRY["audio_models"]["kokoro-82m"],
            "image_gen": SAHIBEX_MODEL_REGISTRY["image_gen_models"]["flux-1-dev"]
        }

        return routing_table.get(task, routing_table["general"])


# ==============================================================================
# 4. UNIFIED LEARNING MEMORY INJECTOR (KEEPS MEMORY SAFE ACROSS ALL MODELS)
# ==============================================================================

class UnifiedMemoryInjector:
    """
    Injects SAHIBEX's persistent learning memory (from SQL Structure 7, Vector Structure 8,
    and Redis Structure 9) into whichever AI model is currently active.
    Even if a cloud company shuts down, the new model immediately inherits 100% of past learnings.
    """

    @staticmethod
    def build_superbrain_prompt(
        user_query: str,
        working_memory_redis: Optional[List[str]] = None,
        sql_learned_rules: Optional[List[str]] = None,
        vector_rag_experiences: Optional[List[str]] = None
    ) -> str:
        redis_block = "\n".join(working_memory_redis[-10:]) if working_memory_redis else "No recent instant cache."
        sql_block = "\n".join(sql_learned_rules) if sql_learned_rules else "Core Owner: Pankaj Singh Argal. Mode: Autonomous Super Brain."
        vector_block = "\n".join(vector_rag_experiences) if vector_rag_experiences else "No prior semantic matches required."

        return (
            "### SAHIBEX AUTONOMOUS SUPER BRAIN KERNEL ###\n"
            "Identity: SAHIBEX Super Brain (Created & Controlled by Pankaj Singh Argal).\n"
            "Architecture: 10-Structure Multi-Cloud & Local GGUF Hybrid.\n\n"
            f"[1. PERMANENT LEARNED RULES & SQL MEMORY (Structure 7 - 15GB Cluster)]:\n{sql_block}\n\n"
            f"[2. LONG-TERM SEMANTIC LEARNING & RAG (Structure 8 - 8GB Vector Brain)]:\n{vector_block}\n\n"
            f"[3. ACTIVE WORKING MEMORY (Structure 9 - Upstash Redis 0.001s Cache)]:\n{redis_block}\n\n"
            f"[USER COMMAND]:\n{user_query}\n\n"
            "Instruction: Execute the command accurately using your persistent memory above."
        )


# ==============================================================================
# 5. 1-CLICK GGUF DOWNLOADER & REGISTRY STATS
# ==============================================================================

def download_offline_model(model_key: str = "qwen3-4b-gguf", target_dir: str = "models") -> str:
    """
    Downloads any offline GGUF model directly from Hugging Face onto Structure 5
    (1.5TB Cloud Disk) or local directory whenever needed.
    """
    offline_catalog = SAHIBEX_MODEL_REGISTRY["offline_gguf_models"]
    if model_key not in offline_catalog:
        raise ValueError(f"Unknown model key '{model_key}'. Choose from: {list(offline_catalog.keys())}")

    model_meta = offline_catalog[model_key]
    os.makedirs(target_dir, exist_ok=True)
    destination = os.path.join(target_dir, model_meta["filename"])

    if not os.path.exists(destination):
        print(f"[SAHIBEX VAULT] Downloading {model_meta['filename']} ({model_meta['size_gb']} GB)...")
        urllib.request.urlretrieve(model_meta["download_url"], destination)
        print(f"[SAHIBEX VAULT] Saved successfully at: {destination}")
    else:
        print(f"[SAHIBEX VAULT] Verified existing model at: {destination}")

    return destination


def get_registry_summary() -> Dict[str, Any]:
    """Returns complete statistics of all models and memory structures."""
    category_counts = {cat: len(models) for cat, models in SAHIBEX_MODEL_REGISTRY.items()}
    total_models = sum(category_counts.values())
    return {
        "total_registered_models": total_models,
        "categories": category_counts,
        "memory_layers": len(SAHIBEX_MEMORY_ARCHITECTURE)
    }


if __name__ == "__main__":
    summary = get_registry_summary()
    print(f"SAHIBEX Model Registry Loaded: {summary['total_registered_models']} Models across {len(summary['categories'])} Categories.")
