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
            "analysis, key risks, and actionable takeaways.\n"
            "Format your response like this:\n"
            "- Start with 1-2 sentences of overall analysis.\n"
            "- Then write 'Key Points:' followed by a numbered list, one point per line.\n"
            "- Then write 'Key Risks:' followed by a numbered list, one point per line.\n"
            "- Then write 'Actionable Takeaways:' followed by a numbered list, one point per line.\n"
            "Do NOT use markdown symbols like **, ##, or *. Use plain text only. Each numbered item must be on its own line.\n\n"
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
