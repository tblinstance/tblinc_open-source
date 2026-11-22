"""1. MiniTransformerLM: Causal Multi-Head Self-Attention Transformer & Instruction Language Model."""

from __future__ import annotations

import ast
import math
import operator
import random
import re
import time
from collections import Counter, defaultdict
from typing import Any

from ..core import (
    BaseAIModel,
    ModelMetadata,
    PredictionResult,
    Tensor,
    TransformerBlock,
    active_compute_backend,
    register_model,
    timed_predict,
)

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "in", "is", "it", "of", "on", "or", "that", "the", "to", "was", "with",
    "what", "how", "why", "who", "when", "where", "can", "you", "tell", "me",
    "about", "please", "explain", "do", "does",
}

DEFAULT_INSTRUCTION_PAIRS: list[dict[str, str]] = [
    {
        "prompt": "hello hi hey greetings good morning good evening",
        "response": "Hello! I am the tblinc AI Transformer engine running locally with 25 built-in AI models (Chat, Diffusion Images, Video Motion, Formant Voice TTS, Polyphonic Music, RAG Search, Vision CNN, and Tabular ML). How can I help you build or generate today?",
    },
    {
        "prompt": "who are you what is tblinc ai model architecture",
        "response": "I am tblinc AI — a self-contained Python AI & MTV/MVC Web Platform. My core engine implements causal Multi-Head Self-Attention Transformers, DDPM Neural Diffusion, BM25 + Cosine RAG, Convolutional Vision networks, and DSP Audio/Music synthesis with zero mandatory external dependencies.",
    },
    {
        "prompt": "how does tblinc generate an admin panel auto crud orm register",
        "response": "The tblinc `AdminSite` automatically inspects registered SQLite ORM models (`app.admin.register(Model)`) and generates a full Light/Dark CRUD Admin Panel at `/admin/` with dynamic `ModelForm` validation, CSRF protection, search, pagination, live AI Studio (`/admin/ai/`), Model Training Center (`/admin/train/`), and API Key & Token Quota management (`/admin/keys/`).",
    },
    {
        "prompt": "how do i train a custom ai model in admin train weights checkpoint",
        "response": "Open `/admin/train/` (or POST to `/api/ai/train`), select any of the 25 AI models, customize the hyperparameters and JSON training dataset, and click Train. Your trained weights are saved to `.tblinc_artifacts/` and automatically loaded by live inference endpoints.",
    },
    {
        "prompt": "how does transformer self attention work q k v multi head",
        "response": "A Transformer projects input token embeddings into Query (Q), Key (K), and Value (V) tensors across multiple heads, computes scaled dot-product attention softmax(Q·K^T / sqrt(d_k))·V with causal masking, and passes the result through RMSNorm and a GELU Feed-Forward Network.",
    },
    {
        "prompt": "how does diffusion image generation ddpm work",
        "response": "Denoising Diffusion Probabilistic Models (DDPM) define a forward schedule that adds Gaussian noise across T timesteps and train a conditional neural denoiser eps_theta(x_t, t, c) to iteratively reverse the noise into structured 2D images using classifier-free guidance.",
    },
    {
        "prompt": "write python code function example snippet",
        "response": "Here is a clean Python example using tblinc AI models:\n```python\nfrom tblinc.ai import create_model\n\nmodel = create_model('chat', embed_dim=24, num_heads=4)\nmodel.fit(['Transformers learn contextual representations via self-attention.'])\nresult = model.predict({'prompt': 'Transformers learn', 'max_tokens': 16})\nprint(result.prediction)\n```",
    },
    {
        "prompt": "api key token quota billing balance wallet topup",
        "response": "Every registered user receives a personal `tbl_sk_...` API key and a $10.00 starter credit (50,000 tokens). You can manage keys at `/profile/`, top up your balance at `/billing/`, or pass `X-API-Key: tbl_sk_...` to `/api/ai/chat`, `/api/ai/image`, `/api/ai/video`, `/api/ai/audio`, and `/api/ai/music`.",
    },
    {
        "prompt": "list all 25 ai models categories available in tblinc",
        "response": "tblinc includes 25 modular AI models: `chat` (Transformer LM), `search` (Hybrid RAG), `sentiment` (Naive Bayes), `summarize` (TextRank), `embed` (Vector Embeddings), `image` (Neural DDPM Diffusion), `vision` (ConvNet), `objects` (Bounding-Box Detector), `multimodal` (Contrastive VLM), `video` (Temporal Motion), `voice` (Formant TTS), `music` (Polyphonic Composer), `audio` (Spectral Classifier), `transcribe` (ASR), `neural` (Adam MLP), `classify` (Logistic SGD), `predict` (Ridge Regression), `tree` (CART), `forest` (Random Forest), `boost` (Gradient Boosting), `cluster` (K-Means++), `similarity` (k-NN), `detector` (Isolation Forest), `forecast` (Holt-Winters), and `recommend` (Matrix Factorization).",
    },
    {
        "prompt": "hardware gpu cuda xpu mps tensorflow pytorch acceleration",
        "response": "tblinc runs out-of-the-box in pure Python on any CPU and automatically accelerates tensor operations when PyTorch, TensorFlow, NumPy, NVIDIA CUDA, Intel XPU, or Apple MPS are installed via `tblinc install all`.",
    },
]

