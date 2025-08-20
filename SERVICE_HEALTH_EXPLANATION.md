# 🔍 Service Health Alerts คืออะไร - อธิบายเชิงลึก

**วันที่**: 2025-07-12 15:55  
**Service Health Monitor**: ระบบแจ้งเตือน Service down/recovery แยกจาก VM

---

## 🎯 **Service Health Alerts คืออะไร?**

**Service Health Alerts** = ระบบแจ้งเตือนเมื่อ **บริการ/แอปพลิเคชัน** มีปัญหา **ไม่ใช่ VM**

### 🔍 **ความแตกต่าง VM vs Service**:

| **VM Monitoring** | **Service Monitoring** |
|------------------|----------------------|
| ตรวจสอบเครื่อง Virtual Machine | ตรวจสอบแอปพลิเคชัน/บริการ |
| CPU, Memory, Disk, Power | API Response, Database, Features |
| VM offline/online | Service down/working |
| Infrastructure Level | Application Level |

---

## 🏗️ **Services ที่ตรวจสอบ (5 บริการ)**

### 1. **Carbon Footprint (UAT)**
- **URL**: `https://uat-carbonfootprint.one.th/api/v2/health`
- **ตรวจสอบ**: API response, Database connection, Sub-modules
- **Function**: ระบบคำนวณ Carbon Footprint สำหรับ testing

### 2. **Carbon Footprint (PRD)** 
- **URL**: `https://prd-carbonfootprint.one.th/api/v2/health`
- **ตรวจสอบ**: API response, Database connection, Sub-modules  
- **Function**: ระบบคำนวณ Carbon Footprint สำหรับ production

### 3. **E-Tax Software**
- **URL**: `http://10.0.0.223/api/health`
- **ตรวจสอบ**: Authentication, Tax processing, Report generation
- **Function**: ระบบจัดการภาษี

### 4. **Rancher Management**
- **URL**: `http://192.168.1.101/api/health`  
- **ตรวจสอบ**: Cluster API, Kubernetes API, Management UI
- **Function**: ระบบจัดการ Container/Kubernetes

### 5. **Database Cluster**
- **URL**: `http://192.168.10.21/api/health`
- **ตรวจสอบ**: PostgreSQL, MongoDB, Redis
- **Function**: ระบบฐานข้อมูลหลัก

---

## ⚙️ **วิธีการทำงาน Service Health Monitor**

### 📁 **ไฟล์หลัก**: `service_health_monitor.py`

### 🔄 **Algorithm**:
```python
def check_service_health():
    # 1. เรียก API เพื่อดูสถานะ services
    response = requests.get("http://192.168.20.10:5000/api/services")
    current_status = response.json()
    
    # 2. โหลดสถานะครั้งก่อน
    previous_status = load_last_status("last_service_status.json")
    
    # 3. เปรียบเทียบการเปลี่ยนแปลง
    for service_name, service_data in current_status['services'].items():
        current_health = service_data['health_level']  # healthy/warning/critical
        previous_health = previous_status.get(service_name, {}).get('health_level')
        
        # 4. ตรวจจับการเปลี่ยนแปลง
        if previous_health != current_health:
            if current_health == 'critical':
                send_line_alert(f"🚨 {service_data['name']} DOWN!")
            elif previous_health == 'critical' and current_health in ['healthy', 'warning']:
                send_line_alert(f"✅ {service_data['name']} BACK ONLINE!")
    
    # 5. บันทึกสถานะใหม่
    save_current_status(current_status)
```

### 📊 **Service Status Levels**:
- **`healthy`**: ✅ บริการทำงานปกติ
- **`warning`**: ⚠️ บริการทำงานแต่ช้า/มีปัญหาเล็กน้อย  
- **`critical`**: 🔴 บริการไม่ทำงาน/error

---

## 📱 **ตัวอย่างข้อความ LINE ที่จะได้รับ**

### 🚨 **Service Down Alert**:
```
🚨 Service Health Alert
🕒 Time: 2025-07-12 15:30:00
🖥️ System: One Climate Infrastructure
📊 Level: CRITICAL
🔴 URGENT: 1 SERVICE(S) DOWN!

- E-Tax Software (error)
  Response: 5000ms
  Database: Disconnect
  Error: Connection timeout

🔗 Dashboard: http://192.168.20.10:5000/mobile
```

### ✅ **Service Recovery Alert**:
```
✅ Service Recovery Alert
🕒 Time: 2025-07-12 15:32:00
🖥️ System: One Climate Infrastructure  
📊 Level: INFO
🟢 RECOVERED: 1 SERVICE(S) BACK ONLINE!

- E-Tax Software (ok)
  Response: 150ms
  Database: Connect
  Uptime: 2m15s

🔗 Dashboard: http://192.168.20.10:5000/mobile
```

### ⚠️ **Service Warning Alert**:
```
⚠️ Service Performance Alert
🕒 Time: 2025-07-12 15:45:00
📊 Level: WARNING
🟡 SLOW RESPONSE: 1 SERVICE(S)

- Rancher Management (warning)
  Response: 2500ms (slow)
  Database: Connect (high latency)
  
🔗 Dashboard: http://192.168.20.10:5000/mobile
```

---

## 🕒 **Cron Schedule**

```bash
*/2 * * * * /usr/bin/python3 service_health_monitor.py
# ทุก 2 นาที = 720 ครั้งต่อวัน
```

### **ทำไมถึงตรวจทุก 2 นาที?**
- **Fast Detection**: รู้ทันทีเมื่อ service down (ไม่เกิน 2 นาที)
- **Business Critical**: Services เหล่านี้สำคัญต่อธุรกิจ
- **Smart Alerts**: ส่งแจ้งเตือน**เฉพาะเมื่อมีการเปลี่ยนแปลง**

---

## 🎯 **ประโยชน์ของ Service Health Alerts**

### 1. **แยกจาก VM Monitoring**:
- VM อาจ online แต่ service อาจ down
- ตัวอย่าง: VM ทำงานปกติ แต่ database connection หลุด

### 2. **Business Impact Focus**:
- แจ้งเตือนปัญหาที่ส่งผลต่อผู้ใช้จริง
- ไม่ใช่แค่ infrastructure metrics

### 3. **Faster Response**:
- รู้ปัญหาภายใน 2 นาที
- แก้ไขได้เร็วกว่า user ร้องเรียน

### 4. **Historical Tracking**:
- ติดตาม service uptime
- วิเคราะห์ pattern ของปัญหา

---

## 📊 **Status ปัจจุบัน (ตอนนี้)**

```json
{
  "carbon_footprint_uat": "healthy",     // ✅ ทำงานปกติ
  "carbon_footprint_prd": "healthy",     // ✅ ทำงานปกติ  
  "etax_software": "healthy",             // ✅ ทำงานปกติ
  "rancher_management": "warning",        // ⚠️ ตอบสนองช้า
  "database_cluster": "healthy"           // ✅ ทำงานปกติ
}
```

**Overall Status**: ⚠️ Warning (เพราะ Rancher ช้า)  
**Services Down**: 0  
**Availability**: 80% (4/5 healthy)

---

## 🎊 **สรุป**

**E-Tax Software DOWN/BACK ONLINE** = ตัวอย่างข้อความแจ้งเตือนเมื่อ:
- 🔴 **E-Tax Software service หยุดทำงาน** (API ไม่ตอบสนอง/error)
- ✅ **E-Tax Software กลับมาทำงานปกติ** (API ตอบสนองแล้ว)

**ไม่ใช่ VM down** แต่เป็น **Application/Service level monitoring** ที่แม่นยำและมีประโยชน์มากกว่า! 🎯