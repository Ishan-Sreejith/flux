from typing import List


CATEGORIES = {
    "software": [
        "What is version control?",
        "Explain continuous integration.",
        "What is a REST API?",
        "What is dependency injection?",
        "Explain test-driven development.",
    ],
    "ai": [
        "What is supervised learning?",
        "Explain overfitting simply.",
        "What is an embedding?",
        "What is the bias-variance tradeoff?",
        "What is gradient descent?",
    ],
    "data": [
        "What is a database index?",
        "Explain normalization in databases.",
        "What is a primary key?",
        "Explain ACID properties.",
        "What is data warehousing?",
    ],
    "systems": [
        "What is a process?",
        "Explain a thread vs process.",
        "What is a kernel?",
        "What is a container?",
        "What is a virtual machine?",
    ],
    "security": [
        "What is phishing?",
        "Explain multi-factor authentication.",
        "What is encryption?",
        "What is SQL injection?",
        "What is zero trust?",
    ],
}

TEMPLATES = [
    "Explain {} in simple terms.",
    "Give a concise definition of {}.",
    "Why does {} matter?",
    "Provide a real-world example of {}.",
    "What are common mistakes about {}?",
    "How does {} work?",
]

TERMS = [
    "load balancing",
    "caching",
    "feature flags",
    "observability",
    "unit testing",
    "integration testing",
    "API rate limiting",
    "data pipeline",
    "distributed systems",
    "consensus",
    "schema migration",
    "vector search",
    "semantic search",
    "content moderation",
    "data governance",
    "privacy by design",
    "latency",
    "throughput",
    "backpressure",
    "event sourcing",
    "message queue",
    "task scheduler",
    "service mesh",
    "idempotency",
    "retry strategy",
    "exponential backoff",
    "circuit breaker",
    "auth token",
    "API gateway",
    "edge computing",
    "feature store",
    "model drift",
    "prompt injection",
    "RAG",
    "knowledge graph",
    "tokenization",
    "serialization",
    "profiling",
    "deadlock",
    "race condition",
    "memory leak",
    "garbage collection",
    "CPU cache",
    "I/O bound vs CPU bound",
    "deployment pipeline",
    "blue green deployment",
    "canary release",
    "rollout strategy",
    "incident response",
    "postmortem",
    "SLO",
    "SLA",
    "error budget",
    "data lineage",
]


def generate_seeds(min_count: int = 300) -> List[str]:
    seeds = []
    for items in CATEGORIES.values():
        seeds.extend(items)

    for term in TERMS:
        for tpl in TEMPLATES:
            seeds.append(tpl.format(term))


    if len(seeds) < min_count:
        extras = [
            f"Explain {term} briefly." for term in TERMS
        ]
        seeds.extend(extras)


    seen = set()
    unique = []
    for q in seeds:
        if q not in seen:
            unique.append(q)
            seen.add(q)
    return unique[:min_count]