DEFAULT_CHAT_CORPUS: list[str] = [
    "Artificial intelligence builds adaptive neural networks that learn patterns from structured data.",
    "Transformers use multi-head self-attention to model long-range token dependencies in natural language.",
    "Retrieval augmented generation grounds language models with factual documents indexed by BM25 and cosine similarity.",
    "Denoising diffusion models synthesize images by reversing a Gaussian noise schedule with classifier-free guidance.",
    "Convolutional vision networks extract spatial edge and texture features using 2D kernels and pooling layers.",
    "Backpropagation and AdamW optimization update neural weights using first and second gradient moments.",
    "Formant speech synthesis and polyphonic music composition generate real 16-bit PCM WAV audio waveforms.",
    "The tblinc Python framework integrates 25 modular AI models with an MTV/MVC web server, SQLite ORM, and Admin Training Center.",
] + [pair["response"] for pair in DEFAULT_INSTRUCTION_PAIRS]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_']+|[.,!?;:\n]", text.lower())


def _content_terms(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower()) if t not in _STOPWORDS and len(t) > 1]


_SAFE_OPS: dict[type[Any], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _try_eval_math(prompt: str) -> str | None:
    """Safely evaluate arithmetic expressions embedded in a natural-language prompt."""
    cleaned = prompt.strip()
    m = re.search(r"([0-9]+(?:\.[0-9]+)?(?:\s*[\+\-\*\/\%\^]\s*[0-9]+(?:\.[0-9]+)?)+)", cleaned)
    if not m:
        return None
    expr_str = m.group(1).replace("^", "**")

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent too large")
            return float(_SAFE_OPS[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return float(_SAFE_OPS[type(node.op)](_eval(node.operand)))
        raise ValueError("Unsupported expression")

    try:
        tree = ast.parse(expr_str, mode="eval")
        val = _eval(tree.body)
        formatted = str(int(val)) if val == int(val) else f"{val:.4f}".rstrip("0").rstrip(".")
        return f"The result of `{m.group(1).strip()}` is **{formatted}**."
    except Exception:
        return None


@register_model
class MiniTransformerLM(BaseAIModel):
    """Causal Multi-Head Self-Attention Transformer & Instruction-Following Language Model.

    Combines learned token embeddings, sinusoidal positional encodings, a trainable
    `TransformerBlock` (Multi-Head Q/K/V Self-Attention + RMSNorm + GELU FFN),
    backed-off n-gram transition heads, and instruction-response semantic memory.
    """

    metadata = ModelMetadata(
        key="chat",
        name="AI Text & Chat Model",
        category="LLM / NLP",
        task="Text Generation & Language Modeling",
        description="Causal multi-head self-attention Transformer with instruction memory, top-k, and top-p sampling.",
        input_example={"prompt": "artificial intelligence builds", "max_tokens": 18, "temperature": 0.7},
        tags=["llm", "transformer", "attention", "generation", "chat"],
    )

    def __init__(
        self,
        context_window: int = 6,
        embed_dim: int = 24,
        num_heads: int = 4,
        seed: int = 42,
    ) -> None:
        super().__init__()
        self.context_window = max(2, context_window)
        self.embed_dim = max(4, embed_dim)
        self.num_heads = max(1, min(num_heads, self.embed_dim))
        self.seed = seed
        self.vocab: list[str] = []
        self.token_to_id: dict[str, int] = {}
        self.embeddings: list[list[float]] = []
        self.lm_head: list[list[float]] = []
        self.transformer = TransformerBlock(embed_dim=self.embed_dim, num_heads=self.num_heads, seed=seed)
        self.ngrams: dict[str, dict[str, int]] = {}
        self.unigrams: dict[str, int] = {}
        self.qa_pairs: list[dict[str, str]] = []

    def _dot(self, a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def _encode_sequence(self, token_ids: list[int]) -> list[list[float]]:
        seq: list[list[float]] = []
        for pos, tid in enumerate(token_ids):
            base = self.embeddings[tid]
            pe = Tensor.sinusoidal_position_encoding(pos, self.embed_dim)
            seq.append([base[d] + 0.15 * pe[d] for d in range(self.embed_dim)])
        out_seq, _ = self.transformer.forward(seq, causal=True)
        return out_seq

    def fit(
        self,
        corpus: list[Any] | str | None = None,
        epochs: int = 3,
        lr: float = 0.08,
        qa_pairs: list[dict[str, str]] | None = None,
    ) -> MiniTransformerLM:
        raw_items = [corpus] if isinstance(corpus, str) else list(corpus or DEFAULT_CHAT_CORPUS)
        extracted_docs: list[str] = []
        custom_qa: list[dict[str, str]] = list(DEFAULT_INSTRUCTION_PAIRS)
        if qa_pairs:
            custom_qa.extend(qa_pairs)

        for item in raw_items:
            if isinstance(item, dict):
                p = str(item.get("prompt") or item.get("question") or "").strip()
                r = str(item.get("response") or item.get("answer") or item.get("text") or "").strip()
                if p and r:
                    custom_qa.append({"prompt": p, "response": r})
                    extracted_docs.append(f"{p} {r}")
                elif r:
                    extracted_docs.append(r)
            elif isinstance(item, str) and item.strip():
                extracted_docs.append(item.strip())
                if "->" in item:
                    parts = item.split("->", 1)
                    custom_qa.append({"prompt": parts[0].strip(), "response": parts[1].strip()})

        self.qa_pairs = custom_qa
        all_tokens: list[list[str]] = [_tokenize(doc) for doc in extracted_docs if doc.strip()]
        flat = [tok for seq in all_tokens for tok in seq]
        if not flat:
            raise ValueError("Corpus must contain at least one token.")

        rng = random.Random(self.seed)
        counts = Counter(flat)
        self.vocab = sorted(counts.keys())
        self.token_to_id = {tok: idx for idx, tok in enumerate(self.vocab)}
        self.unigrams = dict(counts)

        # Build variable-order n-gram transition counts
        ngram_map: dict[str, Counter[str]] = defaultdict(Counter)
        for seq in all_tokens:
            for i in range(len(seq)):
                target = seq[i]
                for n in range(1, min(self.context_window, i) + 1):
                    ctx = " ".join(seq[i - n : i])
                    ngram_map[ctx][target] += 1
        self.ngrams = {ctx: dict(cnt) for ctx, cnt in ngram_map.items()}

        # Initialize token embeddings, causal Transformer block, and output projection head
        scale = 1.0 / math.sqrt(self.embed_dim)
        self.embeddings = [
            [rng.uniform(-scale, scale) for _ in range(self.embed_dim)]
            for _ in self.vocab
        ]
        self.lm_head = [list(vec) for vec in self.embeddings]
        self.transformer = TransformerBlock(embed_dim=self.embed_dim, num_heads=self.num_heads, seed=self.seed)

        total_loss = 0.0
        steps = 0
        for _ in range(max(1, epochs)):
            for seq in all_tokens:
                ids = [self.token_to_id[t] for t in seq]
                for i in range(1, len(ids)):
                    start = max(0, i - self.context_window)
                    ctx_ids = ids[start:i]
                    target_id = ids[i]

                    # Forward pass through causal Multi-Head Self-Attention + FFN
                    hidden_seq = self._encode_sequence(ctx_ids)
                    ctx_vec = hidden_seq[-1]

                    # Contrastive & output projection update
                    pos_vec = self.lm_head[target_id]
                    pos_dot = self._dot(ctx_vec, pos_vec)
                    pos_sig = 1.0 / (1.0 + math.exp(-max(-20.0, min(20.0, pos_dot))))
                    total_loss += -math.log(max(pos_sig, 1e-9))
                    grad = lr * (1.0 - pos_sig)
                    for d in range(self.embed_dim):
                        pos_vec[d] += grad * ctx_vec[d]
                        self.embeddings[target_id][d] += grad * 0.5 * ctx_vec[d]
                        self.embeddings[ctx_ids[-1]][d] += grad * 0.35 * pos_vec[d]

                    if len(self.vocab) > 2:
                        neg_id = rng.randrange(len(self.vocab))
                        if neg_id != target_id:
                            neg_vec = self.lm_head[neg_id]
                            neg_dot = self._dot(ctx_vec, neg_vec)
                            neg_sig = 1.0 / (1.0 + math.exp(-max(-20.0, min(20.0, neg_dot))))
                            total_loss += -math.log(max(1.0 - neg_sig, 1e-9))
                            ngrad = lr * neg_sig
                            for d in range(self.embed_dim):
                                neg_vec[d] -= ngrad * ctx_vec[d]
                    steps += 1

        self.is_fitted = True
        self.trained_at = time.time()
        avg_loss = total_loss / max(1, steps)
        self.training_metrics = {
            "vocab_size": len(self.vocab),
            "tokens_seen": len(flat),
            "ngram_contexts": len(self.ngrams),
            "qa_instructions": len(self.qa_pairs),
            "num_heads": self.num_heads,
            "embed_dim": self.embed_dim,
            "backend": active_compute_backend(),
            "avg_contrastive_loss": round(avg_loss, 4),
        }
        return self

    def _sequence_vector(self, tokens: list[str]) -> list[float]:
        known_ids = [self.token_to_id[t] for t in tokens[-self.context_window :] if t in self.token_to_id]
        if not known_ids or not self.embeddings:
            return [0.0] * self.embed_dim
        hidden = self._encode_sequence(known_ids)
        return hidden[-1]

    def answer_instruction(self, prompt: str) -> tuple[str | None, float]:
        """Match a conversational prompt against math evaluation and trained instruction pairs."""
        math_ans = _try_eval_math(prompt)
        if math_ans is not None:
            return math_ans, 0.99

        q_terms = _content_terms(prompt)
        all_q_toks = _tokenize(prompt)
        if not q_terms and not all_q_toks:
            return None, 0.0

        q_vec = self._sequence_vector(all_q_toks)
        best_resp: str | None = None
        best_score = 0.0

        for pair in self.qa_pairs:
            p_text = pair.get("prompt", "")
            r_text = pair.get("response", "")
            p_terms = set(_content_terms(p_text))
            p_all = set(_tokenize(p_text))
            overlap = sum(1.5 for t in q_terms if t in p_terms) + sum(0.6 for t in all_q_toks if t in p_all)
            if overlap <= 0.0:
                continue
            p_vec = self._sequence_vector(list(p_all))
            cos = max(0.0, Tensor.cosine_similarity(q_vec, p_vec))
            score = (overlap / max(1.0, math.sqrt(len(all_q_toks) * max(1, len(p_all))))) + 0.25 * cos
            if score > best_score:
                best_score = score
                best_resp = r_text

        if best_resp and best_score >= 0.42:
            return best_resp, round(min(0.98, 0.55 + best_score * 0.35), 4)
        return None, 0.0

    def _next_token_distribution(self, tokens: list[str], temperature: float = 0.8) -> tuple[list[str], list[float]]:
        candidates: dict[str, float] = {}
        # Combine backed-off n-gram log-probabilities with causal Multi-Head Transformer logits
        for n in range(min(self.context_window, len(tokens)), 0, -1):
            ctx = " ".join(tokens[-n:])
            if ctx in self.ngrams:
                weight = float(n * 1.6)
                total = sum(self.ngrams[ctx].values())
                for tok, cnt in self.ngrams[ctx].items():
                    candidates[tok] = candidates.get(tok, 0.0) + weight * math.log((cnt + 0.5) / (total + 1.0) + 1.0)

        if not candidates:
            top = sorted(self.unigrams.items(), key=lambda kv: kv[1], reverse=True)[:20]
            for tok, cnt in top:
                candidates[tok] = math.log(cnt + 1.0)

        # Causal Multi-Head Transformer hidden state projection
        known_ids = [self.token_to_id[t] for t in tokens[-self.context_window :] if t in self.token_to_id]
        if known_ids and self.embeddings:
            ctx_vec = self._encode_sequence(known_ids)[-1]
            head_vecs = self.lm_head if len(self.lm_head) == len(self.vocab) else self.embeddings
            for tok in list(candidates.keys()):
                tid = self.token_to_id.get(tok)
                if tid is not None:
                    candidates[tok] += 0.45 * self._dot(ctx_vec, head_vecs[tid])

        toks = list(candidates.keys())
        probs = Tensor.softmax([candidates[t] for t in toks], temperature=temperature)
        return toks, probs

    @timed_predict
    def predict(
        self,
        data: str | dict[str, Any],
        max_tokens: int = 20,
        temperature: float = 0.7,
        top_k: int = 8,
        top_p: float = 0.9,
        seed: int | None = None,
    ) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("MiniTransformerLM must be fitted before predict().")

        conversational = False
        if isinstance(data, dict):
            prompt = str(data.get("prompt", ""))
            max_tokens = int(data.get("max_tokens", max_tokens))
            temperature = float(data.get("temperature", temperature))
            top_k = int(data.get("top_k", top_k))
            top_p = float(data.get("top_p", top_p))
            conversational = bool(data.get("conversational", False))
        else:
            prompt = str(data)

        if conversational:
            inst_reply, inst_conf = self.answer_instruction(prompt)
            if inst_reply:
                return PredictionResult(
                    model=self.metadata.key,
                    prediction=inst_reply,
                    confidence=inst_conf,
                    details={
                        "mode": "instruction_transformer",
                        "vocab_size": len(self.vocab),
                        "num_heads": self.num_heads,
                    },
                )

        rng = random.Random(self.seed if seed is None else seed)
        tokens = _tokenize(prompt)
        generated: list[str] = []
        chosen_probs: list[float] = []

        for _ in range(max(1, min(max_tokens, 128))):
            toks, probs = self._next_token_distribution(tokens, temperature=temperature)
            paired = sorted(zip(toks, probs), key=lambda x: x[1], reverse=True)
            if top_k > 0:
                paired = paired[:top_k]

            # Nucleus (top-p) filtering
            filtered: list[tuple[str, float]] = []
            cum = 0.0
            for tok, p in paired:
                filtered.append((tok, p))
                cum += p
                if cum >= top_p:
                    break

            norm = sum(p for _, p in filtered) or 1.0
            r = rng.random() * norm
            acc = 0.0
            picked_tok, picked_p = filtered[0]
            for tok, p in filtered:
                acc += p
                if r <= acc:
                    picked_tok, picked_p = tok, p / norm
                    break

            tokens.append(picked_tok)
            generated.append(picked_tok)
            chosen_probs.append(picked_p)

        if conversational:
            gen_text = " ".join(generated).strip()
            gen_text = re.sub(r"\s+([.,!?;:])", r"\1", gen_text)
            text = gen_text[:1].upper() + gen_text[1:] if gen_text else prompt
        else:
            text = (prompt.strip() + " " + " ".join(generated)).strip()
            text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        avg_conf = sum(chosen_probs) / max(1, len(chosen_probs))
        return PredictionResult(
            model=self.metadata.key,
            prediction=text,
            confidence=round(avg_conf, 4),
            details={
                "generated_tokens": generated,
                "vocab_size": len(self.vocab),
                "num_heads": self.num_heads,
                "embed_dim": self.embed_dim,
            },
        )

    def evaluate(self, text: str) -> dict[str, Any]:
        tokens = _tokenize(text)
        if len(tokens) < 2 or not self.is_fitted:
            return {"perplexity": None, "tokens": len(tokens)}
        log_prob_sum = 0.0
        for i in range(1, len(tokens)):
            toks, probs = self._next_token_distribution(tokens[:i], temperature=1.0)
            dist = dict(zip(toks, probs))
            p = dist.get(tokens[i], 1e-4)
            log_prob_sum += -math.log(max(p, 1e-9))
        ppl = math.exp(log_prob_sum / (len(tokens) - 1))
        return {"perplexity": round(ppl, 4), "tokens": len(tokens)}

    def get_state(self) -> dict[str, Any]:
        return {
            "context_window": self.context_window,
            "embed_dim": self.embed_dim,
            "num_heads": self.num_heads,
            "seed": self.seed,
            "vocab": self.vocab,
            "embeddings": self.embeddings,
            "lm_head": self.lm_head,
            "transformer": self.transformer.get_state(),
            "ngrams": self.ngrams,
            "unigrams": self.unigrams,
            "qa_pairs": self.qa_pairs,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        self.context_window = int(state["context_window"])
        self.embeddings = state["embeddings"]
        inferred_dim = (
            len(self.embeddings[0])
            if (self.embeddings and isinstance(self.embeddings[0], list) and self.embeddings[0])
            else int(state.get("embed_dim", 24))
        )
        self.embed_dim = inferred_dim
        self.num_heads = max(1, min(int(state.get("num_heads", 4)), self.embed_dim))
        self.seed = int(state["seed"])
        self.vocab = list(state["vocab"])
        self.token_to_id = {tok: idx for idx, tok in enumerate(self.vocab)}
        raw_head = state.get("lm_head")
        if raw_head and len(raw_head) == len(self.vocab) and len(raw_head[0]) == self.embed_dim:
            self.lm_head = raw_head
        else:
            self.lm_head = [list(vec) for vec in self.embeddings]

        tf_state = state.get("transformer")
        if isinstance(tf_state, dict) and int(tf_state.get("embed_dim", 0)) == self.embed_dim:
            self.transformer = TransformerBlock(embed_dim=self.embed_dim, num_heads=self.num_heads, seed=self.seed)
            self.transformer.set_state(tf_state)
        else:
            self.transformer = TransformerBlock(embed_dim=self.embed_dim, num_heads=self.num_heads, seed=self.seed)

        self.ngrams = state["ngrams"]
        self.unigrams = state["unigrams"]
        saved_qa = state.get("qa_pairs")
        if saved_qa:
            existing_prompts = {p.get("prompt") for p in saved_qa if isinstance(p, dict)}
            merged_qa = list(saved_qa)
            for default_pair in DEFAULT_INSTRUCTION_PAIRS:
                if default_pair["prompt"] not in existing_prompts:
                    merged_qa.append(default_pair)
            self.qa_pairs = merged_qa
        else:
            self.qa_pairs = list(DEFAULT_INSTRUCTION_PAIRS)

    def _run_demo(self, custom_input: Any = None) -> dict[str, Any]:
        self.fit(DEFAULT_CHAT_CORPUS, epochs=2)
        sample = custom_input or self.metadata.input_example
        prediction = self.predict(sample)
        eval_metrics = self.evaluate("artificial intelligence builds adaptive neural networks.")
        return {
            "training": self.training_metrics,
            "evaluation": eval_metrics,
            "result": prediction.to_dict(),
        }
