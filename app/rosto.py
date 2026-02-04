import numpy as np
from insightface.app import FaceAnalysis

_APLICACAO = None

def obter_app():
    global _APLICACAO
    if _APLICACAO is None:
        _APLICACAO = FaceAnalysis(name="buffalo_l")
        _APLICACAO.prepare(ctx_id=-1, det_size=(320, 320))
    return _APLICACAO

def bytes_imagem_para_rgb_np(bytes_imagem) -> np.ndarray:
    from PIL import Image
    import io
    imagem = Image.open(io.BytesIO(bytes_imagem)).convert("RGB")
    return np.array(imagem)

def obter_embedding(rgb_np: np.ndarray) -> np.ndarray:
    app = obter_app()
    rostos = app.get(rgb_np)
    if not rostos:
        raise ValueError("Nenhum rosto detectado na imagem.")

    # maior rosto detectado
    rostos = sorted(
        rostos,
        key=lambda r: (r.bbox[2]-r.bbox[0]) * (r.bbox[3]-r.bbox[1]),
        reverse=True
    )
    emb = rostos[0].embedding.astype(np.float32)
    emb = emb / (np.linalg.norm(emb) + 1e-9)
    return emb

def similaridade_cosseno(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))

def gerar_template_medio(embeddings: list[np.ndarray]) -> np.ndarray:
    medio = np.mean(np.stack(embeddings, axis=0), axis=0).astype(np.float32)
    medio = medio / (np.linalg.norm(medio) + 1e-9)
    return medio
