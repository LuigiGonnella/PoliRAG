# How Sources Are Retrieved

PoliRAG source chips come from the local Qdrant retrieval stage, not from the language model.

## Retrieval Flow

1. The user message is optionally rewritten into a standalone search query.
2. The backend builds a Qdrant filter from the active chat scope:
   - `degree_level`
   - `year`
   - `course`
3. The query is embedded locally with FastEmbed.
4. Qdrant performs hybrid retrieval:
   - dense vector search on the `dense` vector
   - sparse BM25 search on the `sparse` vector
   - reciprocal-rank fusion of both result sets
5. The candidate chunks are reranked by the local cross-encoder.
6. The top chunks are passed to the assistant as context.

## Source Chips

Each retrieved chunk contains Qdrant payload metadata such as:

- `source`
- `index`
- `course`
- `year`
- `degree_level`

The UI source chips are built from the returned citation metadata:

- `source` becomes the file name shown in the chip.
- `index` is shown as the page/chunk indicator when available.
- `score` is retained for debugging and ranking.

## Duplicate Handling

Multiple relevant chunks often come from the same file. The backend now deduplicates citations by file source, merging page/chunk indicators where possible. The frontend also deduplicates defensively before rendering chips.

This means a file can contribute several context chunks to the answer while still appearing only once in the source list.
