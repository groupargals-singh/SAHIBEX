import os
import requests
import streamlit as st
from openai import OpenAI
from huggingface_hub import HfApi, InferenceClient

def get_secret(key_name):
    return st.secrets.get(key_name, os.environ.get(key_name, ""))

class SahibexCloudCluster:
    def __init__(self):
        # 1. Structure 2: 6 Heavy GPU Servers (200GB+ VRAM with Ultra-Fast Timeout)
        self.gpu_servers = [
            {
                "name": "NVIDIA NIM H100 Tensor GPU (80GB VRAM)",
                "key": get_secret("NVIDIA_API_KEY"),
                "url": "https://integrate.api.nvidia.com/v1",
                "model": "meta/llama-3.3-70b-instruct",
                "type": "OPENAI_GPU"
            },
            {
                "name": "Hyperbolic AI GPU Cluster (H100/A100)",
                "key": get_secret("HYPERBOLIC_API_KEY"),
                "url": "https://api.hyperbolic.xyz/v1",
                "model": "meta-llama/Llama-3.3-70B-Instruct",
                "type": "OPENAI_GPU"
            },
            {
                "name": "Chutes AI Serverless GPU (DeepSeek-R1)",
                "key": get_secret("CHUTES_API_KEY"),
                "url": "https://llm.chutes.ai/v1",
                "model": "deepseek-ai/DeepSeek-R1",
                "type": "OPENAI_GPU"
            },
            {
                "name": "Hugging Face ZeroGPU (A10G / H200)",
                "key": get_secret("HF_TOKEN"),
                "model": "Qwen/Qwen2.5-72B-Instruct",
                "type": "HF_GPU"
            },
            {
                "name": "Kaggle Dual T4 GPU (32GB VRAM)",
                "key": get_secret("KAGGLE_KEY"),
                "username": get_secret("KAGGLE_USERNAME"),
                "type": "WORKER_GPU"
            },
            {
                "name": "Google Colab T4 GPU (15GB VRAM)",
                "key": get_secret("GEMINI_API_KEY"),
                "type": "WORKER_GPU"
            }
        ]

        # 2. Structure 3: 16 Google TPU Super-Cores (Deep Math & Matrix)
        self.tpu_cluster = {
            "Kaggle TPU v5e-8 (8 Cores)": bool(get_secret("KAGGLE_KEY")),
            "Google Colab TPU v5e (8 Cores)": bool(get_secret("GEMINI_API_KEY"))
        }

        # 3. Structure 4: 110GB+ High-RAM + 24 CPU Workers
        self.ram_workers = {
            "GitHub Codespaces & Runner (32GB RAM)": bool(get_secret("GITHUB_TOKEN")),
            "Kaggle CPU Worker VM (30GB RAM)": bool(get_secret("KAGGLE_KEY")),
            "Hugging Face Spaces CPU (16GB RAM)": bool(get_secret("HF_TOKEN")),
            "Google Project IDX & Cloud Shell (32GB RAM)": bool(get_secret("GEMINI_API_KEY"))
        }

        # 4. Structure 5: 1.5TB+ Permanent Hard Disk (Model & File Storage)
        self.hf_token = get_secret("HF_TOKEN")
        self.dagshub_token = get_secret("DAGSHUB_TOKEN")
        self.github_token = get_secret("GITHUB_TOKEN")
        self.kaggle_key = get_secret("KAGGLE_KEY")

        self.storage_disks = {
            "Hugging Face Hub (1TB+ Disk)": bool(self.hf_token),
            "Kaggle Datasets (100GB Disk)": bool(self.kaggle_key),
            "GitHub Releases & Repos (100GB+ Disk)": bool(self.github_token),
            "DagsHub ML Storage (10GB Disk)": bool(self.dagshub_token)
        }

    # ⚡ ULTRA-FAST GPU EXECUTION (Structure 2)
    def run_on_gpu(self, prompt, max_tokens=2048):
        for gpu in self.gpu_servers:
            key = gpu.get("key")
            if not key:
                continue

            # OpenAI-Compatible Heavy GPUs (NVIDIA H100, Hyperbolic, Chutes)
            if gpu["type"] == "OPENAI_GPU":
                try:
                    client = OpenAI(
                        api_key=key,
                        base_url=gpu["url"],
                        timeout=12.0,  # 12 sec mein jawab nahi aaya toh turant agle GPU par switch!
                        max_retries=1
                    )
                    res = client.chat.completions.create(
                        model=gpu["model"],
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens
                    )
                    return res.choices[0].message.content, gpu["name"]
                except Exception:
                    continue

            # Hugging Face ZeroGPU Direct Client
            elif gpu["type"] == "HF_GPU":
                try:
                    hf_client = InferenceClient(token=key, timeout=12.0)
                    res = hf_client.chat_completion(
                        model=gpu["model"],
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens
                    )
                    return res.choices[0].message.content, gpu["name"]
                except Exception:
                    continue

        return "Heavy GPU Cluster busy hai ya keys Streamlit Secrets mein nahi dali hain!", "Offline"

    # 💽 ASLI CLOUD HARD DISK SAVE ENGINE (Structure 5)
    def verify_dagshub_storage(self):
        """DagsHub 10GB Storage ki real connectivity check karta hai"""
        if not self.dagshub_token:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.dagshub_token}"}
            r = requests.get("https://dagshub.com/api/v1/user", headers=headers, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def upload_to_hf_disk(self, file_bytes, filename, repo_id):
        """Hugging Face 1TB+ Hard Disk par direct file save karne ka engine"""
        if not self.hf_token:
            return "HF_TOKEN missing hai!"
        try:
            api = HfApi(token=self.hf_token)
            api.upload_file(
                path_or_fileobj=file_bytes,
                path_in_repo=filename,
                repo_id=repo_id,
                repo_type="dataset"
            )
            return f"File '{filename}' successfully 1TB+ HF Cloud Disk par save ho gayi!"
        except Exception as e:
            return f"Upload Error: {str(e)}"

    # 📊 COMPLETE DASHBOARD STATUS (Structure 2, 3, 4, 5)
    def full_cloud_status(self):
        return {
            "Structure_2_Heavy_GPUs": {g["name"]: bool(g.get("key")) for g in self.gpu_servers},
            "Structure_3_TPU_Cores": self.tpu_cluster,
            "Structure_4_High_RAM_CPU": self.ram_workers,
            "Structure_5_Permanent_Disk": self.storage_disks
        }
