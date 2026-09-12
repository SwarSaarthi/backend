"""
SwarSaarthi — ASR Service (IndicWav2Vec Hindi)

Loads the ai4bharat/indicwav2vec-hindi model at startup and provides:

    - load_model()
    - is_model_loaded()
    - predict_audio(audio_path)
    - analyze_pronunciation(target, prediction)

Pipeline:

    Browser Audio
         ↓
    FFmpeg conversion
         ↓
    16 kHz Mono WAV
         ↓
    IndicWav2Vec
         ↓
    Hindi Text Prediction
         ↓
    Target vs Prediction
         ↓
    CER + Accuracy + Feedback
"""

import os
import logging
import tempfile
import subprocess
from typing import Optional

import torch
import torchaudio

from transformers import (
    AutoProcessor,
    AutoModelForCTC
)

from jiwer import cer as compute_cer


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Model Configuration
# ---------------------------------------------------------

MODEL_ID = "ai4bharat/indicwav2vec-hindi"

TARGET_SAMPLE_RATE = 16_000


# ---------------------------------------------------------
# Singleton Model State
# ---------------------------------------------------------

_processor: Optional[AutoProcessor] = None
_model: Optional[AutoModelForCTC] = None
_device: Optional[torch.device] = None

_model_loaded = False


# =========================================================
# MODEL LIFECYCLE
# =========================================================

def load_model() -> None:
    """
    Load the IndicWav2Vec Hindi model.

    The model is loaded only once and kept in memory so that
    every prediction request can reuse the same model.
    """

    global _processor
    global _model
    global _device
    global _model_loaded

    # -----------------------------------------------------
    # Prevent loading twice
    # -----------------------------------------------------

    if _model_loaded:

        logger.info(
            "ASR model already loaded — skipping."
        )

        return

    # -----------------------------------------------------
    # Select device
    # -----------------------------------------------------

    _device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    logger.info(
        "ASR device: %s",
        _device
    )

    # -----------------------------------------------------
    # Hugging Face authentication
    # -----------------------------------------------------
    #
    # If HF_TOKEN exists in the environment, it will be used.
    #
    # Otherwise Hugging Face's locally saved login can be used.
    #
    # You can authenticate with:
    #
    #     hf auth login
    #
    # -----------------------------------------------------

    hf_token = os.getenv("HF_TOKEN")

    if hf_token:

        logger.info(
            "Using HF_TOKEN for Hugging Face authentication."
        )

    else:

        logger.info(
            "No HF_TOKEN found. Using Hugging Face cached authentication."
        )

    # -----------------------------------------------------
    # Load processor
    # -----------------------------------------------------

    logger.info(
        "Loading processor from %s ...",
        MODEL_ID
    )

    if hf_token:

        _processor = AutoProcessor.from_pretrained(
            MODEL_ID,
            token=hf_token
        )

    else:

        _processor = AutoProcessor.from_pretrained(
            MODEL_ID
        )

    # -----------------------------------------------------
    # Load model
    # -----------------------------------------------------

    logger.info(
        "Loading IndicWav2Vec model from %s ...",
        MODEL_ID
    )

    if hf_token:

        _model = AutoModelForCTC.from_pretrained(
            MODEL_ID,
            token=hf_token
        )

    else:

        _model = AutoModelForCTC.from_pretrained(
            MODEL_ID
        )

    # -----------------------------------------------------
    # Move model to CPU / GPU
    # -----------------------------------------------------

    _model.to(_device)

    # -----------------------------------------------------
    # Evaluation mode
    # -----------------------------------------------------

    _model.eval()

    _model_loaded = True

    logger.info(
        "ASR model loaded successfully on %s",
        _device
    )


# =========================================================
# MODEL STATUS
# =========================================================

def is_model_loaded() -> bool:
    """
    Check whether the ASR model has been loaded.
    """

    return _model_loaded


# =========================================================
# AUDIO CONVERSION
# =========================================================

