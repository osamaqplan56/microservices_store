 import json
from app import app 

print("🚀 جاري ضخ بيانات إضافية ورسائل مكثفة لاختبار محرك التحسين...")

with app.test_client() as client:
    # ضخ مجموعة رسائل متتالية لاختبار زر أرشفة الذاكرة الحية (Memory Archiving)
    for i in range(1, 8):
        msg_payload = {
            "sender_id": 1,
            "receiver_id": 2,
            "message_text": f"رسالة فحص ومزامنة رقم {i}: مراجعة بنود الخدمة والملفات المرفقة."
        }
        client.post('/api/messages', data=json.dumps(msg_payload), content_type='application/json; charset=utf-8')
        
    print("🎉 تم ضخ الرسائل بنجاح! توجه للموقع واضغط زر أرشفة الذاكرة لتشاهد الأتمتة.")