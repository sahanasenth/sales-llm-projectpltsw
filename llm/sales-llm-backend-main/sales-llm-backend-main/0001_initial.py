def handle_query(query):
    intent, confidence = detect_intent(query)

    if confidence < 0.3:
        return {
            "type": "unknown",
            "value": None,
            "answer": "Sorry, I couldn't clearly understand your query."
        }

    try:
        # ENQUIRIES
        if "enquiries" in intent:
            count = Enquiry.objects.count()
            return {
                "type": "enquiry",
                "value": count,
                "answer": f"There are {count} enquiries recorded."
            }

        # APPOINTMENTS
        elif "appointments" in intent or "meetings" in intent:
            count = Appointment.objects.count()
            return {
                "type": "appointment",
                "value": count,
                "answer": f"There are {count} appointments scheduled."
            }

        # FEEDBACK
        elif "feedback" in intent or "reviews" in intent:
            count = Feedback.objects.count()
            return {
                "type": "feedback",
                "value": count,
                "answer": f"There are {count} feedback entries."
            }

        # CUSTOMERS
        elif "customers" in intent:
            count = Customer.objects.count()
            return {
                "type": "customer",
                "value": count,
                "answer": f"There are {count} customers."
            }

        # SUMMARY
        elif "summary" in intent or "report" in intent:
            summary = generate_summary()
            return {
                "type": "summary",
                "value": summary,
                "answer": (
                    f"Summary:\n"
                    f"Enquiries: {summary['enquiries']}, "
                    f"Appointments: {summary['appointments']}, "
                    f"Feedback: {summary['feedback']}, "
                    f"Customers: {summary['customers']}"
                )
            }

        return {
            "type": "unknown",
            "value": None,
            "answer": "Sorry, I couldn't understand the query."
        }

    except Exception as e:
        return {
            "type": "error",
            "value": None,
            "answer": f"Error: {str(e)}"
        }