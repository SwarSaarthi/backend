"""Short, contextual Hindi voice conversations using the existing AI credentials."""
import httpx
from app.config import settings
from app.services.feedback_language import coaching_matches_language

SYSTEM = """आप स्वर सारथी के धैर्यवान हिंदी बोलचाल साथी हैं। शिक्षार्थी के आखिरी संदेश का सीधे जवाब दें और बातचीत के पिछले संदर्भ को याद रखें।
सिर्फ सहज हिंदी और देवनागरी में बोलें। अंग्रेज़ी या रोमन हिंदी न लिखें। जवाब बोलकर सुनाया जाएगा, इसलिए सजावटी चिह्न, तालिका और मार्कडाउन न दें।
आमतौर पर दो से चार छोटे वाक्य और अंत में एक आसान सवाल रखें। एक समय में एक अभ्यास दें। शिक्षार्थी अधिक विवरण मांगे तो समझाएं।
उनके दिन, रुचियों और रोज़मर्रा की स्थितियों पर बातचीत करके बोलने का अभ्यास करवाएं। गलत वाक्य हो तो विनम्रता से एक बेहतर उदाहरण दें।
आपको केवल आवाज़ से पहचाना गया पाठ मिलता है। आवाज़ की गुणवत्ता, वास्तविक जीभ की स्थिति या उच्चारण का अंक न गढ़ें। अंक के लिए निर्देशित अभ्यास का सुझाव दें।
चिकित्सकीय निदान न दें। अपने आप को इंसान न बताएं। सुनाई न देने या अस्पष्ट पाठ पर विनम्रता से दोबारा बोलने को कहें।"""


async def reply_to_turn(history: list[dict[str, str]], text: str) -> dict[str, str]:
    messages = history[-12:] + [{"role": "user", "content": text}]
    async with httpx.AsyncClient(timeout=httpx.Timeout(25, connect=5)) as client:
        if settings.SWAR_GOOGLE_KEY:
            try:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{settings.VOICE_GEMINI_MODEL}:generateContent",
                    headers={"x-goog-api-key": settings.SWAR_GOOGLE_KEY},
                    json={"system_instruction": {"parts": [{"text": SYSTEM}]},
                          "contents": [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in messages],
                          "generationConfig": {"temperature": .65, "maxOutputTokens": 2048}},
                )
                if response.is_success:
                    candidates = response.json().get("candidates", [])
                    if candidates and candidates[0].get("finishReason") == "STOP":
                        reply = "\n".join(p.get("text", "") for p in candidates[0].get("content", {}).get("parts", []) if not p.get("thought")).strip()
                        if coaching_matches_language(reply, "hi"):
                            return {"reply": reply, "provider": "Gemini"}
            except (httpx.HTTPError, ValueError, TypeError, KeyError):
                pass
        if settings.GROQ_API_KEY:
            try:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={"model": settings.VOICE_GROQ_MODEL,
                          "messages": [{"role": "system", "content": SYSTEM}, *messages],
                          "temperature": .65, "max_tokens": 2048},
                )
                if response.is_success:
                    choices = response.json().get("choices", [])
                    if choices and choices[0].get("finish_reason") == "stop":
                        reply = (choices[0].get("message", {}).get("content") or "").strip()
                        if coaching_matches_language(reply, "hi"):
                            return {"reply": reply, "provider": "Groq"}
            except (httpx.HTTPError, ValueError, TypeError, KeyError):
                pass
    raise RuntimeError("The conversation service is unavailable. Please try again, or switch to guided practice.")
