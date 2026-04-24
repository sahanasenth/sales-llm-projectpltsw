import re
import os
import pandas as pd
from datetime import datetime, timedelta
from vector_db import VectorDB


class SalesRAG:
    def __init__(self):
        self.db = VectorDB()
        self.data_path = "./data"
        self._enquiry_df = None
        self._appointment_df = None
        self._feedback_df = None

    def _load_dataframes(self):
        """Load and cache all three dataframes for structured queries."""
        if self._enquiry_df is None:
            self._enquiry_df = pd.read_csv(
                os.path.join(self.data_path, "sales_enquiry_dataset.csv")
            ).fillna("Unknown")
            self._enquiry_df["Enquiry Date"] = pd.to_datetime(
                self._enquiry_df["Enquiry Date"], errors="coerce"
            )
            self._enquiry_df["Appointment Date"] = pd.to_datetime(
                self._enquiry_df["Appointment Date"], errors="coerce"
            )

        if self._appointment_df is None:
            self._appointment_df = pd.read_csv(
                os.path.join(self.data_path, "sales_appointment_dataset.csv")
            ).fillna("Unknown")
            self._appointment_df["Appointment Date"] = pd.to_datetime(
                self._appointment_df["Appointment Date"], errors="coerce"
            )

        if self._feedback_df is None:
            self._feedback_df = pd.read_csv(
                os.path.join(self.data_path, "sales_feedback_dataset.csv")
            ).fillna("Unknown")
            self._feedback_df["Date"] = pd.to_datetime(
                self._feedback_df["Date"], errors="coerce"
            )

    def load_and_process_csvs(self):
        """Load all 3 CSVs and convert rows into meaningful sentences for the vector DB."""
        self._load_dataframes()
        documents = []
        ids = []
        metadatas = []

        # Enquiry CSV
        for idx, row in self._enquiry_df.iterrows():
            sentence = (
                f"Customer {row['Customer Name']} (Phone: {row['Phone Number']}) "
                f"made an enquiry for {row['Vehicle Name / Model']} via {row['Enquiry Source']} "
                f"on {row['Enquiry Date'].strftime('%d/%m/%Y') if pd.notna(row['Enquiry Date']) else 'Unknown'}. "
                f"Status: {row['Status']}. Budget/Payment: {row['Payment Type']}. "
                f"Test ride taken: {row['Test Ride Taken']}. "
                f"Customer type: {row['Customer Type']}. City: {row['City / State']}."
            )
            documents.append(sentence)
            ids.append(f"enq_{idx}")
            metadatas.append({"source": "enquiry", "status": str(row["Status"])})

        # Appointment CSV
        for idx, row in self._appointment_df.iterrows():
            sentence = (
                f"Appointment for customer {row['Customer Name']} "
                f"for vehicle {row['Vehicle']} on "
                f"{row['Appointment Date'].strftime('%d/%m/%Y') if pd.notna(row['Appointment Date']) else 'Unknown'} "
                f"at {row['Time']}. Status: {row['Status']}."
            )
            documents.append(sentence)
            ids.append(f"app_{idx}")
            metadatas.append({"source": "appointment", "status": str(row["Status"])})

        # Feedback CSV
        for idx, row in self._feedback_df.iterrows():
            sentence = (
                f"Customer {row['Customer Name']} gave feedback: '{row['Feedback']}'. "
                f"Rating: {row['Rating']}/5 on "
                f"{row['Date'].strftime('%d/%m/%Y') if pd.notna(row['Date']) else 'Unknown'}."
            )
            documents.append(sentence)
            ids.append(f"fb_{idx}")
            metadatas.append({"source": "feedback"})

        print(f"✅ Processed {len(documents)} documents from 3 CSV files.")
        self.db.add_documents(documents=documents, ids=ids, metadatas=metadatas)

    def search_similar(self, query: str, n_results: int = 6) -> list:
        """Search for similar past sales records via vector similarity."""
        return self.db.search(query, n_results)

    def get_full_summary_context(self) -> str:
        """
        Builds a comprehensive context string from all 3 datasets.
        Used when the user asks for a full report.
        """
        self._load_dataframes()
        lines = []

        # --- Enquiry Summary ---
        enq = self._enquiry_df
        lines.append("ENQUIRY DATA:")
        lines.append(f"  Total enquiries: {len(enq)}")
        for status, grp in enq.groupby("Status"):
            lines.append(f"  - {status}: {len(grp)}")
        top_vehicles = enq["Vehicle Name / Model"].value_counts().head(3)
        lines.append("  Top enquired vehicles:")
        for v, c in top_vehicles.items():
            lines.append(f"    • {v}: {c} enquiries")
        top_sources = enq["Enquiry Source"].value_counts().head(3)
        lines.append("  Top enquiry sources:")
        for s, c in top_sources.items():
            lines.append(f"    • {s}: {c}")

        # --- Appointment Summary ---
        apt = self._appointment_df
        lines.append("\nAPPOINTMENT DATA:")
        lines.append(f"  Total appointments: {len(apt)}")
        for status, grp in apt.groupby("Status"):
            lines.append(f"  - {status}: {len(grp)}")

        # --- Feedback Summary ---
        fb = self._feedback_df
        lines.append("\nFEEDBACK DATA:")
        lines.append(f"  Total feedback entries: {len(fb)}")
        if "Rating" in fb.columns:
            avg = fb["Rating"].mean()
            lines.append(f"  Average rating: {avg:.1f}/5")
            for rating in sorted(fb["Rating"].unique(), reverse=True):
                c = len(fb[fb["Rating"] == rating])
                lines.append(f"  - {rating}/5: {c} feedback(s)")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # STRUCTURED QUERY METHODS
    # ------------------------------------------------------------------

    def get_structured_context(self, query: str) -> str | None:
        """
        Detects if the query needs a precise data answer and returns a
        pre-built context string. Returns None for vector search fallback.
        """
        self._load_dataframes()
        q = query.lower()
        today = datetime.today().date()

        # ---- DATE PARSING ----
        target_date = None
        if "today" in q:
            target_date = today
        elif "tomorrow" in q:
            target_date = today + timedelta(days=1)
        elif "yesterday" in q:
            target_date = today - timedelta(days=1)
        else:
            date_patterns = [
                r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b",
                r"\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b",
            ]
            for pat in date_patterns:
                m = re.search(pat, q)
                if m:
                    try:
                        raw = m.group(0).replace("-", "/")
                        parts = raw.split("/")
                        if len(parts[2]) == 4:
                            for fmt in ["%m/%d/%Y", "%d/%m/%Y"]:
                                try:
                                    target_date = datetime.strptime(raw, fmt).date()
                                    break
                                except ValueError:
                                    pass
                        else:
                            target_date = datetime.strptime(raw, "%Y/%m/%d").date()
                    except Exception:
                        pass
                    break

        # ---- DATE-BASED APPOINTMENT QUERIES ----
        if target_date and any(w in q for w in ["appointment", "schedule", "report", "meeting", "today", "tomorrow", "yesterday"]):
            df = self._appointment_df.copy()
            df["_date"] = df["Appointment Date"].dt.date
            filtered = df[df["_date"] == target_date]
            date_str = target_date.strftime("%d/%m/%Y")
            if filtered.empty:
                return f"No appointments found for {date_str}."
            lines = [f"Appointments for {date_str} (Today: {today.strftime('%d/%m/%Y')}):"]
            for _, row in filtered.iterrows():
                lines.append(
                    f"  - {row['Customer Name']} | {row['Vehicle']} | {row['Time']} | Status: {row['Status']}"
                )
            lines.append(f"\nTotal: {len(filtered)} appointment(s).")
            return "\n".join(lines)

        # ---- COUNT QUERIES ----
        if any(w in q for w in ["how many", "count", "total", "number of"]):

            if target_date and "enquir" in q:
                df = self._enquiry_df.copy()
                df["_date"] = df["Enquiry Date"].dt.date
                c = len(df[df["_date"] == target_date])
                return f"Total enquiries on {target_date.strftime('%d/%m/%Y')}: {c}"

            if any(w in q for w in ["sold", "booked", "purchased", "bought", "sale"]):
                if target_date:
                    df = self._enquiry_df.copy()
                    df["_date"] = df["Enquiry Date"].dt.date
                    c = len(df[(df["_date"] == target_date) & (df["Status"].str.lower() == "booked")])
                    return f"Bookings (status=Booked) on {target_date.strftime('%d/%m/%Y')}: {c}"
                c = len(self._enquiry_df[self._enquiry_df["Status"].str.lower() == "booked"])
                return f"Total bookings (status=Booked) in the database: {c}"

            if "appointment" in q:
                if target_date:
                    df = self._appointment_df.copy()
                    df["_date"] = df["Appointment Date"].dt.date
                    c = len(df[df["_date"] == target_date])
                    return f"Total appointments on {target_date.strftime('%d/%m/%Y')}: {c}"
                total = len(self._appointment_df)
                scheduled = len(self._appointment_df[self._appointment_df["Status"].str.lower() == "scheduled"])
                cancelled = len(self._appointment_df[self._appointment_df["Status"].str.lower() == "cancelled"])
                completed = len(self._appointment_df[self._appointment_df["Status"].str.lower() == "completed"])
                return (
                    f"Appointment summary:\n"
                    f"  Total: {total}\n"
                    f"  Scheduled: {scheduled}\n"
                    f"  Completed: {completed}\n"
                    f"  Cancelled: {cancelled}"
                )

        # ---- VEHICLE-SPECIFIC QUERIES ----
        all_vehicles = pd.concat([
            self._enquiry_df["Vehicle Name / Model"],
            self._appointment_df["Vehicle"],
        ]).dropna().unique()

        matched_vehicle = None
        for v in all_vehicles:
            if str(v).lower() in q:
                matched_vehicle = str(v)
                break

        if matched_vehicle:
            enq = self._enquiry_df[
                self._enquiry_df["Vehicle Name / Model"].str.lower() == matched_vehicle.lower()
            ]
            appt = self._appointment_df[
                self._appointment_df["Vehicle"].str.lower() == matched_vehicle.lower()
            ]

            # Search feedback using full vehicle name (all words must match)
            vehicle_words = matched_vehicle.lower().split()
            fb = self._feedback_df.copy()
            for word in vehicle_words:
                fb = fb[fb["Feedback"].str.lower().str.contains(word, na=False)]

            lines = [f"Data summary for vehicle: {matched_vehicle}"]
            lines.append(f"\nEnquiries: {len(enq)}")
            if not enq.empty:
                for status, grp in enq.groupby("Status"):
                    lines.append(f"  - {status}: {len(grp)}")
            lines.append(f"\nAppointments: {len(appt)}")
            if not appt.empty:
                for status, grp in appt.groupby("Status"):
                    lines.append(f"  - {status}: {len(grp)}")

            if not fb.empty:
                avg_rating = fb["Rating"].mean()
                lines.append(f"\nFeedback mentions: {len(fb)}")
                lines.append(f"Average rating: {avg_rating:.1f}/5")
                for _, row in fb.iterrows():
                    lines.append(f"  - {row['Customer Name']}: '{row['Feedback']}' ({row['Rating']}/5)")

            return "\n".join(lines)

        return None


# For initial data load
if __name__ == "__main__":
    rag = SalesRAG()
    rag.load_and_process_csvs()
    print("RAG setup completed! Data is safely stored in ChromaDB.")