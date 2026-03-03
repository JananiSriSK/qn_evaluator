# Model Selection Rationale

## Why These Specific Models?

### 1. all-MiniLM-L6-v2 (Bi-Encoder)

**Purpose**: Fast semantic retrieval from large document collections

**Why this model:**
- **Speed**: 384 dimensions (vs 768 in larger models) → 2x faster
- **Accuracy**: 58.8% on STS benchmark (good enough for retrieval)
- **Size**: 80MB model → fast loading, low memory
- **Use case fit**: Designed for semantic search, not generation
- **Batch processing**: Can embed 1000s of chunks efficiently

**Alternative considered:**
- `all-mpnet-base-v2` (768 dims, 420MB) → Too slow for real-time
- `all-MiniLM-L12-v2` (384 dims, 120MB) → Marginal accuracy gain, slower

**Where used:**
- FAISS index building (embed book chunks)
- Question embedding for retrieval
- Topic candidate selection (bi-encoder stage)

---

### 2. cross-encoder/ms-marco-MiniLM-L-6-v2 (Cross-Encoder)

**Purpose**: Precise reranking of top candidates

**Why this model:**
- **Accuracy**: Trained on MS MARCO (passage ranking dataset)
- **Architecture**: Cross-attention between question and topic → better than bi-encoder for final ranking
- **Speed**: 6 layers (vs 12 in base) → 2x faster inference
- **Size**: 90MB → acceptable for reranking 10 candidates
- **Output**: Raw relevance scores (not embeddings)

**Why cross-encoder after bi-encoder:**
- Bi-encoder: Fast but approximate (dot product similarity)
- Cross-encoder: Slow but accurate (full attention)
- **Two-stage retrieval**: Bi-encoder narrows 1000s → 10, Cross-encoder picks best from 10

**Alternative considered:**
- `ms-marco-MiniLM-L-12-v2` (12 layers) → Too slow for real-time
- `ms-marco-TinyBERT-L-6` → Lower accuracy

**Where used:**
- Topic matching (rerank top 10 candidates)
- Syllabus enrichment (rerank book chunks)

**Why sigmoid conversion:**
- MS MARCO produces raw logits (can be negative)
- Sigmoid converts to probabilities [0, 1]
- Enables relative comparison (margin, dominance rules)

---

### 3. final_bloom_model (DistilBERT fine-tuned)

**Purpose**: Classify questions into Bloom's Taxonomy levels (BT1-BT6)

**Why DistilBERT base:**
- **Speed**: 40% faster than BERT-base
- **Size**: 66M parameters (vs 110M in BERT)
- **Accuracy**: 97% of BERT performance
- **Fine-tuning**: Trained on academic question dataset with BT labels

**Why not use LLM (GPT/Llama):**
- LLMs are overkill for 6-class classification
- 200ms inference vs 2-5s for LLM
- Deterministic outputs (no prompt engineering needed)
- No API costs

**Where used:**
- Bloom taxonomy prediction for every question

---

### 4. llama-3.3-70b-versatile (Groq API)

**Purpose**: Generate enriched subtopics from book content

**Why LLM here:**
- **Task**: Generate human-readable subtopic names (creative task)
- **Input**: Long context (10 book chunks, ~3000 tokens)
- **Output**: Structured JSON array of subtopics
- **Cannot use**: Classification models (not generative)

**Why Groq:**
- **Speed**: 500 tokens/sec (vs 50 tokens/sec OpenAI)
- **Cost**: $0.59/1M tokens (vs $15/1M GPT-4)
- **Quality**: Llama 3.3 70B comparable to GPT-4

**Why not smaller model:**
- Llama 8B: Poor at following JSON format
- Llama 13B: Inconsistent subtopic quality
- 70B: Reliable, follows instructions

**Where used:**
- Syllabus enrichment (one-time operation)
- Not used in real-time evaluation

---

## Architecture Decision: Two-Stage Retrieval

