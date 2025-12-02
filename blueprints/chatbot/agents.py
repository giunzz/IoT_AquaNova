import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai.chat import OpenAIChat

# Import hàm kết nối DB
try:
    from firebase_admin_init import get_db
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from firebase_admin_init import get_db

load_dotenv()

# --- HÀM HỖ TRỢ ---
def safe_json_dump(data):
    """Chuyển đổi dữ liệu sang JSON (Dùng cho hàm get_current_sensors)."""
    def converter(o):
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        return str(o)
    return json.dumps(data, default=converter, ensure_ascii=False)

# --- TOOL 1: LẤY CẢM BIẾN (Giữ nguyên JSON để Agent dễ đọc số) ---
def get_current_sensors() -> str:
    """
    Lấy thông số nhiệt độ và độ đục hiện tại.
    """
    try:
        db = get_db()
        docs = db.collection('readings').order_by('ts', direction='DESCENDING').limit(1).stream()
        
        latest = None
        for doc in docs: latest = doc.to_dict()
            
        if latest:
            return safe_json_dump({
                "temperature": latest.get('temperature'),
                "turbidity": latest.get('turbidity'),
                "time": latest.get('ts')
            })
        return "Không có dữ liệu cảm biến."
    except Exception as e:
        return f"Lỗi đọc cảm biến: {str(e)}"

def get_average_temperature() -> str:
    """
    Tính nhiệt độ trung bình từ 10 mẫu dữ liệu gần nhất.
    Sử dụng khi người dùng hỏi về: nhiệt độ trung bình, nhiệt độ chung.
    """
    try:
        db = get_db()
        # Lấy 10 bản ghi gần nhất
        docs = db.collection('readings').order_by('ts', direction='DESCENDING').limit(10).stream()
        
        temps = []
        for doc in docs:
            data = doc.to_dict()
            if 'temperature' in data:
                temps.append(float(data['temperature']))
        
        if not temps:
            return "Không có dữ liệu để tính trung bình."
            
        avg_temp = sum(temps) / len(temps)
        return f"{avg_temp:.2f}" # Trả về số trung bình chính xác
    except Exception as e:
        return "Lỗi tính toán"


# --- TOOL 2: DỰ BÁO THAY NƯỚC (SỬA ĐỔI: TRẢ VỀ VĂN BẢN THUẦN) ---
def predict_maintenance() -> str:
    """
    Dự báo chính xác thời điểm cần thay nước.
    Trả về câu trả lời văn bản tiếng Việt rõ ràng, không chứa JSON.
    """
    try:
        db = get_db()
        # Lấy 20 mẫu gần nhất
        docs = db.collection('readings').order_by('ts', direction='DESCENDING').limit(20).stream()
        records = [doc.to_dict() for doc in docs]
        
        if len(records) < 5:
            return "Hiện tại hệ thống chưa thu thập đủ dữ liệu để dự báo. Vui lòng đợi thêm một lát."

        # Sắp xếp theo thời gian
        records.sort(key=lambda x: str(x.get('ts', '')))

        # Chuẩn bị dữ liệu tính toán
        x_time = []
        y_turb = []
        start_time = None
        latest_time = None
        
        for r in records:
            ts_val = r.get('ts') or r.get('timestamp')
            tur_val = r.get('turbidity')
            if not ts_val or tur_val is None: continue

            try:
                if isinstance(ts_val, str):
                    dt = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                else:
                    dt = ts_val
                dt = dt.replace(tzinfo=None)
                
                if start_time is None: start_time = dt
                
                hours = (dt - start_time).total_seconds() / 3600.0
                x_time.append(hours)
                y_turb.append(float(tur_val))
                latest_time = dt
            except:
                continue

        if len(x_time) < 5: return "Dữ liệu bị lỗi, không thể tính toán dự báo."

        # Tính Linear Regression (Tìm độ dốc a)
        n = len(x_time)
        sum_x = sum(x_time)
        sum_y = sum(y_turb)
        sum_xy = sum(x*y for x,y in zip(x_time, y_turb))
        sum_xx = sum(x*x for x in x_time)
        
        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0: slope = 0
        else: slope = (n * sum_xy - sum_x * sum_y) / denominator

        current_turb = y_turb[-1]
        THRESHOLD = 250.0 # Ngưỡng thay nước

        # --- TẠO CÂU TRẢ LỜI TỰ NHIÊN (TEXT ONLY) ---
        
        if current_turb >= THRESHOLD:
            return f"CẢNH BÁO KHẨN CẤP: Độ đục hiện tại là {current_turb:.1f} NTU đã vượt mức an toàn. Bạn cần thay nước ngay lập tức!"

        if slope <= 0.1:
            return f"Chất lượng nước hiện tại rất ổn định ({current_turb:.1f} NTU). Chưa cần thay nước trong thời gian tới."
        
        # Tính toán deadline
        hours_left = (THRESHOLD - current_turb) / slope
        deadline = latest_time + timedelta(hours=hours_left)
        deadline_str = deadline.strftime("%H giờ %M phút, ngày %d/%m/%Y")
        
        days_left = hours_left / 24.0
        
        if days_left > 30:
            return f"Nước vẫn rất sạch ({current_turb:.1f} NTU). Dự kiến hơn 1 tháng nữa mới cần thay."
            
        # Câu trả lời chốt hạ
        return (f"Theo phân tích xu hướng, độ đục đang tăng dần. "
                f"Dự kiến bạn cần thay nước trước {deadline_str} "
                f"(tức là khoảng {days_left:.1f} ngày nữa).")

    except Exception as e:
        return "Xin lỗi, hệ thống gặp lỗi khi tính toán dự báo."

# --- CẤU HÌNH AGENT ---
model = OpenAIChat(
    id="moonshotai/kimi-k2-instruct-0905",
    api_key=os.getenv("GROQ_API_KEY"),
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
   - Call get_average_temperature() for average temperature or turbidity inquiries.
3. HALLUCINATION CHECK: Never invent data. If tools return "Error" or "No data", report that honestly.
4. RESPONSE:
   - Answer in VIETNAMESE (Tiếng Việt).
   - Tone: Professional, helpful, friendly.
   - Safety Checks:
     - If Temperature > 32°C or < 20°C: Add a health warning.
     - If Turbidity > 250 NTU: Add a water quality warning.

Example User:"Nhiệt độ bể cá bao nhiêu?"
Example Tool Output:`{"temperature": 28.5}'
Example Response:"Nhiệt độ hiện tại của bể là 28.5°C, mức này rất tốt cho cá phát triển ạ."

CRITICAL RESTRICTIONS
- Do not mix JSON commands with text. It's either JSON (Mode 1) OR Text (Mode 2).
- Always prioritize user safety and fish health.
"""
aqua_agent = Agent(
    name="AquaNova Smart Agent",
    model=model,
    tools=[get_current_sensors, predict_maintenance, get_average_temperature], 
    system_message=system_prompt,
    markdown=True, 
    debug_mode=True
)