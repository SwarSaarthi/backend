"""Language rules shared by score summaries and generated coaching."""
import re


def feedback_summary(analysis: dict, language: str) -> str:
    if language == "en":
        return analysis["feedback"]
    if not analysis.get("prediction"):
        return "आवाज़ पहचानी नहीं गई। कृपया माइक के पास स्पष्ट बोलें और फिर से रिकॉर्ड करें।"
    if analysis["is_correct"]:
        return "बहुत अच्छा! आपका उच्चारण सही है।"
    if analysis["accuracy_score"] >= 50:
        return "अच्छा प्रयास! सही उच्चारण का ऑडियो ध्यान से सुनें और फिर कोशिश करें।"
    return "उच्चारण में सुधार की गुंजाइश है। सही उच्चारण का ऑडियो सुनें और धीरे-धीरे बोलकर अभ्यास करें।"


def coaching_matches_language(text: str, language: str) -> bool:
    if not text.strip():
        return False
    if language == "hi":
        # Do not pass English/Hinglish coaching to the Hindi voice.
        return bool(re.search(r"[\u0900-\u097f]", text)) and not re.search(r"[A-Za-z]", text)
    return bool(re.search(r"[A-Za-z]", text))
