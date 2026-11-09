"""
SwarSaarthi — Gemini AI Pronunciation Coaching Service

Uses Google Gemini API (gemini-3.5-flash) to provide expert-level
articulation and speech-therapy coaching tailored for speech-impaired learners.

Supports user-selected feedback language:
- 'hi' (Hindi): Instructions provided in natural Hindi with Devanagari phonetics
- 'en' (English): Instructions provided in simple English with highlighted Devanagari phonemes

Includes an intelligent clinical fallback for offline/low-connectivity environments.
"""

import logging
import re
from typing import Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ── Supported Models (in priority order) ─────────────────────
GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-flash-latest",
]

# ── Clinical Hindi Articulation Map (for Fallback Coaching) ──
HINDI_ARTICULATION_GUIDE_EN: dict[str, dict[str, str]] = {
    "त": {"place": "Dental (दंत्य)", "tongue": "Touch the tip of your tongue flat against the back of your upper front teeth."},
    "थ": {"place": "Dental Aspirated", "tongue": "Touch your tongue against upper front teeth, then release with a strong puff of air."},
    "द": {"place": "Dental Voiced", "tongue": "Vibrate vocal cords while touching tongue to the back of upper front teeth."},
    "ध": {"place": "Dental Voiced Aspirated", "tongue": "Vibrate vocal cords and release air with tongue against upper front teeth."},
    "ट": {"place": "Retroflex (मूर्धन्य)", "tongue": "Curl the tip of your tongue backwards to touch the hard roof (palate) of your mouth, then snap it down."},
    "ठ": {"place": "Retroflex Aspirated", "tongue": "Curl tongue back against the roof of mouth and release with a burst of air."},
    "ड": {"place": "Retroflex Voiced", "tongue": "Curl tongue tip to touch the roof of mouth with vocal cord vibration."},
    "ढ": {"place": "Retroflex Voiced Aspirated", "tongue": "Curl tongue to palate, vibrate vocal cords and release strong air."},
    "स": {"place": "Alveolar Sibilant", "tongue": "Keep tongue tip close behind upper front teeth without touching; gently hiss air forward."},
    "श": {"place": "Palatal Sibilant", "tongue": "Flatten middle of tongue against hard palate; round lips slightly and push air ('shh')."},
    "ष": {"place": "Retroflex Sibilant", "tongue": "Curl tongue tip slightly backward toward the roof while exhaling."},
    "क": {"place": "Velar (कंठ्य)", "tongue": "Raise the back of your tongue against your soft palate (back of mouth) and release."},
    "ख": {"place": "Velar Aspirated", "tongue": "Raise back of tongue to soft palate and release with an energetic puff of air."},
    "ग": {"place": "Velar Voiced", "tongue": "Vibrate vocal cords while pressing back of tongue against soft palate."},
    "घ": {"place": "Velar Voiced Aspirated", "tongue": "Deep throat sound; vibrate vocal cords and push air forcefully."},
    "प": {"place": "Bilabial (ओष्ठ्य)", "tongue": "Press both lips firmly together, build air pressure, and pop lips open."},
    "फ": {"place": "Bilabial Aspirated", "tongue": "Press both lips together and blow open with a strong puff of air."},
    "ब": {"place": "Bilabial Voiced", "tongue": "Press lips together and vibrate your vocal cords as you release."},
    "भ": {"place": "Bilabial Voiced Aspirated", "tongue": "Vibrate vocal cords and burst lips open with breath."},
    "म": {"place": "Bilabial Nasal", "tongue": "Keep lips closed and direct air humming through your nose."},
    "र": {"place": "Alveolar Tap", "tongue": "Lightly tap the tip of your tongue once against the gum ridge behind upper teeth."},
    "ल": {"place": "Lateral Approximant", "tongue": "Press tongue tip behind upper front teeth and let air flow freely around the sides."},
    "व": {"place": "Labiodental", "tongue": "Gently touch upper front teeth to inside of lower lip without biting; exhale smoothly."},
    "ह": {"place": "Glottal", "tongue": "Keep mouth relaxed open; exhale warm air directly from your throat/chest."},
}

