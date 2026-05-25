import os
import sys
import threading
from datetime import datetime
import pandas as pd
from .models import Enquiry, Appointment, Feedback

# Add LLM module to path
llm_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                      'llm', 'Platinum_Sales_Chatbot-main'))
if llm_path not in sys.path:
    sys.path.insert(0, llm_path)

import test as chatbot_test_module

_chatbot_instance = None
_chatbot_lock = threading.Lock()


def fetch_crm_data_for_chatbot():
    """Fetch live data from PostgreSQL via Django ORM"""
    # Enquiry
    enq_qs = Enquiry.objects.all().values()
    df_enq = pd.DataFrame(list(enq_qs))
    if not df_enq.empty:
        df_enq = df_enq.rename(columns={
            'enquiry_id': 'ENQUIRY ID',
            'customer': 'Customer Name',
            'vehicle': 'Vehicle Name / Model',
            'source': 'Enquiry Source',
            'date': 'Enquiry Date',
            'status': 'Status',
            'temperature': 'Temperature',
        })
        for col in ['Phone Number', 'Email', 'Gender', 'Appointment Date', 
                   'City / State', 'Customer Type', 'Payment Type', 'Test Ride Taken']:
            if col not in df_enq.columns:
                df_enq[col] = ''
    else:
        df_enq = pd.DataFrame(columns=['ENQUIRY ID', 'Customer Name', ...])  # add all needed columns

    # Appointment
    app_qs = Appointment.objects.all().values()
    df_app = pd.DataFrame(list(app_qs))
    if not df_app.empty:
        df_app = df_app.rename(columns={
            'appointment_id': 'Enquiry ID',
            'customer': 'Customer Name',
            'vehicle': 'Vehicle',
            'date': 'Appointment Date',
            'time': 'Time',
            'status': 'Status',
        })

    # Feedback
    fb_qs = Feedback.objects.all().values()
    df_fb = pd.DataFrame(list(fb_qs))
    if not df_fb.empty:
        df_fb = df_fb.rename(columns={
            'enquiry_id': 'Enquiry ID',
            'customer': 'Customer Name',
            'date': 'Date',
            'status': 'Feedback',
        })
        df_fb['Rating'] = 3  # placeholder

    return {
        "Enquiry": df_enq,
        "Appointment": df_app,
        "Feedback": df_fb
    }


def get_chatbot_instance():
    """Singleton pattern for chatbot with live DB data"""
    global _chatbot_instance
    with _chatbot_lock:
        if _chatbot_instance is None:
            print(" Building chatbot retriever from live CRM data...")
            dfs = fetch_crm_data_for_chatbot()
            
            # Update known names
            for df in dfs.values():
                for col in df.columns:
                    if "name" in col.lower():
                        chatbot_test_module._KNOWN_NAMES_SET.update(
                            str(x) for x in df[col].dropna().unique() if str(x).strip()
                        )
            
            docs = chatbot_test_module.build_docs_per_source(dfs)
            retriever = chatbot_test_module.IntelligentRetriever(dfs, docs)
            
            if not chatbot_test_module._llm_ready:
                threading.Thread(target=chatbot_test_module._load_llm, daemon=True).start()
            
            _chatbot_instance = chatbot_test_module.IntelligentSalesChatbot(retriever)
            print(" Chatbot ready with dynamic CRM data!")
    return _chatbot_instance


def process_chat_query(query: str) -> dict:
    """Main function called from views.py"""
    try:
        chatbot = get_chatbot_instance()
        answer, elapsed, intent = chatbot.chat(query)
        
        return {
            "status": "success",
            "response": answer,
            "intent": intent,
            "latency": round(elapsed, 3)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
