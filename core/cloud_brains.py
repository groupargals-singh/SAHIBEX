import os
import streamlit as st
from openai import OpenAI
from huggingface_hub import InferenceClient

def get_secret(key_name):
    return st.secrets.get(key_name, os.environ.get(key_name, ""))

class SahibexMegaBrainCluster:
    def __init__(self):
        # Structure 1: Top 9 AI Brains with Best Flagship Models
        self.brains = [
            {
                "name": "Groq LPU (Lightning Fast)",
                "key": get_secret("GROQ_API_KEY"),
                "url": "https://api.groq.com/openai/v1",
                "model": "llama-3.3-70b-versatile"
            },
            {
                "name": "NVIDIA NIM (H100 Tensor Core)",
                "key": get_secret("NVIDIA_API_KEY"),
                "url": "https://integrate.api.nvidia.com/v1",
                "model": "meta/llama-3.3-70b-instruct"
            },
            {
                "name": "Cohere AI (Command-R+ RAG)",
                "key": get_secret("COHERE_API_KEY"),
                "url": "https://api.cohere.ai/v1",
                "model": "command-r-plus"
            },
            {
                "name": "SambaNova RDU (DeepSeek-R1 Logic)",
                "key": get_secret("SAMBANOVA_API_KEY"),
                "url": "https://api.sambanova.ai/v1",
                "model": "DeepSeek-R1-Distill-Llama-70B"
            },
            {
                "name": "Google Gemini 2.0 Flash",
                "key": get_secret("GEMINI_API_KEY"),
                "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "model": "gemini-2.0-flash"
            },
            {
                "name": "OpenRouter Free Cluster",
                "key": get_secret("OPENROUTER_API_KEY"),
                "url": "https://openrouter.ai/api/v1",
                "model": "meta-llama/llama-3.3-70b-instruct:free"
            },
            {
                "name": "GitHub Models (GPT-4o Mini)",
                "key": get_secret("GITHUB_TOKEN"),
                "url": "https://models.inference.ai.azure.com",
                "model": "gpt-4o-mini"
            },
            {
                "name": "Mistral AI Engine",
                "key": get_secret("MISTRAL_API_KEY"),
                "url": "https://api.mistral.ai/v1",
                "model": "mistral-small-latest"
            },
            {
                "name": "Hugging Face Hub Router",
                "key": get_secret("HF_TOKEN"),
                "url": "https://api-inference.huggingface.co/v1",
                "model": "Qwen/Qwen3-235B-A22B"
            }
        ]

        # Hugging Face ke 5 Sabse Powerful Models Dedicated Dictionary
        self.hf_token = get_secret("HF_TOKEN")
        self.hf_power_models = {
            "qwen_72b": "Qwen/Qwen2.5-72B-Instruct",
            "deepseek_r1": "deepseek-ai/DeepSeek-R1",
            "qwen3_235b": "Qwen/Qwen3-235B-A22B",
            "llama_70b": "meta-llama/Llama-3.3-70B-Instruct",
            "mistral_large": "mistralai/Mistral-Large-Instruct-2407"
        }

    def generate_response(self, messages):
        # Automatic Failover across all 9 Brains
        for brain in self.brains:
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
        return "Sabhi Cloud Brain Keys Missing hain! Streamlit Secrets check karein.", "Offline"

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

    def cluster_status(self):
        status_dict = {b["name"]: bool(b["key"]) for b in self.brains}
        status_dict["Hugging Face 5-Power Models Ready"] = bool(self.hf_token)
        return status_dict