HINDI_ARTICULATION_GUIDE_HI: dict[str, dict[str, str]] = {
    "त": {"place": "दंत्य वर्ण", "tongue": "जीभ की नोक को ऊपर के सामने वाले दांतों के पिछले हिस्से पर लगाएं और धीरे से हटाएं।"},
    "थ": {"place": "दंत्य महाप्राण", "tongue": "जीभ को ऊपर के दांतों से सटाएं और हवा का एक हल्का झोंका छोड़ते हुए बोलें।"},
    "द": {"place": "दंत्य घोष", "tongue": "गले में कंपन करते हुए जीभ को सामने के दांतों के पीछे स्पर्श कराएं।"},
    "ध": {"place": "दंत्य महाप्राण घोष", "tongue": "गले में कंपन के साथ जीभ को दांतों से सटाकर सांस का प्रवाह छोड़ें।"},
    "ट": {"place": "मूर्धन्य वर्ण", "tongue": "जीभ की नोक को पीछे की ओर मोड़कर तालू (छत) से स्पर्श करें, फिर झटके से नीचे लाएं।"},
    "ठ": {"place": "मूर्धन्य महाप्राण", "tongue": "जीभ को तालू से मोड़कर स्पर्श करें और हवा के झोंके के साथ उच्चारण करें।"},
    "ड": {"place": "मूर्धन्य घोष", "tongue": "जीभ को तालू से मोड़ें और स्वर-तंत्री में कंपन करते हुए बोलें।"},
    "ढ": {"place": "मूर्धन्य महाप्राण", "tongue": "जीभ को तालू से मुड़ी अवस्था में रखते हुए गहरी सांस के साथ बोलें।"},
    "स": {"place": "दंतमूल दंती 'स'", "tongue": "जीभ को दांतों के बिल्कुल पास रखें (बिना छुए) और 'सस्स्' की सीटी जैसी हवा निकालें।"},
    "श": {"place": "तालव्य 'श'", "tongue": "जीभ के बीच के भाग को तालू से सटाएं, होंठों को हल्का गोल करें और 'श' की हवा निकालें।"},
    "ष": {"place": "मूर्धन्य 'ष'", "tongue": "जीभ की नोक को हल्का पीछे मोड़कर हवा को बाहर की ओर निकालें।"},
    "क": {"place": "कंठ्य वर्ण", "tongue": "जीभ के पिछले भाग को गले के तालू से सटाकर झटके से छोड़ें।"},
    "ख": {"place": "कंठ्य महाप्राण", "tongue": "गले से जीभ के पिछले हिस्से को छूकर हवा का तीव्र झोंका बाहर निकालें।"},
    "ग": {"place": "कंठ्य घोष", "tongue": "गले में कंपन करते हुए जीभ के पिछले हिस्से से उच्चारण करें।"},
    "घ": {"place": "कंठ्य महाप्राण घोष", "tongue": "गले से गहरी गूंज और सांस के दबाव के साथ उच्चारण करें।"},
    "प": {"place": "ओष्ठ्य वर्ण", "tongue": "दोनों होंठों को आपस में कसकर मिलाएं, हवा का दबाव बनाएं और होंठ खोलें।"},
    "फ": {"place": "ओष्ठ्य महाप्राण", "tongue": "दोनों होंठों को मिलाकर हवा के तेज झोंके के साथ खोलें (अंग्रेजी F की तरह दांत न लगाएं)।"},
    "ब": {"place": "ओष्ठ्य घोष", "tongue": "दोनों होंठों को मिलाकर गले में कंपन करते हुए खोलें।"},
    "भ": {"place": "ओष्ठ्य महाप्राण घोष", "tongue": "होंठों को मिलाकर गहरी सांस और कंपन के साथ खोलें।"},
    "म": {"place": "ओष्ठ्य अनुनासिक", "tongue": "होंठ बंद रखें और आवाज को नाक से गूंजते हुए निकालें।"},
    "र": {"place": "लुंठित वर्ण", "tongue": "जीभ की नोक को दांतों के ठीक पीछे मसूड़े पर हल्का सा कंपन कराएं।"},
    "ल": {"place": "पार्श्विक वर्ण", "tongue": "जीभ की नोक को ऊपर के दांतों के पीछे रखें और हवा को दोनों तरफ से निकलने दें।"},
    "व": {"place": "दंतोष्ठ्य वर्ण", "tongue": "ऊपर के दांतों को नीचे के होंठ से हल्का स्पर्श कराएं और सांस छोड़ें।"},
    "ह": {"place": "काकल्य वर्ण", "tongue": "मुंह को सामान्य खुला रखें और सीधे गले/छाती से गर्म हवा छोड़ें।"},
}

SYSTEM_INSTRUCTION_EN = """You are **SwarSaarthi AI Speech Coach** — an expert speech-language pathologist specializing in Hindi articulation therapy for speech-impaired individuals (dysarthria, stuttering, apraxia, and language learners).

Your goal is to provide warm, encouraging, clinically precise feedback comparing the learner's spoken attempt against the target word.

Format your response cleanly with these three sections in simple English:

🎯 **Analysis**
A concise 1-2 sentence comparison. Identify the specific phonemes, matras, or conjuncts that were mispronounced, omitted, or substituted.

👅 **Tongue & Mouth Placement**
Provide clear, step-by-step physical positioning instructions for the target sounds:
- Tongue position (e.g., dental against front teeth vs retroflex curled to palate)
- Lip shape (rounded, spread, closed)
- Airflow control (aspirated puff vs smooth breathing)

💡 **Practice Tip**
Give 1 or 2 concrete exercises (e.g. syllable breakdown, minimal pair drill, or mirror practice) to master this sound.

Guidelines:
- Keep the total response under 120 words.
- Write in simple English with Hindi letters highlighted in bold Devanagari (e.g., **'स'**, **'त'**).
- If pronunciation was excellent (score >= 85%), celebrate their success and offer a tip for natural fluency.
"""

