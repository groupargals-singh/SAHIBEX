"""
SAHIBEX SUPER BRAIN - AUTONOMOUS SUPER AGENTS (SEARCH, VISION, VOICE & IMAGE GEN)
File: core/super_agents.py
Zero-crash architecture: Uses existing packages (requests, openai, huggingface_hub)
to give SAHIBEX Eyes, Ears, Live Web Search, and Visual Studio capabilities.
"""

import os
import io
import base64
import urllib.parse
import requests
import streamlit as st
from openai import OpenAI
from huggingface_hub import InferenceClient


def get_secret(key_name: str) -> str:
    try:
        return st.secrets.get(key_name, os.environ.get(key_name, ""))
    except Exception:
        return os.environ.get(key_name, "")


class SahibexSuperAgents:
    """
    Provides Multimodal & Autonomous Agent capabilities to SAHIBEX:
    1. Live Web Search (Tavily + Free DuckDuckGo/Wikipedia API Fallback)
    2. Vision Analysis (Gemini 2.0 Flash + Groq Llama-3.2 Vision)
    3. Speech-to-Text (Groq Whisper-Large-v3-Turbo)
    4. Image Generation (HuggingFace FLUX.1-dev)
    """

    def __init__(self):
        self.groq_key = get_secret("GROQ_API_KEY")
        self.gemini_key = get_secret("GEMINI_API_KEY")
        self.nvidia_key = get_secret("NVIDIA_API_KEY")
        self.hf_token = get_secret("HF_TOKEN")
        self.tavily_key = get_secret("TAVILY_API_KEY")

    # =========================================================================
    # 1. LIVE INTERNET SEARCH AGENT (HATH-PAIR: REAL-TIME WEB DATA)
    # =========================================================================
    def live_web_search(self, query: str) -> str:
        """Fetches live internet information using Tavily or Free Web APIs."""
        results = []

        # Method A: Tavily AI Search (if key is present)
        if self.tavily_key:
            try:
                res = requests.post(
                    "https://api.tavily.com/search",
                    json={"api_key": self.tavily_key, "query": query, "max_results": 4},
                    timeout=15,
                )
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("results", []):
                        results.append(f"• **{item.get('title')}**: {item.get('content')} ({item.get('url')})")
                    if results:
                        return "\n\n".join(results)
            except Exception:
                pass

        # Method B: 100% Free DuckDuckGo Instant API (No API key needed)
        try:
            encoded_q = urllib.parse.quote(query)
            ddg_url = f"https://api.duckduckgo.com/?q={encoded_q}&format=json&no_html=1&skip_disambig=1"
            res = requests.get(ddg_url, timeout=12)
            if res.status_code == 200:
                data = res.json()
                if data.get("AbstractText"):
                    results.append(f"• **Summary**: {data['AbstractText']} (Source: {data.get('AbstractURL', 'Web')})")
                for topic in data.get("RelatedTopics", [])[:4]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append(f"• {topic['Text']}")
        except Exception:
            pass

        # Method C: Free Wikipedia Live Search Fallback (Great for facts, companies, stocks, history)
        try:
            wiki_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 3,
            }
            headers = {"User-Agent": "SAHIBEX-SuperBrain/3.0"}
            res = requests.get(wiki_url, params=params, headers=headers, timeout=12)
            if res.status_code == 200:
                search_items = res.json().get("query", {}).get("search", [])
                for item in search_items:
                    snippet = item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                    results.append(f"• **{item.get('title')}**: {snippet}...")
        except Exception:
            pass

        if results:
            return "\n\n".join(results)
        return "Live web search par is waqt koi direct result nahi mila, lekin AI Brain apni knowledge se jawab dega."

    # =========================================================================
    # 2. VISION ENGINE (SAHIBEX KI AANKHEIN: IMAGE, OCR & SCREENSHOT READER)
    # =========================================================================
    def analyze_image(self, image_bytes: bytes, prompt: str = "Is image ko detail mein samjhao aur agar koi text ya code hai toh nikaal kar do.") -> tuple:
        """Reads any image/screenshot using Gemini 2.0 Flash or Groq Llama-3.2 Vision."""
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        vision_providers = [
            {
                "name": "Google Gemini 2.0 Flash Vision",
                "key": self.gemini_key,
                "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "model": "gemini-2.0-flash",
            },
            {
                "name": "Groq Llama-3.2 Vision",
                "key": self.groq_key,
                "url": "https://api.groq.com/openai/v1",
                "model": "llama-3.2-11b-vision-preview",
            },
            {
                "name": "NVIDIA NIM Llama-3.2-90B Vision",
                "key": self.nvidia_key,
                "url": "https://integrate.api.nvidia.com/v1",
                "model": "meta/llama-3.2-90b-vision-instruct",
            },
        ]

        for vp in vision_providers:
            if vp["key"]:
                try:
                    client = OpenAI(api_key=vp["key"], base_url=vp["url"])
                    response = client.chat.completions.create(
                        model=vp["model"],
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                                    },
                                ],
                            }
                        ],
                        max_tokens=1500,
                    )
                    return response.choices[0].message.content, vp["name"]
                except Exception:
                    continue

        return "Vision API Key (GEMINI_API_KEY ya GROQ_API_KEY) check karein.", "Vision Offline"

    # =========================================================================
    # 3. VOICE ENGINE (SAHIBEX KE KAAN: WHISPER-LARGE-V3-TURBO STT)
    # =========================================================================
    def speech_to_text(self, audio_bytes: bytes, filename: str = "voice.wav") -> str:
        """Converts Hindi/English voice audio into text using Groq Whisper-Large-v3-Turbo."""
        if not self.groq_key:
            return "Voice sunne ke liye GROQ_API_KEY zaroori hai."

        try:
            client = OpenAI(api_key=self.groq_key, base_url="https://api.groq.com/openai/v1")
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename
            transcription = client.audio.transcriptions.create(
                file=(filename, audio_file.read()),
                model="whisper-large-v3-turbo",
            )
            return transcription.text
        except Exception as e:
            return f"Voice Transcription Error: {str(e)}"

    # =========================================================================
    # 4. VISUAL STUDIO (IMAGE GENERATION: FLUX.1-DEV / STABLE DIFFUSION)
    # =========================================================================
    def generate_image(self, prompt: str) -> tuple:
        """Generates high-resolution AI images using Hugging Face FLUX.1-dev."""
        if not self.hf_token:
            return None, "HF_TOKEN missing hai! Streamlit Secrets mein HF_TOKEN check karein."

        models_to_try = [
            "black-forest-labs/FLUX.1-schnell",
            "black-forest-labs/FLUX.1-dev",
            "stabilityai/stable-diffusion-xl-base-1.0",
        ]

        client = InferenceClient(token=self.hf_token)
        for model_id in models_to_try:
            try:
                image = client.text_to_image(prompt=prompt, model=model_id)
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                return buf.getvalue(), model_id
            except Exception:
                continue

        return None, "Image Generation server abhi busy hai. Thodi der baad try karein."


# Global instance for easy import across SAHIBEX
super_agents = SahibexSuperAgents()
