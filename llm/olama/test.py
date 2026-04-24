import sys
from datetime import datetime
from model import SalesLLM
from prompts import is_report_request


def print_report_box(text: str):
    """Wraps a report response in a print-friendly box."""
    print("\n" + "═" * 62)
    print(text)
    print("═" * 62)
    print("📄 (This report is print-ready — copy to Word/Notepad to print)")
    print()


def main():
    print("🚀 Initializing Sales Assistant...")
    llm = SalesLLM()

    today = datetime.today().strftime("%d/%m/%Y (%A)")
    print(f"\n📅 Today: {today}")
    print("\n" + "=" * 62)
    print("🤖 SALES CRM AI IS ONLINE!")
    print("Ask anything about enquiries, appointments, or feedback.")
    print("Say 'report' or 'give report' to get a printable summary.")
    print("Type 'exit' or 'quit' to close.")
    print("=" * 62 + "\n")

    while True:
        user_input = input("👤 You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Shutting down. Goodbye!")
            sys.exit()

        if not user_input:
            continue

        if is_report_request(user_input):
            print("\n🤖 AI (generating report...):\n")
            result = llm.chat_with_data(user_input)
            # The streaming already printed it — show the print-ready box hint
            print_report_box(result)
        else:
            print("🤖 AI: ", end="")
            llm.chat_with_data(user_input)
            print("\n" + "-" * 62 + "\n")


if __name__ == "__main__":
    main()