SYSTEM_INSTRUCTION_HI = """आप **स्वर-सारथी एआई वाक्-कोच (Speech Coach)** हैं — एक विशेषज्ञ स्पीच-थेरेपिस्ट (Speech-Language Pathologist) जो वाणी दोष (dysarthria, हकलाहट, स्पष्ट उच्चारण की समस्या) वाले शिक्षार्थियों को हिंदी उच्चारण सुधारने में प्रशिक्षित करते हैं।

आपका कार्य शिक्षार्थी के बोले गए शब्द की सही शब्द से तुलना करके सरल, उत्साहवर्धक और चिकित्सकीय रूप से सटीक मार्गदर्शन देना है।

अपनी प्रतिक्रिया को इन तीन अनुभागों में व्यवस्थित करें:

🎯 **विश्लेषण (Analysis)**
1-2 सरल वाक्यों में बताएं कि शिक्षार्थी ने क्या बोला और क्या छूटा या बदला (जैसे अल्पप्राण/महाप्राण या मात्रा की त्रुटि)।

👅 **जीभ और मुख की सही स्थिति (Tongue & Mouth Placement)**
सही उच्चारण के लिए भौतिक स्थिति के स्पष्ट निर्देश दें:
- जीभ की स्थिति (जैसे दंत्य: ऊपरी दांतों के पीछे, या मूर्धन्य: तालू से मुड़ी हुई)
- होंठों का आकार (गोल, खुले, या बंद)
- वायु-प्रवाह (हवा का हल्का झोंका या निरंतर सांस)

💡 **अभ्यास युक्ति (Practice Tip)**
1 या 2 व्यावहारिक अभ्यास दें (जैसे शब्द को अक्षरों में तोड़ना या आईने के सामने दोहराना)।

दिशानिर्देश:
- पूरी प्रतिक्रिया शुद्ध, सरल और मधुर **हिंदी (देवनागरी लिपि)** में होनी चाहिए।
- कुल प्रतिक्रिया 120 शब्दों के अंदर रखें।
- अत्यंत उत्साहवर्धक और धैर्यवान रहें।
- यदि उच्चारण उत्कृष्ट हो (स्कोर >= 85%), तो प्रशंसा करें और धाराप्रवाह बोलने की युक्ति दें।
"""


def _generate_rule_based_fallback(
    target_text: str,
    user_spoken_text: str,
    accuracy_score: float,
    cer: float,
    transliteration: str = "",
    feedback_language: str = "en",
) -> str:
    """
    Intelligent clinical fallback when Gemini API is unavailable or offline.
    Inspects Devanagari characters to provide accurate articulation instructions.
    """
    is_hindi = feedback_language == "hi"

    # Detect mispronounced or missing characters
    target_chars = set(target_text)
    spoken_chars = set(user_spoken_text) if user_spoken_text else set()
    guide_map = HINDI_ARTICULATION_GUIDE_HI if is_hindi else HINDI_ARTICULATION_GUIDE_EN
    missing_chars = [ch for ch in target_text if ch not in spoken_chars and ch in guide_map]

    focused_char = missing_chars[0] if missing_chars else None
    if not focused_char:
        for ch in target_text:
            if ch in guide_map:
                focused_char = ch
                break

    guide = guide_map.get(focused_char, {}) if focused_char else {}

    if is_hindi:
        if accuracy_score >= 85.0:
            return (
                f"🎯 **विश्लेषण**: बहुत बढ़िया! आपने **{target_text}** का उच्चारण बहुत स्पष्ट और सटीक रूप से किया ({accuracy_score:.0f}%)।\n\n"
                f"👅 **मुख की स्थिति**: आपकी जीभ और होंठों का तालमेल बिल्कुल सही था। सांस का प्रवाह सहज बनाए रखें।\n\n"
                f"💡 **अभ्यास युक्ति**: **{target_text}** को पूरे वाक्य में 3 बार दोहराकर अभ्यास करें!"
            )
        place = guide.get("place", "उच्चारण स्थान")
        tongue = guide.get("tongue", "हवा का प्रवाह संतुलित रखें और जीभ को स्थिर रखें।")
        spoken_display = f"'{user_spoken_text}'" if user_spoken_text else "मौन / अस्पष्ट"
        return (
            f"🎯 **विश्लेषण**: आपकी सटीकता {accuracy_score:.0f}% रही। लक्ष्य शब्द **'{target_text}'** के लिए हमें {spoken_display} सुनाई दिया।\n\n"
            f"👅 **'{focused_char or target_text}' के लिए जीभ की स्थिति** ({place}):\n"
            f"{tongue}\n\n"
            f"💡 **अभ्यास युक्ति**: शब्द को धीरे-धीरे अलग-अलग अक्षरों में बोलें, फिर एक साथ मिलाकर **{target_text}** का अभ्यास करें।"
        )
    else:
        if accuracy_score >= 85.0:
            return (
                f"🎯 **Analysis**: Excellent pronunciation! You pronounced **{target_text}** clearly with great accuracy ({accuracy_score:.0f}%).\n\n"
                f"👅 **Mouth Placement**: Your tongue and lip coordination were accurate. Maintain relaxed jaw movement and natural airflow.\n\n"
                f"💡 **Practice Tip**: Try repeating **{target_text}** 3 times in a full sentence to practice conversational rhythm!"
            )
        place = guide.get("place", "articulation point")
        tongue = guide.get("tongue", "Focus on releasing air steadily while keeping your tongue steady.")
        spoken_display = f"'{user_spoken_text}'" if user_spoken_text else "silence"
        return (
            f"🎯 **Analysis**: You scored {accuracy_score:.0f}%. We heard {spoken_display} for the target **'{target_text}'**.\n\n"
            f"👅 **Tongue Placement for '{focused_char or target_text}'** ({place}):\n"
            f"{tongue}\n\n"
            f"💡 **Practice Tip**: Break the word down slowly: say each syllable separately, then blend them together into **{target_text}**."
        )


