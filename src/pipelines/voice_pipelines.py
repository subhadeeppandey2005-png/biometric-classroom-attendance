import io
import json
import librosa
import numpy as np
import streamlit as st
from resemblyzer import VoiceEncoder, preprocess_wav


@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()


def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        wav = preprocess_wav(audio)
        embedding = encoder.embed_utterance(wav)
        return embedding.tolist()
    except Exception as e:
        st.error(f"Voice recognition error: {e}")
        return None


def identify_speaker(new_embedding, candidates_dict, threshold=0.55):
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    v1 = np.array(new_embedding, dtype=np.float32).flatten()
    norm1 = np.linalg.norm(v1)
    if norm1 == 0:
        return None, 0.0

    best_sid = None
    best_score = -1.0

    for sid, stored_embedding in candidates_dict.items():
        if not stored_embedding:
            continue

        try:
            if isinstance(stored_embedding, str):
                stored_embedding = json.loads(stored_embedding)

            v2 = np.array(stored_embedding, dtype=np.float32).flatten()
            norm2 = np.linalg.norm(v2)

            if norm2 > 0:
                similarity = float(np.dot(v1, v2) / (norm1 * norm2))
                if similarity > best_score:
                    best_score = similarity
                    best_sid = sid
        except Exception:
            continue

    if best_score >= threshold:
        return best_sid, best_score

    return None, best_score


def process_bulk_audio(audio_bytes, candidates_dict, threshold=0.55):
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)

        # Fallback to entire clip if too short
        if len(audio) < sr * 0.5:
            wav = preprocess_wav(audio)
            emb = encoder.embed_utterance(wav)
            sid, score = identify_speaker(emb, candidates_dict, threshold)
            return {str(sid): score} if sid is not None else {}

        # Split audio into speech segments
        segments = librosa.effects.split(audio, top_db=25)
        identified_results = {}

        # If silence splitter detects no chunks, process whole recording
        if len(segments) == 0:
            segments = [(0, len(audio))]

        for start, end in segments:
            if (end - start) < sr * 0.4:
                continue

            segment_audio = audio[start:end]
            wav = preprocess_wav(segment_audio)
            embedding = encoder.embed_utterance(wav)

            sid, score = identify_speaker(embedding, candidates_dict, threshold)

            if sid is not None:
                sid_str = str(sid)
                if sid_str not in identified_results or score > identified_results[sid_str]:
                    identified_results[sid_str] = round(float(score), 3)

        # If segmentation didn't pick up a candidate, run one full pass over the entire clip
        if not identified_results:
            wav = preprocess_wav(audio)
            embedding = encoder.embed_utterance(wav)
            sid, score = identify_speaker(embedding, candidates_dict, threshold)
            if sid is not None:
                identified_results[str(sid)] = round(float(score), 3)

        return identified_results

    except Exception as e:
        st.error(f"Bulk process error: {e}")
        return {}