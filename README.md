# BJT DC Bias Web App

เว็บแอปคำนวณจุดปฏิบัติการ (DC Operating Point) ของวงจรขยาย NPN Common-Emitter แบบ Voltage-Divider Bias สำหรับรายวิชา **ENG29 2121 · Lab 02** (ภาคเรียนที่ 2/2569)

คำนวณทั้งหมดโดย **Python Backend (Flask)** ที่รันบน server `http://127.0.0.1:5000/` — ไม่มีค่าที่ hardcode ไว้ใน HTML/JavaScript และไม่มีการคำนวณฝั่ง browser

## สิ่งที่ต้องมีก่อนเริ่ม

- Python ≥ 3.11 (ทดสอบกับ Python 3.15.2)
- Git (สำหรับ clone repository)
- pip (มาพร้อมกับ Python)

## การติดตั้ง

### Windows (PowerShell / CMD)

```powershell
git clone https://github.com/B6812980Atthakowit/BJT-DC-Bias-Web-App.git
cd BJT-DC-Bias-Web-App

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

### Linux / macOS

```bash
git clone https://github.com/B6812980Atthakowit/BJT-DC-Bias-Web-App.git
cd BJT-DC-Bias-Web-App

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## การรันเว็บแอป

```bash
flask --app app run --debug
```

แล้วเปิดเบราว์เซอร์เข้า:

> **http://127.0.0.1:5000/**

กรอกค่าวงจร (VCC, R1, R2, RC, RE, β, VBE) แล้วกด **Calculate DC Bias** — ผลจะคำนวณจาก Python backend ทุกครั้งที่กด และแสดงผลบนหน้าเดิมพร้อมคำเตือนเมื่อค่าอยู่นอกสมมติฐาน Forward-Active

## การรันแบบทดสอบ (Automated Tests)

```bash
python -m unittest discover -s tests -v
```

ผลที่คาดหวัง: `OK` (19 tests ผ่านทั้งหมด)

ทดสอบครอบคลุม:
- การคำนวณตามสมการ Exact/Thevenin (อ้างอิงค่าจากเอกสาร Lab §6)
- การแปลงหน่วย kΩ → Ω
- การปฏิเสธค่าที่ไม่ใช่ตัวเลข, ค่าติดลบ/ศูนย์, ช่องว่าง, ฟิลด์ขาด
- พื้นที่ทำงาน Cutoff / Saturation พร้อมคำเตือน
- Flask test client: GET /, POST /calculate, รหัสสถานะ 405 สำหรับ method ที่ไม่รองรับ, การคงค่าในฟอร์มหลัง submit ผิดพลาด
- การเปรียบเทียบวิธี Approximate (stiff divider)

## โครงสร้างไฟล์

```
BJT-DC-Bias-Web-App/
├── app.py                      # Flask routes (GET /, POST /calculate)
├── dc_bias.py                  # โมดูลวิศวกรรมบริสุทธิ์ (คำนวณ + validation, ไม่ import Flask)
├── requirements.txt            # Python dependencies (Flask ≥3.0)
├── static/
│   └── style.css               # stylesheet (หน้าตาเว็บ)
├── templates/
│   └── index.html              # Jinja template (ฟอร์ม + ตารางผล + คำเตือน)
├── tests/
│   ├── __init__.py
│   ├── test_dc_bias.py         # unit tests วิศวกรรม (11 tests)
│   └── test_web.py             # Flask test-client tests (8 tests)
├── docs/
│   ├── design-note.md          # โน้ตออกแบบและบันทึกการตัดสินใจ
│   ├── validation.md           # ผลทดสอบจริง + หลักฐานเกณฑ์ A1–A7
│   ├── reflection.md           # โครงคำถามสำหรับนักศึกษาเขียนสะท้อนคิด
│   ├── demo-active.png         # ภาพหน้าเว็บกรณีปกติ (แสดง 2 วิธีคำนวณ)
│   └── demo-cutoff.png         # ภาพหน้าเว็บกรณี Cutoff
└── .gitignore                  # ข้าม .venv/, __pycache__/, *.pyc, .env
```

## ข้อจำกัดของแบบจำลอง (สำคัญ)

- แบบจำลอง **Forward-Active Approximation**: β คงที่, VBE คงที่ (ไม่ใช่ SPICE solver)
- `VCE_sat = 0.2 V` ใช้เป็นค่าตรวจภาวะ saturation
- ผลลัพธ์นอกพื้นที่ทำงาน Forward-Active (Cutoff / Saturation) จะแสดง **พร้อมคำเตือน** และไม่ควรอ้างว่าเป็นค่าจำลองที่แม่นยำทางกายภาพ
- โปรเจกต์นี้อยู่ในขอบเขตสัปดาห์ที่ 2 เท่านั้น: **ไม่มี AC / small-signal / transient / bias type อื่น ๆ**

## เกณฑ์ที่ครอบคลุม (A1–A7)

ดูรายละเอียดใน `docs/validation.md` พร้อมภาพหน้าจอจริงและสรุปผลทดสอบแต่ละเกณฑ์

## หมายเหตุสำหรับการส่งงาน

- ทุกคำอธิบายบนหน้าเว็บเป็น **ภาษาไทย** พร้อม **สัญลักษณ์สากล** (VCC, R1, β, ฯลฯ)
- ทุก commit ทำผ่าน GitHub Desktop โดยตัวนักศึกษาเอง (Human Gate)
- ส่งผ่าน Moodle ด้วย Repository URL + Commit SHA + ภาพหน้าจอ + test log