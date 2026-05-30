# PoliRAG
Agent ChatBot with RAG capabilities on university material

# Architecture

                        [ New User Message ]

                                 │
                                 ▼
                     1. Node: cache_judge 
               (Tiny Cloud LLM Evaluates Cache)
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼

    (Cache Hit: YES)                               (Cache Miss: NO)
    Skip RAG Search                          2. Node: rewrite_judge
         │                               (Tiny Cloud LLM Checks History)
         │                                               │
         │                                               │ 
         │                                               │
         │                        ┌──────────────────────┴──────────────────────┐
         │                        ▼                                             ▼
         │               (Needs Context: YES)                            (Standalone: NO)
         │               3. Node: rewrite_exec                             Skip Rewriter 
         │                        │                                             │
         │                        └──────────────────────┬──────────────────────┘
         │                                               │
         │                                               ▼
         │                                   4. Node: local_search
         │                                (Hybrid RAG + Cross-Encoder)
         │                                               │
         │                        ┌──────────────────────┴──────────────────────┐
         │                        ▼                                             ▼
         │                   (Score < 0.45)                               (Score >= 0.45)
         │             5. Node: web_search_fallback                  Skip deterministic WebSearch 
         │                        │                                             │
         └───────────────────────►└──────────────────────┬──────────────────────┘
                                                         │
                                                         ▼
                                              6. Node: agent_think
                                         (Dynamic Tools: Python, Calc, Web)
                                                         │
                                                         ▼
                                              7. Node: ltm_compile
                                                         │
                                                         ▼
                                                 [ Final Response ]