def convert_to_wav(input_path: str) -> str:
    """
    Convert browser audio (WebM/Opus, OGG, WAV, etc.)
    into a 16 kHz mono WAV using PyAV.

    No system FFmpeg installation required.
    """

    import av
    import soundfile as sf
    import numpy as np

    wav_path = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    ).name

    try:
        container = av.open(input_path)

        audio_stream = container.streams.audio[0]

        resampler = av.audio.resampler.AudioResampler(
            format="s16",
            layout="mono",
            rate=TARGET_SAMPLE_RATE
        )

        samples = []

        for frame in container.decode(audio_stream):

            frames = resampler.resample(frame)

            if not isinstance(frames, list):
                frames = [frames]

            for resampled_frame in frames:

                array = resampled_frame.to_ndarray()

                samples.append(array)

        container.close()

        if not samples:
            raise RuntimeError(
                "No audio samples found in uploaded file."
            )

        audio = np.concatenate(
            samples,
            axis=1
        )

        # Mono
        audio = audio[0]

        # int16 → float32
        audio = audio.astype(np.float32) / 32768.0

        sf.write(
            wav_path,
            audio,
            TARGET_SAMPLE_RATE
        )

        return wav_path

    except Exception as e:

        if os.path.exists(wav_path):
            os.remove(wav_path)

        raise RuntimeError(
            f"Audio conversion failed: {e}"
        )

# =========================================================
# ASR PREDICTION
# =========================================================

def predict_audio(audio_path: str) -> str:
    """
    Run IndicWav2Vec inference and return Hindi text.

    Uses direct CTC greedy decoding from model logits.
    We intentionally do NOT use processor.batch_decode()
    because this model's processor contains a pyctcdecode
    language-model decoder with a vocabulary mismatch.
    """

    if (
        not _model_loaded
        or _processor is None
        or _model is None
        or _device is None
    ):
        raise RuntimeError(
            "ASR model not loaded. Call load_model() first."
        )

    converted_path = convert_to_wav(audio_path)

    try:

        # -------------------------------------------------
        # Load WAV using soundfile
        # -------------------------------------------------

        import soundfile as sf

        data, sample_rate = sf.read(
            converted_path
        )

        logger.info(
            "Audio loaded: sample_rate=%s, shape=%s",
            sample_rate,
            getattr(data, "shape", None)
        )

        # -------------------------------------------------
        # Stereo -> mono
        # -------------------------------------------------

        if data.ndim == 2:
            data = data.mean(axis=1)

        # -------------------------------------------------
        # NumPy -> Torch
        # -------------------------------------------------

        waveform = torch.from_numpy(
            data
        ).float()

        # -------------------------------------------------
        # Resample -> 16 kHz
        # -------------------------------------------------

        if sample_rate != TARGET_SAMPLE_RATE:

            resampler = torchaudio.transforms.Resample(
                orig_freq=sample_rate,
                new_freq=TARGET_SAMPLE_RATE
            )

            waveform = resampler(
                waveform
            )

        # -------------------------------------------------
        # Tensor -> NumPy
        # -------------------------------------------------

        audio = waveform.squeeze().numpy()

        # -------------------------------------------------
        # Processor
        # -------------------------------------------------

        inputs = _processor(
            audio,
            sampling_rate=TARGET_SAMPLE_RATE,
            return_tensors="pt"
        )

        input_values = inputs.input_values.to(
            _device
        )

        # -------------------------------------------------
        # Model inference
        # -------------------------------------------------

        with torch.no_grad():

            logits = _model(
                input_values
            ).logits

        logger.info(
            "Logits shape: %s",
            logits.shape
        )

        # -------------------------------------------------
        # Direct CTC greedy decoding
        # -------------------------------------------------
        #
        # logits shape:
        #
        #   [batch, time, vocabulary]
        #
        # Example:
        #
        #   [1, 92, 68]
        #
        # argmax over vocabulary dimension
        # -------------------------------------------------

        predicted_ids = torch.argmax(
            logits,
            dim=-1
        )

        # Remove batch dimension
        predicted_ids = predicted_ids[0]

        # -------------------------------------------------
        # Get vocabulary from model
        # -------------------------------------------------

        vocab = _processor.tokenizer.get_vocab()

        # tokenizer vocab is:
        #
        # token -> ID
        #
        # We need:
        #
        # ID -> token
        # -------------------------------------------------

        id_to_token = {
            idx: token
            for token, idx in vocab.items()
        }

        # -------------------------------------------------
        # CTC decoding
        # -------------------------------------------------

        blank_id = _model.config.pad_token_id

        if blank_id is None:
            blank_id = _processor.tokenizer.pad_token_id

        tokens = []

        previous_id = None

        for token_id in predicted_ids.tolist():

            # CTC blank
            if token_id == blank_id:
                previous_id = token_id
                continue

            # CTC removes repeated consecutive tokens
            if token_id == previous_id:
                continue

            token = id_to_token.get(
                token_id,
                ""
            )

            if token:
                tokens.append(token)

            previous_id = token_id

        raw_text = "".join(tokens)

        # Replace '|' (Wav2Vec word boundary) with standard space ' '
        prediction = raw_text.replace("|", " ")

        # Remove special tokens
        for special_token in [
            "<unk>",
            "<pad>",
            "[UNK]",
            "[PAD]"
        ]:
            prediction = prediction.replace(
                special_token,
                ""
            )

        # Collapse spaces and strip leading/trailing whitespace
        prediction = " ".join(prediction.strip().split())

        logger.info(
            "ASR Prediction: %s",
            prediction
        )

        return prediction

    finally:

        if os.path.exists(converted_path):
            os.remove(converted_path)

