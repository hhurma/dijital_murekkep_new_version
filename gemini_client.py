import os
import json
import urllib.request
import urllib.error

try:
    import google.generativeai as genai  # type: ignore
    _GENAI_AVAILABLE = True
except Exception:
    genai = None  # type: ignore
    _GENAI_AVAILABLE = False


class GeminiClient:
    """Basit Gemini API istemcisi (Generative Language)"""

    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        # GenAI'yi yapılandır
        if _GENAI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except Exception:
                pass

    def is_configured(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def default_models() -> list[str]:
        # Basit sabit liste; gerekirse API discovery eklenebilir
        return [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro",
        ]

    def list_models(self) -> list[str]:
        """Gemini model listesini getirebilirsek genai ile, değilse REST ile getir."""
        if not self.is_configured():
            return self.default_models()

        # Öncelik: google-generativeai
        if _GENAI_AVAILABLE:
            try:
                names = []
                for m in genai.list_models():  # type: ignore
                    name = getattr(m, "name", "")
                    # name genelde "models/gemini-1.5-flash"
                    if name.startswith("models/"):
                        name = name.split("/", 1)[1]
                    # Yalnızca generateContent destekleyenleri al
                    methods = set(getattr(m, "supported_generation_methods", []) or [])
                    if name and ("generateContent" in methods or not methods):
                        names.append(name)
                if names:
                    priority = {"gemini-1.5-flash": 0, "gemini-1.5-pro": 1}
                    return sorted(set(names), key=lambda n: priority.get(n, 99))
            except Exception:
                pass

        # Fallback: REST
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"}, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
            names = []
            for m in data.get("models", []):
                name = m.get("name", "")
                if name.startswith("models/"):
                    name = name.split("/", 1)[1]
                if name:
                    names.append(name)
            if names:
                priority = {"gemini-1.5-flash": 0, "gemini-1.5-pro": 1}
                return sorted(set(names), key=lambda n: priority.get(n, 99))
        except Exception:
            pass

        return self.default_models()

    def generate_json(self, prompt: str, schema_hint: dict) -> dict:
        """Prompt ver, JSON bekle. Öncelik google-generativeai, yedek REST."""
        if not self.is_configured():
            return {}

        system_hint = (
            "Sadece JSON döndür. Türkçe komutları algıla."
            " Eksen adları, çizgi/sembol listesi, grup adları üret."
        )

        # Öncelik: google-generativeai
        if _GENAI_AVAILABLE:
            try:
                model_name = self.model
                gm = genai.GenerativeModel(  # type: ignore
                    model_name,
                    system_instruction=system_hint,
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.2,
                        "top_k": 40,
                        "top_p": 0.9,
                        "max_output_tokens": 1024,
                    },
                )
                resp = gm.generate_content(prompt)
                text = resp.text if hasattr(resp, "text") else None
                if not text:
                    return {}
                text = text.strip()
                if text.startswith("```json"):
                    text = text[len("```json"):].strip()
                if text.startswith("```)" ):
                    text = text.split("```", 2)[1] if "```" in text else text
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        parsed.setdefault("_raw", text)
                        return parsed
                except Exception:
                    pass
                return {"_raw": text}
            except Exception:
                pass

        # Fallback: REST
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": system_hint + "\n\nİstek:" + prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.9,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json"
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            text = text.strip()
            if text.startswith("```json"):
                text = text[len("```json"):].strip()
            if text.startswith("```)" ):
                text = text.split("```", 2)[1] if "```" in text else text
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    parsed.setdefault("_raw", text)
                    return parsed
            except Exception:
                pass
            return {"_raw": text}
        except Exception:
            return {}


