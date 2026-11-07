
import os
import streamlit as st
from openai import OpenAI
from huggingface_hub import InferenceClient

# Nayi 30+ Model Registry aur Learning Memory Injector ko safely connect karna
try:
    from core.model_registry import (
        SAHIBEX_MODEL_REGISTRY,
        SAHIBEX_MEMORY_ARCHITECTURE,
        SahibexSmartRouter,
        UnifiedMemoryInjector,
        get_registry_summary
    )
    REGISTRY_ACTIVE = True
except Exception:
    REGISTRY_ACTIVE = False


def get_secret(key_name):
    try:
        return st.secrets.get(key_name, os.environ.get(key_name, ""))
    except Exception:
        return os.environ.get(key_name, "")


class SahibexMegaBrainCluster:
    def __init__(self):
        # =====================================================================
        # Structure 1: Top 9 AI Brains with Best Flagship Models (100% INTACT)
        # =====================================================================
        self.brains = [
            {
                "name": "Groq LPU (Lightning Fast)",
                "key": get_secret("GROQ_API_KEY"),
                "url": "https://api.groq.com/openai/v1",
                "model": "llama-3.3-70b-versatile",
                "task_tags": ["general", "fast_chat", "reasoning"]
            },
            {
                "name": "NVIDIA NIM (H100 Tensor Core)",
                "key": get_secret("NVIDIA_API_KEY"),
                "url": "https://integrate.api.nvidia.com/v1",
                "model": "meta/llama-3.3-70b-instruct",
                "task_tags": ["general", "reasoning", "vision"]
            },
            {
                "name": "Cohere AI (Command-R+ RAG)",
                "key": get_secret("COHERE_API_KEY"),
                "url": "https://api.cohere.ai/v1",
                "model": "command-r-plus",
                "task_tags": ["rag_memory", "heavy_data"]
            },
            {
                "name": "SambaNova RDU (DeepSeek-R1 Logic)",
                "key": get_secret("SAMBANOVA_API_KEY"),
                "url": "https://api.sambanova.ai/v1",
                "model": "DeepSeek-R1-Distill-Llama-70B",
                "task_tags": ["reasoning", "math", "coding"]
            },
            {
                "name": "Google Gemini 2.0 Flash",
                "key": get_secret("GEMINI_API_KEY"),
                "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "model": "gemini-2.0-flash",
                "task_tags": ["long_context", "vision", "general"]
            },
            {
                "name": "OpenRouter Free Cluster",
                "key": get_secret("OPENROUTER_API_KEY"),
                "url": "https://openrouter.ai/api/v1",
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "task_tags": ["general", "coding", "architecture"]
            },
            {
                "name": "GitHub Models (GPT-4o Mini)",
                "key": get_secret("GITHUB_TOKEN"),
                "url": "https://models.inference.ai.azure.com",
                "model": "gpt-4o-mini",
                "task_tags": ["coding", "debugging", "fast_chat"]
            },
            {
                "name": "Mistral AI Engine",
                "key": get_secret("MISTRAL_API_KEY"),
                "url": "https://api.mistral.ai/v1",
                "model": "mistral-small-latest",
                "task_tags": ["coding", "debugging", "general"]
            },
            {
                "name": "Hugging Face Hub Router",
                "key": get_secret("HF_TOKEN"),
                "url": "https://api-inference.huggingface.co/v1",
                "model": "Qwen/Qwen3-235B-A22B",
                "task_tags": ["heavy_data", "reasoning", "coding"]
            }
        ]

        # =====================================================================
        # Hugging Face Dedicated Power Models (Purane 5 + Naye Specialist Models)
        # =====================================================================
        self.hf_token = get_secret("HF_TOKEN")
        self.hf_power_models = {
            # Aapke 5 Mool (Original) Power Models:
            "qwen_72b": "Qwen/Qwen2.5-72B-Instruct",
            "deepseek_r1": "deepseek-ai/DeepSeek-R1",
            "qwen3_235b": "Qwen/Qwen3-235B-A22B",
            "llama_70b": "meta-llama/Llama-3.3-70B-Instruct",
            "mistral_large": "mistralai/Mistral-Large-Instruct-2407",
            # Naye Specialist Models (from model_registry.py):
            "qwen_coder_32b": "Qwen/Qwen2.5-Coder-32B-Instruct",
            "llama_vision_90b": "meta-llama/Llama-3.2-90B-Vision-Instruct",
            "qwen_vision_72b": "Qwen/Qwen2-VL-72B-Instruct",
            "gemma_2_27b": "google/gemma-2-27b-it"
        }

        # Local GGUF Offline Server Endpoint (Port 8080 Backup)
        self.local_gguf_url = get_secret("LOCAL_GGUF_URL") or "http://127.0.0.1:8080/v1"

    # =========================================================================
    # 1. MAIN GENERATE RESPONSE (100% Compatible with Existing app.py + Memory)
    # =========================================================================
    def generate_response(
        self,
        messages,
        task_type=None,
        working_memory=None,
        sql_learned_rules=None,
        vector_experiences=None,
        offline_mode=False
    ):
        """
        Purane app.py ke sath 100% compatible:
        - Agar sirf generate_response(messages) call hoga -> (reply, brain_name) return karega.
        - Agar memory ya task_type diya jayega -> Smart Router aur 4-Layer Memory bhi lagayega.
        """
        # Agar user ne text string bheji ho toh use messages list mein badalna
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # Agar 4-Layer Learning Memory di gayi hai, toh prompt mein inject karna
        if REGISTRY_ACTIVE and any([working_memory, sql_learned_rules, vector_experiences]):
            last_user_msg = messages[-1]["content"] if messages else ""
            enriched_prompt = UnifiedMemoryInjector.build_superbrain_prompt(
                user_query=last_user_msg,
                working_memory_redis=working_memory,
                sql_learned_rules=sql_learned_rules,
                vector_rag_experiences=vector_experiences
            )
            messages = list(messages[:-1]) + [{"role": "user", "content": enriched_prompt}]

        # Agar 100% Offline GGUF Mode on hai, toh seedha Local GGUF Engine chalana
        if offline_mode:
            return self._call_local_gguf_fallback(messages)

        # Smart Task Priority: Agar task_type diya hai (e.g., 'coding', 'math'),
        # toh us kaam ke specialist brains ko list mein sabse aage rakhna
        ordered_brains = self.brains
        if task_type:
            preferred = [b for b in self.brains if task_type in b.get("task_tags", [])]
            others = [b for b in self.brains if task_type not in b.get("task_tags", [])]
            ordered_brains = preferred + others

        # Automatic Failover across all 9 Cloud Brains
        for brain in ordered_brains:
            if brain["key"]:
                try:
                    client = OpenAI(api_key=brain["key"], base_url=brain["url"])
                    res = client.chat.completions.create(
                        model=brain["model"],
                        messages=messages
                    )
                    return res.choices[0].message.content, brain["name"]
                except Exception:
                    continue

        # 10th Backup: Agar 9 Cloud APIs fail ya busy hon, toh Local GGUF (Port 8080) try karna
        local_reply, local_name = self._call_local_gguf_fallback(messages, silent_if_down=True)
        if local_reply:
            return local_reply, local_name

        return "Sabhi Cloud Brain Keys Missing hain! Streamlit Secrets check karein.", "Offline"

    # =========================================================================
    # 2. HUGGING FACE POWER MODELS (100% Intact + Extended Models)
    # =========================================================================
    def query_huggingface_power_model(self, model_key, prompt):
        if not self.hf_token:
            return "Hugging Face Token (HF_TOKEN) missing hai!"

        model_id = self.hf_power_models.get(model_key, self.hf_power_models["qwen3_235b"])
        try:
            client = InferenceClient(token=self.hf_token)
            response = client.chat_completion(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"HF Power Model Error ({model_id}): {str(e)}"

    # =========================================================================
    # 3. LOCAL GGUF OFFLINE ENGINE (100% Independent Backup Brain)
    # =========================================================================
    def _call_local_gguf_fallback(self, messages, silent_if_down=False):
        try:
            client = OpenAI(api_key="sahibex-local", base_url=self.local_gguf_url)
            res = client.chat.completions.create(
                model="local-gguf-model",
                messages=messages
            )
            return res.choices[0].message.content, "Local GGUF Brain (Port 8080)"
        except Exception:
            if silent_if_down:
                return None, None
            return (
                "Local GGUF Server (Port 8080) abhi band hai. Cloud mode on karein ya llama-server start karein.",
                "Offline GGUF Vault"
            )

    # =========================================================================
    # 4. REGISTRY & CLUSTER STATUS (100% Intact + 30+ Model Registry Info)
    # =========================================================================
    def cluster_status(self):
        status_dict = {b["name"]: bool(b["key"]) for b in self.brains}
        status_dict["Hugging Face 5-Power Models Ready"] = bool(self.hf_token)
        status_dict["30+ Master Model Registry Connected"] = REGISTRY_ACTIVE
        return status_dict

    def get_full_model_registry(self):
        """Returns the 30+ models and 4-Layer Memory specs from core/model_registry.py."""
        if REGISTRY_ACTIVE:
            return {
                "summary": get_registry_summary(),
                "models": SAHIBEX_MODEL_REGISTRY,
                "memory_layers": SAHIBEX_MEMORY_ARCHITECTURE
            }
        return {"error": "core/model_registry.py not found"}


# Alias taaki agar kahin SahibexBrainRouter naam use ho toh woh bhi bina error ke chale
SahibexBrainRouter = SahibexMegaBrainCluster
