import json
import re

from src.retriever import retrieve_top_chunks
from src.llm import ask_llm


NOT_FOUND_MESSAGE = (
    "لم أجد معلومات كافية للإجابة عن هذا السؤال في الوثيقة."
)


def _parse_json_response(raw_answer):
    try:
        return json.loads(raw_answer)

    except json.JSONDecodeError:
        match = re.search(
            r"\{.*\}",
            raw_answer,
            flags=re.DOTALL,
        )

        if not match:
            return None

        try:
            return json.loads(
                match.group(0)
            )

        except json.JSONDecodeError:
            return None


def answer_question(
    query,
    chunks,
    embeddings,
    embedding_model,
    top_k=3,
):
    results = retrieve_top_chunks(
        query=query,
        chunks=chunks,
        embeddings=embeddings,
        model=embedding_model,
        top_k=top_k,
    )

    if not results:
        return {
            "answer": NOT_FOUND_MESSAGE,
            "sources": [],
        }

    context_parts = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        context_parts.append(
            f"""
SOURCE {index}

File: {result['file_name']}
Page: {result['page']}
Chunk: {result['chunk_number']}

Text:
{result['text']}
"""
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = f"""
You are a strict document question-answering assistant.

Use ONLY the provided context.

Your job is to:

1. Decide whether the context contains enough information
   to answer the question.

2. Identify which sources directly support the answer.

3. Compare claims carefully before calling them contradictory.

IMPORTANT CONTRADICTION RULE:

Two statements are contradictory ONLY if they refer to the
same fact, same metric, same definition, and same time period.

Do NOT call two statements contradictory merely because
they contain different numbers if they describe different
concepts or use different wording.

For example:

"34th country integrated into a global surveillance network"

and

"31st country implementing sentinel surveillance"

must NOT automatically be treated as the same metric.

If their relationship cannot be established from the
provided text, explain that the document uses different
wording instead of declaring a contradiction.

Return ONLY valid JSON with this exact structure:

{{
  "answerable": true,
  "answer": "your answer here",
  "used_sources": [1]
}}

If more than one source is genuinely useful:

{{
  "answerable": true,
  "answer": "your answer here",
  "used_sources": [1, 3]
}}

If the context is not sufficient:

{{
  "answerable": false,
  "answer": "{NOT_FOUND_MESSAGE}",
  "used_sources": []
}}

STRICT RULES:

- Never use outside knowledge.
- Never invent information.
- Answer in the same language as the user's question.
- Use only sources that directly support the answer.
- Do not include irrelevant sources.
- Do not silently merge different concepts.
- Do not declare a contradiction unless the two claims
  clearly describe the same metric or fact.
- If two passages use different definitions or wording,
  mention that distinction when relevant.
- Keep the answer concise and clear.
- Do not mention chunk numbers in the answer.
- Mention page numbers only when they help clarify
  different claims.

QUESTION:
{query}

CONTEXT:
{context}
"""

    raw_answer = ask_llm(
        prompt
    )

    parsed = _parse_json_response(
        raw_answer
    )

    if parsed is None:
        return {
            "answer": raw_answer,
            "sources": [],
        }

    answerable = parsed.get(
        "answerable",
        False,
    )

    answer = parsed.get(
        "answer",
        NOT_FOUND_MESSAGE,
    )

    if not answerable:
        return {
            "answer": answer,
            "sources": [],
        }

    used_source_ids = parsed.get(
        "used_sources",
        [],
    )

    sources = []
    seen_pages = set()

    for source_id in used_source_ids:

        if not isinstance(
            source_id,
            int,
        ):
            continue

        index = source_id - 1

        if (
            index < 0
            or index >= len(results)
        ):
            continue

        result = results[index]

        source_key = (
            result["file_name"],
            result["page"],
        )

        if source_key in seen_pages:
            continue

        seen_pages.add(
            source_key
        )

        sources.append(
            {
                "file_name": (
                    result["file_name"]
                ),
                "page": (
                    result["page"]
                ),
                "chunk_number": (
                    result["chunk_number"]
                ),
                "score": (
                    result["score"]
                ),
                "text": (
                    result["text"]
                ),
            }
        )

    return {
        "answer": answer,
        "sources": sources,
    }