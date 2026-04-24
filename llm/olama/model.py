import ollama
from rag import SalesRAG
from prompts import SalesPrompts, is_report_request


class SalesLLM:
    MODEL = "llama3.2"

    def __init__(self):
        self.rag = SalesRAG()

    def generate_followup_message(self, enquiry_data: dict) -> str:
        similar_docs = self.rag.search_similar(str(enquiry_data))
        prompt = SalesPrompts.followup_message(enquiry_data, similar_docs)
        response = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]

    def analyze_lead(self, enquiry_data: dict) -> str:
        similar_docs = self.rag.search_similar(str(enquiry_data))
        prompt = SalesPrompts.analyze_lead(enquiry_data, similar_docs)
        response = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]

    def summarize_feedback(self, feedback_text: str) -> str:
        similar_docs = self.rag.search_similar(feedback_text)
        prompt = SalesPrompts.summarize_feedback(feedback_text, similar_docs)
        response = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]

    def chat_with_data(self, user_query: str) -> str:
        """
        Smart routing:
          - If user asks for a 'report' → build full summary context + report prompt
          - Else → structured pandas query first, fallback to vector search
        Then stream the LLM response live and also return the full text.
        """

        # ── REPORT PATH ──────────────────────────────────────────────
        if is_report_request(user_query):
            context = self.rag.get_full_summary_context()
            prompt = SalesPrompts.report_chat(user_query, context)

        # ── NORMAL CHAT PATH ─────────────────────────────────────────
        else:
            structured_context = self.rag.get_structured_context(user_query)

            if structured_context:
                context = structured_context
            else:
                similar_docs = self.rag.search_similar(user_query, n_results=6)
                context = "\n".join(similar_docs) if similar_docs else "No relevant records found in the CRM database."

            prompt = SalesPrompts.general_chat(user_query, context)

        # ── STREAM + COLLECT ─────────────────────────────────────────
        response = ollama.chat(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        full_response = ""
        for chunk in response:
            piece = chunk["message"]["content"]
            print(piece, end="", flush=True)
            full_response += piece
        print()

        return full_response