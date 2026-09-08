"""
SwarSaarthi — NLP Evaluator Service

Compares target Hindi text against recognized/transcribed text to produce
an accuracy score.  Uses character-level comparison + Levenshtein ratio
via rapidfuzz.

When the IndicWav2Vec ASR model is integrated later, the recognized_text
will come from the model's output.  For now the frontend sends it from
the browser's Web Speech API.
"""

from rapidfuzz import fuzz


# Score at or above this threshold counts as "correct"
CORRECT_THRESHOLD = 70.0


def evaluate_pronunciation(target: str, recognized: str) -> dict:
    """
    Return a dict with:
      - accuracy: 0–100 float
      - is_correct: bool
      - details: sub-scores for transparency
    """
    if not target or not recognized:
        return {
            "accuracy": 0.0,
            "is_correct": False,
            "details": {
                "char_ratio": 0.0,
                "token_sort_ratio": 0.0,
                "partial_ratio": 0.0,
            },
        }

    # Normalise — strip whitespace, lowercase (Devanagari is case-insensitive
    # but transliterations might have mixed case)
    t = target.strip()
    r = recognized.strip()

    # Multiple similarity metrics — weighted blend gives a fairer score
    # for partial matches, reordered tokens, etc.
    char_ratio = fuzz.ratio(t, r)             # strict char-level Levenshtein
    token_sort = fuzz.token_sort_ratio(t, r)  # order-independent token match
    partial = fuzz.partial_ratio(t, r)        # best partial substring match

    # Weighted average (char_ratio matters most for pronunciation)
    accuracy = round(0.50 * char_ratio + 0.30 * token_sort + 0.20 * partial, 2)

    return {
        "accuracy": accuracy,
        "is_correct": accuracy >= CORRECT_THRESHOLD,
        "details": {
            "char_ratio": round(char_ratio, 2),
            "token_sort_ratio": round(token_sort, 2),
            "partial_ratio": round(partial, 2),
        },
    }
