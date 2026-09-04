# CampusMind RAG Evaluation Strategy

## Evaluation Framework

CampusMind evaluates RAG performance against the ground-truth benchmark suite in `tests/eval_qa_pairs.json`.

### Key Metrics Tracked:
1. **Context Precision**: Ratio of retrieved chunks that contain ground-truth answers.
2. **Context Recall**: Percentage of ground-truth facts retrieved by ChromaDB.
3. **Faithfulness**: Rate at which generated answers stick strictly to retrieved context without external knowledge additions.
4. **Fallback Accuracy**: Verified trigger rate of the "I don't have information on that" response when out-of-domain questions are asked.

## Running Evaluation Benchmarks
```bash
pytest tests/test_retrieval.py -v
```
