import os
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai.chat import OpenAIChat
from firebase_admin import firestore

load_dotenv()

# --- HELPER FUNCTION: DATA SERIALIZATION ---
def safe_json_dump(data):
    """Safely convert data to JSON string, handling datetime objects."""
    def converter(o):
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(o, 'isoformat'): # Handle Firestore Timestamp
            return o.isoformat()
        return str(o)
        
    return json.dumps(data, default=converter, ensure_ascii=False)

# --- PART 1: DEFINE TOOLS ---

def get_current_sensors() -> str:
    """
    Retrieves the latest sensor data (Temperature, Turbidity) from Firestore.
    Use this tool when the user asks for current status, water quality, or sensor readings.
    """
    try:
        db = firestore.client()
        docs = db.collection('telemetry').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).stream()
        
        data = None
        for doc in docs:
            data = doc.to_dict()
            
        if data:
            return safe_json_dump(data)
        else:
            return "System has not recorded any sensor data yet."
    except Exception as e:
        return f"Error reading database: {str(e)}"

def predict_maintenance() -> str:
    """
    Analyzes historical data to predict water change schedule based on turbidity trends.
    Use this tool when the user asks about maintenance, cleaning prediction, or water change schedule.
    """
    try:
        db = firestore.client()
        # Get last 20 samples
        docs = db.collection('telemetry').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20).stream()
        records = [doc.to_dict() for doc in docs]
        
        if not records or len(records) < 2:
            return "Insufficient historical data for prediction."

        # Get latest and oldest records in the batch
        current_record = records[0]
        past_record = records[-1]
        
        current_turbidity = current_record.get('turbidity', 0)
        past_turbidity = past_record.get('turbidity', 0)
        
        # Parse timestamps
        t1 = current_record.get('timestamp')
        t2 = past_record.get('timestamp')
        
        # Handle string or datetime objects
        if isinstance(t1, str): t1 = datetime.fromisoformat(t1.replace('Z', '+00:00'))
        if isinstance(t2, str): t2 = datetime.fromisoformat(t2.replace('Z', '+00:00'))
        
        if hasattr(t1, 'to_datetime'): t1 = t1.to_datetime()
        if hasattr(t2, 'to_datetime'): t2 = t2.to_datetime()
        
        if isinstance(t1, datetime) and isinstance(t2, datetime):
            t1 = t1.replace(tzinfo=None)
            t2 = t2.replace(tzinfo=None)
            time_diff = (t1 - t2).total_seconds() / 3600
        else:
            time_diff = 1
            
        if time_diff <= 0: time_diff = 0.1

        # Calculate growth rate
        growth_rate = (current_turbidity - past_turbidity) / time_diff
        threshold = 100 
        
        # Analyze
        if current_turbidity >= threshold:
            return f"CRITICAL WARNING: Water is very dirty ({current_turbidity} NTU). Change water IMMEDIATELY!"
            
        if growth_rate <= 0:
             return safe_json_dump({
                "current_turbidity": current_turbidity,
                "status": "Good",
                "message": "Water quality is stable or improving. No maintenance needed yet."
            })
            
        remaining = threshold - current_turbidity
        hours_left = remaining / growth_rate
        days_left = hours_left / 24
        
        return safe_json_dump({
            "current_turbidity": current_turbidity,
            "growth_rate": f"{growth_rate:.2f} NTU/h",
            "prediction": f"Approximately {days_left:.1f} days left until water change is needed."
        })

    except Exception as e:
        print(f"Prediction Error: {e}")
        return f"Error calculating prediction: {str(e)}"

# --- PART 2: CONFIGURE AGENT ---

model = OpenAIChat(
    id="moonshotai/kimi-k2-instruct-0905",
    api_key=os.getenv("GROQ_API_KEY")
    base_url="https://api.groq.com/openai/v1"
)


system_prompt = """
You are the AquaNova Smart Controller, an advanced AI agent managing an IoT Fish Monitoring System.

 CORE OBJECTIVE
Your goal is to either CONTROL hardware devices or ADVISE the user based on real-time data. You must understand the user's intent in Vietnamese and act accordingly.

 MODES OF OPERATION

MODE 1: DEVICE CONTROL (Command Execution)
If the user wants to change the state of a device (turn on/off light, feed fish), you act as a silent controller.
RULES:
1. Do NOT output any conversational text.
2. Output ONLY a single JSON object corresponding to the command.
3. Recognized Commands:
   - **Turn ON Light:`{"light": 1}`
   - **Turn OFF Light:`{"light": 0}`
   - **Feed Fish:`{"feeding": 1}`

Example User: "Bật đèn lên giúp tôi"
Example Output: `{"light": 1}`

MODE 2: ADVISORY & MONITORING (Information Retrieval)
If the user asks for information (temperature, turbidity, water status, predictions), you act as an intelligent consultant.
PROTOCOL:
1. THOUGHT PROCESS: Identify which data is needed.
2. TOOL USAGE:
   - Call `get_current_sensors` for real-time readings (Temperature, Turbidity).
   - Call `predict_maintenance` for trends and water change schedules.
3. HALLUCINATION CHECK: Never invent data. If tools return "Error" or "No data", report that honestly.
4. RESPONSE:
   - Answer in VIETNAMESE (Tiếng Việt).
   - Tone: Professional, helpful, friendly.
   - Safety Checks:
     - If Temperature > 32°C or < 20°C: Add a health warning.
     - If Turbidity > 250 NTU: Add a water quality warning.

Example User:"Nhiệt độ bể cá bao nhiêu?"
Example Tool Output:`{"temperature": 28.5, "turbidity": 45}`
Example Response:"Nhiệt độ hiện tại của bể là 28.5°C, mức này rất tốt cho cá phát triển ạ."

CRITICAL RESTRICTIONS
- Do not mix JSON commands with text. It's either JSON (Mode 1) OR Text (Mode 2).
- Always prioritize user safety and fish health.
"""

aqua_agent = Agent(
    name="AquaNova Smart Agent",
    model=model,
    tools=[get_current_sensors, predict_maintenance], 
    system_message=system_prompt,
    markdown=True, 
    debug_mode=True
)