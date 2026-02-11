import google.generativeai as genai
import json
import os

# ---------------------------------------------------------
# 1. ตั้งค่า API Key (เปลี่ยนตรงนี้เป็น Key ของพี่)
# ---------------------------------------------------------
API_KEY = "AIzaSyBVU0cFC9dK1jwf9eqjfRbARhekjk0gDQg"
genai.configure(api_key=API_KEY)

# ---------------------------------------------------------
# 2. ตั้งค่าโมเดล (ใช้ Gemini 2.5 Flash เพื่อความไว)
# ---------------------------------------------------------
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json", # บังคับให้ตอบเป็น JSON เท่านั้น
}

# ---------------------------------------------------------
# 3. ใส่ System Instruction (สมองของ Polaris AI)
# ---------------------------------------------------------
system_instruction = """
Role: คุณคือ "Polaris AI" ผู้เชี่ยวชาญด้านการวิเคราะห์ข่าวสารการลงทุนและหุ้นไทย
Objective: วิเคราะห์ "ข้อความข่าว" ที่ได้รับ และประเมินผลกระทบต่อราคาหุ้นในระยะสั้น

Instructions:
1. อ่านข้อความข่าวที่ได้รับอย่างละเอียด
2. วิเคราะห์ Sentiment (อารมณ์ของข่าว) ว่าส่งผลบวกหรือลบต่อราคาหุ้น
3. ให้คะแนน (Score) ตั้งแต่ -10 ถึง +10
   - (-10) = ข่าวร้ายรุนแรงมาก
   - (0) = ข่าวทั่วไป หรือ ข่าวที่รับรู้ไปแล้ว (Neutral)
   - (+10) = ข่าวดีรุนแรงมาก
4. สรุปเหตุผลสั้นๆ (Reasoning) ไม่เกิน 1 บรรทัด

Output Format: ตอบกลับเป็น JSON เท่านั้น:
{
  "score": [ตัวเลขจำนวนเต็ม],
  "reasoning": "[ข้อความเหตุผล]"
}
"""

# สร้างโมเดลเตรียมไว้
model = genai.GenerativeModel(
  model_name="gemini-2.5-flash",
  generation_config=generation_config,
  system_instruction=system_instruction,
)

# ---------------------------------------------------------
# 4. ฟังก์ชันสำหรับเรียกใช้งาน (Call Function)
# ---------------------------------------------------------
def get_ai_sentiment(news_text):
    """
    รับข้อความข่าว -> ส่งให้ AI -> คืนค่าเป็น Dictionary (Score, Reason)
    """
    try:
        # ส่งข้อความไปให้ AI
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(news_text)
        
        # แปลงข้อความ JSON จาก AI เป็น Python Dictionary
        result = json.loads(response.text)
        return result
    
    except Exception as e:
        print(f"Error AI Analysis: {e}")
        return {"score": 0, "reasoning": "ระบบขัดข้อง วิเคราะห์ไม่ได้"}

# =========================================================
# ส่วนทดสอบการทำงาน (Run Test)
# =========================================================
if __name__ == "__main__":
    # ลองใส่ข่าวจำลองดูครับ
    test_news = "บมจ. XYZ กำไรไตรมาส 2 วูบ 20% เซ่นพิษเศรษฐกิจ แต่บอร์ดยังใจดีปันผลระหว่างกาล 0.50 บาท"
    
    print(f"กำลังวิเคราะห์ข่าว: {test_news} ...")
    analysis = get_ai_sentiment(test_news)
    
    print("-" * 30)
    print(f"คะแนนความน่าสนใจ: {analysis['score']}")
    print(f"เหตุผล: {analysis['reasoning']}")
    print("-" * 30)
# =========================================================
# ส่วนทดสอบการทำงาน (Run Test แบบหลายข่าว)
# =========================================================
if __name__ == "__main__":
    # จำลองรายการข่าวที่ดึงมาจากเว็บ (มีทั้งดี, ร้าย, และเฉยๆ)
    news_list = [
        "PTT พบแหล่งก๊าซใหม่ปริมาณมหาศาล เตรียมขุดเจาะปีหน้า",
        "JMART แจ้งงบขาดทุนยับ เหตุตั้งสำรองหนี้เสียเพิ่มขึ้น 50%",
        "CPALL เปิดสาขาใหม่เพิ่ม 200 แห่ง ยอดขายเติบโตตามเป้า",
        "DELTA ราคาพุ่ง 10% โดยไม่มีข่าวใหม่อย่างเป็นทางการ ตลท.จับตาใกล้ชิด"
    ]

    print(f"กำลังวิเคราะห์ข่าวทั้งหมด {len(news_list)} รายการ...\n")

    for i, news in enumerate(news_list, 1):
        print(f"ข่าวที่ {i}: {news}")
        result = get_ai_sentiment(news) # ส่งข่าวไปให้ AI
        
        # แสดงผล
        print(f"-> คะแนน: {result['score']}")
        print(f"-> เหตุผล: {result['reasoning']}")
        print("-" * 50) # ขีดเส้นคั่นสวยๆ