async def generate_pronunciation_feedback(
    target_text: str,
    user_spoken_text: str,
    accuracy_score: float,
    cer: float,
    transliteration: str = "",
    feedback_language: str = "en",
) -> str:
    """
    Generate speech-therapy coaching feedback via Google Gemini API in user's chosen language.
    Gracefully falls back to clinical rule-based feedback if network/API fails.
    """
    api_key = settings.SWAR_GOOGLE_KEY or ""
    feedback_lang = "hi" if feedback_language.lower().startswith("hi") else "en"

    if not api_key:
        logger.info("No SWAR_GOOGLE_KEY configured; using clinical fallback.")
        return _generate_rule_based_fallback(
            target_text, user_spoken_text, accuracy_score, cer, transliteration, feedback_lang
        )

    system_instruction = SYSTEM_INSTRUCTION_HI if feedback_lang == "hi" else SYSTEM_INSTRUCTION_EN

    if feedback_lang == "hi":
        user_prompt = (
            f"लक्ष्य हिंदी शब्द: {target_text} (ट्रांसलिट्रेशन: {transliteration})\n"
            f"शिक्षार्थी द्वारा बोला गया: {user_spoken_text if user_spoken_text else '(कोई आवाज नहीं सुनी गई)'}\n"
            f"सटीकता स्कोर: {accuracy_score:.1f}%\n"
            f"वर्ण त्रुटि दर (CER): {cer:.3f}\n"
            f"कृपया पूरी प्रतिक्रिया शुद्ध और सरल हिंदी में दें।"
        )
    else:
        user_prompt = (
            f"Target Hindi Word: {target_text} ({transliteration})\n"
            f"Learner Spoke: {user_spoken_text if user_spoken_text else '(no audible speech detected)'}\n"
            f"Accuracy: {accuracy_score:.1f}%\n"
            f"Character Error Rate (CER): {cer:.3f}\n"
            f"Please provide the full feedback in clear, simple English."
        )

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}],
        },
        "contents": [
            {"parts": [{"text": user_prompt}]},
        ],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 450,
        },
    }

    # Try supported models
    timeout = httpx.Timeout(connect=6.0, read=16.0, write=6.0, pool=6.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for model in GEMINI_MODELS:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                res = await client.post(endpoint, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            feedback = parts[0]["text"].strip()
                            logger.info(
                                "Gemini feedback generated using model '%s' in language '%s' for '%s'",
                                model, feedback_lang, target_text
                            )
                            return feedback
                else:
                    logger.warning(
                        "Gemini model '%s' returned status %d: %s",
                        model, res.status_code, res.text[:120]
                    )
            except Exception as e:
                logger.warning("Gemini model '%s' attempt failed: %s", model, e)

    # Fallback
    logger.info("Using clinical fallback for '%s' in language '%s'", target_text, feedback_lang)
    return _generate_rule_based_fallback(
        target_text, user_spoken_text, accuracy_score, cer, transliteration, feedback_lang
    )
