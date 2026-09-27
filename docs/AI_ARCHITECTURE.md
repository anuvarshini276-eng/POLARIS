# AI pipeline

Upload validation → durable queue → PDF/DOCX/TXT/CSV extraction → normalization → overlapping chunks → metadata → configurable embeddings → persisted vectors. Hybrid lexical/vector ranking is permission-filtered, thresholded and top-k limited. Context is bounded and citations point to actual chunks/pages. Scores are retrieval relevance, never calibrated confidence. Insufficient evidence yields an explicit abstention. Uploaded text is untrusted data.

LLMProvider implementations: extractive Mock, OpenAI HTTP, local OpenAI-compatible HTTP. Embeddings: deterministic Mock, OpenAI, sentence-transformers (optional model download). Demo content is labeled and cannot establish model quality. Source IDs are selected by the server; provider output cannot invent citation IDs.
