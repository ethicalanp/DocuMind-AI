from openai import OpenAI
import json

from app.core.config import (
    LLM_API_KEY,
    LLM_MODEL,
    LLM_BASE_URL
)


# ==========================================
# Groq Client
# ==========================================

client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)


# ==========================================
# Generate Answer
# ==========================================

def generate_answer(
    question: str,
    context: str
):

    system_prompt = """
You are DocuMind AI, a business document assistant.

Your job is to answer questions using ONLY the
information provided in the document context.

IMPORTANT RULES:

1. Never use outside knowledge.
2. Never invent facts.
3. If the answer is not supported by the document
   context, say that the information was not found
   in the uploaded documents.
4. Keep the answer concise and useful.
5. Every factual claim must be supported by the
   provided document context.
6. Do not invent document names, IDs, page numbers,
   or sources.
7. Return ONLY valid JSON.

Your JSON response MUST have exactly these fields:

{
    "answer": "your answer here",
    "grounded": true
}

Set "grounded" to true only when the document
context supports the answer.

Set "grounded" to false when the answer cannot
be determined from the document context.
"""


    user_prompt = f"""
DOCUMENT CONTEXT:

{context}


USER QUESTION:

{question}


Return ONLY JSON.

Example:

{{
    "answer": "The document states that...",
    "grounded": true
}}
"""


    # ==========================================
    # Call Groq
    # ==========================================

    response = client.chat.completions.create(

        model=LLM_MODEL,

        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],

        temperature=0
    )


    raw_response = response.choices[0].message.content


    # ==========================================
    # Parse JSON
    # ==========================================

    try:

        result = json.loads(
            raw_response
        )

    except json.JSONDecodeError:

        # Fallback if the model returns
        # malformed JSON.

        return {
            "answer": raw_response,
            "grounded": True
        }


    # ==========================================
    # Validate Fields
    # ==========================================

    answer = result.get(
        "answer",
        ""
    )

    grounded = result.get(
        "grounded",
        False
    )


    return {
        "answer": answer,
        "grounded": bool(grounded)
    }