```
Question: "Explain deadlock in OS"
         │
         ▼
┌────────────────────────────────────┐
│  Stage 1: Bi-Encoder (Fast)        │
│  all-MiniLM-L6-v2                  │
│                                     │
│  Search 6500 chunks → Top 10       │
│  Time: 50ms                        │
└────────────────┬───────────────────┘
                 │
                 ▼
┌────────────────────────────────────┐
│  Stage 2: Cross-Encoder (Accurate) │
│  ms-marco-MiniLM-L-6-v2            │
│                                     │
│  Rerank 10 → Best match            │
│  Time: 300ms                       │
└────────────────────────────────────┘
```

**Why not just cross-encoder:**
- Cross-encoder on 6500 chunks = 6500 × 30ms = 195 seconds
- Two-stage = 50ms + 300ms = 350ms (557x faster)

**Why not just bi-encoder:**
- Bi-encoder accuracy: ~70% (dot product similarity)
- Cross-encoder accuracy: ~90% (full attention)
- False "Out of Syllabus" reduced by 20%

---

## Performance vs Accuracy Trade-offs

| Model Choice | Speed | Accuracy | Memory | Cost |
|--------------|-------|----------|--------|------|
| **Bi-Encoder: all-MiniLM-L6-v2** | ✓✓✓ | ✓✓ | ✓✓✓ | Free |
| Alternative: all-mpnet-base-v2 | ✓ | ✓✓✓ | ✓ | Free |
| **Cross-Encoder: ms-marco-MiniLM-L-6** | ✓✓ | ✓✓✓ | ✓✓ | Free |
| Alternative: ms-marco-MiniLM-L-12 | ✓ | ✓✓✓ | ✓ | Free |
| **Bloom: DistilBERT fine-tuned** | ✓✓✓ | ✓✓✓ | ✓✓✓ | Free |
| Alternative: GPT-4 API | ✓ | ✓✓✓ | N/A | $$$$ |
| **Enrichment: Llama 3.3 70B (Groq)** | ✓✓✓ | ✓✓✓ | N/A | $ |
| Alternative: GPT-4 | ✓ | ✓✓✓ | N/A | $$$$ |

**Selected configuration:**
- Total inference time: ~550ms per question
- Total cost: ~$0.01 per 1000 questions (Groq only, one-time enrichment)
- Memory usage: ~2GB (all models loaded)

---

## Why Not Use Single Large Model?

**Option: Use GPT-4 for everything**

❌ **Problems:**
1. **Latency**: 2-5s per question (vs 550ms)
2. **Cost**: $15/1M tokens = $0.015 per question (vs $0.00001)
3. **Reliability**: Prompt engineering needed, inconsistent outputs
4. **Offline**: Requires internet, API dependency
5. **Privacy**: Sends questions to OpenAI

**Our approach:**
- Specialized models for each task
- Local inference (no API for evaluation)
- LLM only for creative task (enrichment)
- 10x faster, 1000x cheaper

---

## Model Loading Strategy

**Singleton Pattern (model_registry.py):**
```python
# Load once at startup
model_registry.load_all_models()

# Reuse everywhere
bi_encoder = model_registry.get_bi_encoder()
cross_encoder = model_registry.get_cross_encoder()
```

**Why:**
- Models loaded once (5-10s startup)
- Shared across all requests
- No repeated loading overhead
- Memory efficient (single instance)

**Startup time:**
- Bi-encoder: 2s
- Cross-encoder: 2s
- Bloom model: 3s
- Total: ~7s (acceptable for backend startup)

---

## Summary

| Task | Model | Why |
|------|-------|-----|
| **Retrieval** | all-MiniLM-L6-v2 | Fast semantic search, 384 dims |
| **Reranking** | ms-marco-MiniLM-L-6-v2 | Accurate relevance scoring |
| **Classification** | DistilBERT fine-tuned | Fast BT1-BT6 prediction |
| **Generation** | Llama 3.3 70B (Groq) | Quality subtopic generation |

**Key principle**: Use the smallest, fastest model that achieves acceptable accuracy for each specific task.