# =========================================================
# TEXT NORMALIZATION
# =========================================================

def _normalize(text: str) -> str:
    """
    Remove leading/trailing whitespace, replace '|' (word boundary)
    with space, and collapse multiple spaces.
    """
    if not text:
        return ""
    text = text.replace("|", " ")
    return " ".join(
        text.strip().split()
    )


# =========================================================
# PRONUNCIATION ANALYSIS
# =========================================================

def analyze_pronunciation(
    target: str,
    prediction: str
) -> dict:
    """
    Compare expected target word with ASR prediction.

    Uses Character Error Rate (CER).

    Returns:

        {
            "target": ...,
            "prediction": ...,
            "cer": ...,
            "accuracy_score": ...,
            "is_correct": ...,
            "feedback": ...,
            "details": ...
        }
    """

    # -----------------------------------------------------
    # Normalize
    # -----------------------------------------------------

    target = _normalize(
        target
    )

    prediction = _normalize(
        prediction
    )

    # -----------------------------------------------------
    # No speech detected
    # -----------------------------------------------------

    if not prediction:
        return {
            "target": target,
            "prediction": "",
            "cer": 1.0,
            "accuracy_score": 0.0,
            "is_correct": False,
            "feedback_tier": "needs_improvement",
            "feedback": (
                "No speech detected. "
                "Please speak clearly into the microphone and try recording again."
            ),
            "details": {
                "cer_based_score": 0.0
            }
        }

    # =====================================================
    # CER
    # =====================================================

    error_rate = compute_cer(
        target,
        prediction
    )

    # -----------------------------------------------------
    # Convert CER → similarity score
    #
    # CER = 0.0 → 100
    # CER = 0.5 → 50
    # CER = 1.0 → 0
    # -----------------------------------------------------

    accuracy_score = max(
        0.0,
        (1.0 - error_rate) * 100
    )

    accuracy_score = round(
        accuracy_score,
        2
    )

    # -----------------------------------------------------
    # Match evaluation: exact match or 80%+ accuracy
    # -----------------------------------------------------

    is_correct = (
        target == prediction
    ) or (
        accuracy_score >= 80.0
    )

    # =====================================================
    # Feedback Tiers:
    # 1. Excellent: score >= 80% (is_correct)
    # 2. Almost There: 50% <= score < 80%
    # 3. Needs Improvement: score < 50%
    # =====================================================

    if is_correct:
        feedback_tier = "excellent"
        feedback = (
            "Excellent! Your pronunciation is accurate."
        )
    elif accuracy_score >= 50.0:
        feedback_tier = "almost_there"
        feedback = (
            "Good attempt! Listen carefully to the reference audio and try again."
        )
    else:
        feedback_tier = "needs_improvement"
        feedback = (
            "The pronunciation needs improvement. Listen to the reference audio carefully and try speaking slowly."
        )

    # =====================================================
    # Return result
    # =====================================================

    return {
        "target": target,
        "prediction": prediction,
        "cer": round(
            error_rate,
            3
        ),
        "accuracy_score": accuracy_score,
        "is_correct": is_correct,
        "feedback_tier": feedback_tier,
        "feedback": feedback,
        "details": {
            "cer_based_score": accuracy_score
        }
    }