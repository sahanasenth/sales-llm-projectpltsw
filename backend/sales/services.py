import os
import sys
import threading
from datetime import datetime
import pandas as pd
from .models import Enquiry, Appointment, Feedback

# Add llm directory to path to import test.py properly without colliding with python's internal test module
llm_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'llm', 'Platinum_Sales_Chatbot-main'))
if llm_dir not in sys.path:
    sys.path.insert(0, llm_dir)

import test as chatbot_test_module

_chatbot_instance = None
_chatbot_lock = threading.Lock()


def fetch_crm_data_for_chatbot():
    # 1. Fetch Enquiry Data
    enquiries = Enquiry.objects.all().values()
    df_enq = pd.DataFrame(list(enquiries))
    if not df_enq.empty:
        df_enq = df_enq.rename(columns={
            'enquiry_id': 'ENQUIRY ID',
            'customer': 'Customer Name',
            'vehicle': 'Vehicle Name / Model',
            'source': 'Enquiry Source',
            'date': 'Enquiry Date',
            'status': 'Status',
        })
        # Add missing columns expected by test.py with empty strings
        for col in ['Phone Number', 'Email', 'Gender', 'Appointment Date', 'City / State', 'Customer Type', 'Payment Type', 'Test Ride Taken']:
            if col not in df_enq.columns:
                df_enq[col] = ''
    else:
        df_enq = pd.DataFrame(columns=['ENQUIRY ID', 'Customer Name', 'Vehicle Name / Model', 'Enquiry Source', 'Enquiry Date', 'Status', 'Phone Number', 'Email', 'Gender', 'Appointment Date', 'City / State', 'Customer Type', 'Payment Type', 'Test Ride Taken'])

    # 2. Fetch Appointment Data
    appointments = Appointment.objects.all().values()
    df_app = pd.DataFrame(list(appointments))
    if not df_app.empty:
        df_app = df_app.rename(columns={
            'appointment_id': 'Enquiry ID',  # test.py expects Enquiry ID
            'customer': 'Customer Name',
            'vehicle': 'Vehicle',
            'date': 'Appointment Date',
            'time': 'Time',
            'status': 'Status',
        })
    else:
        df_app = pd.DataFrame(columns=['Enquiry ID', 'Customer Name', 'Vehicle', 'Appointment Date', 'Time', 'Status'])

    # 3. Fetch Feedback Data
    feedbacks = Feedback.objects.all().values()
    df_fb = pd.DataFrame(list(feedbacks))
    if not df_fb.empty:
        df_fb = df_fb.rename(columns={
            'enquiry_id': 'Enquiry ID',
            'customer': 'Customer Name',
            'date': 'Date',
            # Model lacks feedback/rating, using status as a placeholder
            'status': 'Feedback',
        })
        df_fb['Rating'] = 3  # Dummy rating since it's not in the model
    else:
        df_fb = pd.DataFrame(columns=['Enquiry ID', 'Customer Name', 'Date', 'Feedback', 'Rating'])

    return {
        "Enquiry": df_enq,
        "Appointment": df_app,
        "Feedback": df_fb
    }


def get_chatbot_instance():
    """
    Returns a cached, thread-safe instance of the IntelligentSalesChatbot.
    This provides massive performance gains over rebuilding the index every time.
    """
    global _chatbot_instance
    with _chatbot_lock:
        dfs = fetch_crm_data_for_chatbot()
        # Populate KNOWN_NAMES_SET for better intent recognition
        for src_df in dfs.values():
            for col in src_df.columns:
                if "name" in col.lower() and not col.startswith("__"):
                    chatbot_test_module._KNOWN_NAMES_SET.update(
                        n for n in src_df[col].dropna().astype(str).unique()
                        if n not in ("nan", "None", "")
                    )
        
        docs_per_source = chatbot_test_module.build_docs_per_source(dfs)
        retriever = chatbot_test_module.IntelligentRetriever(dfs, docs_per_source)
        
        # Start LLM loading in background if not already ready
        if not chatbot_test_module._llm_ready:
            threading.Thread(target=chatbot_test_module._load_llm, daemon=True).start()
            
        _chatbot_instance = chatbot_test_module.IntelligentSalesChatbot(retriever)
    return _chatbot_instance


def process_chat_query(query: str) -> dict:
    """
    Handles the chatbot execution and wraps the response with expanded metadata.
    """
    chatbot = get_chatbot_instance()
    answer, elapsed, intent = chatbot.chat(query)
    
    # Calculate dataset sizes for metadata
    dfs = fetch_crm_data_for_chatbot()
    enquiries_count = len(dfs["Enquiry"])
    appointments_count = len(dfs["Appointment"])
    feedbacks_count = len(dfs["Feedback"])

    return {
        "status": "success",
        "query": query,
        "response": answer,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "records_used": {
                "enquiries": enquiries_count,
                "appointments": appointments_count,
                "feedback": feedbacks_count
            },
            "intent": intent,
            "latency_seconds": round(elapsed, 3)
        }
    }
