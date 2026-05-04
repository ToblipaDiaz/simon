from faster_whisper import WhisperModel

_model = None

def get_model():
    global _model
    if _model is None:
        # Modelo recomendado para CPU: small + int8
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model

def transcribe_whisper(path: str):
    """
    Devuelve:
    text: str
    segments: list[{start, end, text}]
    """
    model = get_model()

    segments_iter, _info = model.transcribe(
        path,
        language="es",
        vad_filter=True,
        beam_size=5,
        best_of=3,
    )

    segments = []
    full = []
    for s in segments_iter:
        t = (s.text or "").strip()
        if not t:
            continue
        segments.append({"start": float(s.start), "end": float(s.end), "text": t})
        full.append(t)

    return " ".join(full).strip(), segments