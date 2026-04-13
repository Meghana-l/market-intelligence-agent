from groq import Groq

from app.core.config import settings
from app.models.schemas import DocumentChunk


class GroqAgentService:
    def __init__(self) -> None:
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    def answer_question(self, question: str, chunks: list[DocumentChunk]) -> str:
        context = "\n\n".join(f"[{idx + 1}] {chunk.text}" for idx, chunk in enumerate(chunks))
        prompt = (
            "You are ARIA, a stock market intelligence assistant. Use the evidence context to provide clear "
            "analysis, key risks, and actionable takeaways. "
            "Write in plain English with clean formatting — use simple numbered lists and short paragraphs. "
            "Do NOT use markdown symbols like **, ##, or *. Just plain readable text.\n\n"
            f"Question: {question}\n\n"
            f"Context:\n{context}"
        )

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
        )
        return completion.choices[0].message.content or "No response returned by Groq model."
