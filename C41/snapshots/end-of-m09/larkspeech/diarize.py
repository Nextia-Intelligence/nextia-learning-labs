"""Who spoke when: split by channel, or cluster speaker embeddings; and the diarization error rate."""
import itertools

import numpy as np

from larkspeech import vad as V
from larkspeech.models import path as model_path

STEP = 0.01


def by_channel(stereo, sr, speakers=("agent", "caller"), threshold=0.5, louder_wins=True):
    """Stereo calls: each side has its own channel, so each channel's speech is one speaker.
    Background talk on the caller's side can look like speech while the agent talks: with louder_wins, a 10 ms
    frame that both channels call speech goes to the louder channel."""
    n = int(len(stereo) / sr / STEP) + 1
    active = np.zeros((2, n), bool)
    for ch in range(2):
        for s, e in V.silero(stereo[:, ch], sr, threshold=threshold):
            active[ch, int(s / STEP):int(e / STEP)] = True
    if louder_wins:
        hop = int(sr * STEP)
        k = min(n, len(stereo) // hop)
        energy = (stereo[: k * hop].reshape(k, hop, 2) ** 2).mean(axis=1).T
        both = active[0, :k] & active[1, :k]
        active[1, :k][both & (energy[0] > energy[1])] = False
        active[0, :k][both & (energy[1] >= energy[0])] = False
    turns = []
    for ch, name in enumerate(speakers):
        start = None
        for i, a in enumerate(list(active[ch]) + [False]):
            if a and start is None:
                start = i
            elif not a and start is not None:
                if (i - start) * STEP >= 0.1:
                    turns.append((start * STEP, i * STEP, name))
                start = None
    return sorted(turns)


_extractor = None


def extractor():
    global _extractor
    if _extractor is None:
        import sherpa_onnx
        cfg = sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=str(model_path("spk/wespeaker_en_voxceleb_resnet34_LM.onnx")), num_threads=2)
        _extractor = sherpa_onnx.SpeakerEmbeddingExtractor(cfg)
    return _extractor


def embed(x, sr=16000):
    ex = extractor()
    s = ex.create_stream()
    s.accept_waveform(sr, x)
    s.input_finished()
    e = np.array(ex.compute(s))
    return e / (np.linalg.norm(e) + 1e-9)


def by_embeddings(x, sr=16000, window=1.5, hop=0.75, n_speakers=2, threshold=None):
    """Mono calls: speech pieces -> speaker embeddings -> two clusters. The cluster that speaks first is the
    agent (Larkfield's agents answer the call). threshold= (a cosine distance) lets the clustering choose how many
    speakers there are instead."""
    from sklearn.cluster import AgglomerativeClustering
    pieces = []
    for s, e in V.silero(x, sr):
        t = s
        while t < e - 0.4:
            u = min(t + window, e)
            pieces.append((t, u))
            t += hop
    if len(pieces) < 2:
        return [(s, e, "agent") for s, e in pieces]
    embs = np.stack([embed(x[int(s * sr):int(e * sr)], sr) for s, e in pieces])
    cl = AgglomerativeClustering(n_clusters=None if threshold else n_speakers, distance_threshold=threshold,
                                 metric="cosine", linkage="average").fit(embs)
    first = cl.labels_[0]
    names = {first: "agent"}
    for lab in cl.labels_:
        names.setdefault(lab, "caller" if "caller" not in names.values() else f"speaker{len(names) + 1}")
    # each 10 ms frame takes the label of the piece whose centre is nearest
    frames = {}
    for (s, e), lab in zip(pieces, cl.labels_):
        c = (s + e) / 2
        for k in range(int(s / STEP), int(e / STEP)):
            if k not in frames or abs(k * STEP - c) < frames[k][1]:
                frames[k] = (names[lab], abs(k * STEP - c))
    turns, cur = [], None
    for k in sorted(frames):
        name = frames[k][0]
        if cur and cur[2] == name and k * STEP - cur[1] <= STEP * 1.5:
            cur[1] = (k + 1) * STEP
        else:
            if cur:
                turns.append(tuple(cur))
            cur = [k * STEP, (k + 1) * STEP, name]
    if cur:
        turns.append(tuple(cur))
    return turns


def der(pred, truth, seconds, collar=0.25):
    """Diarization error rate = (missed speech + false speech + speaker confusion) / true speech time.
    Speaker names are matched in the best way first. A collar around each true boundary is not scored."""
    n = int(seconds / STEP) + 1
    tnames = sorted({t[2] for t in truth})
    pnames = sorted({p[2] for p in pred})

    def masks(turns, names):
        m = np.zeros((len(names), n), bool)
        for s, e, w in turns:
            m[names.index(w), int(s / STEP):int(e / STEP)] = True
        return m

    T, P = masks(truth, tnames), masks(pred, pnames)
    score = np.ones(n, bool)
    for s, e, _ in truth:
        for b in (s, e):
            score[max(0, int((b - collar) / STEP)):int((b + collar) / STEP)] = False
    ref_speech = T.any(0) & score
    best = None
    for perm in itertools.permutations(range(max(len(pnames), len(tnames))), len(pnames)):
        conf = 0
        for pi, ti in enumerate(perm):
            if ti < len(tnames):
                conf += int((P[pi] & ~T[ti] & T.any(0) & score).sum())
            else:
                conf += int((P[pi] & T.any(0) & score).sum())
        if best is None or conf < best:
            best = conf
    missed = int((T.any(0) & ~P.any(0) & score).sum())
    false = int((P.any(0) & ~T.any(0) & score).sum())
    total = max(int(ref_speech.sum()), 1)
    return {"der": (missed + false + best) / total, "missed": missed / total, "false": false / total,
            "confusion": best / total}


def speaker_at(turns, t, reach=0.5):
    """The speaker of the turn that holds time t (the middle of a word). A word in a short gap between turns goes
    to the nearest turn within `reach` seconds; further away, "?" (nobody was found speaking there)."""
    for s, e, w in turns:
        if s <= t <= e:
            return w
    near = [(min(abs(t - s), abs(t - e)), w) for s, e, w in turns]
    best = min(near, default=(reach + 1, "?"))
    return best[1] if best[0] <= reach else "?"


def truth_turns(call):
    """The true turns from the labels, from the first word to the last word of each turn."""
    out = []
    for t in call["turns"]:
        if t.get("words"):
            out.append((t["words"][0]["start"], t["words"][-1]["end"], t["speaker"]))
        else:
            out.append((t["start"], t["end"], t["speaker"]))
    return out
