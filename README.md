# BJT DC Bias Web App

เว็บแอปคำนวณจุดปฏิบัติการ (DC Operating Point) ของวงจรขยาย NPN Common-Emitter **3 รูปแบบไบอัส** — Fixed Bias, Emitter Bias (แหล่งจ่ายเดียว) และ Voltage-Divider Bias สำหรับรายวิชา **ENG29 2121 · Lab 02–03** (ภาคเรียนที่ 2/2569)

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

**ขั้นตอนเลือกวงจร:** ที่กล่อง "เลือกวงจรไบอัส" ให้เลือกโหมดจาก dropdown แล้วกด **เปลี่ยนโหมด** — ฟอร์มจะแสดงเฉพาะช่องที่โหมดนั้นใช้

| โหมด | ช่องอินพุต | สมการหลัก |
|---|---|---|
| Fixed Bias | VCC, RB, RC, β, VBE | `IB = (VCC − VBE)/RB`, `VE = 0` |
| Emitter Bias | VCC, RB, RC, RE, β, VBE | `IB = (VCC − VBE)/[RB + (β+1)RE]` |
| Voltage Divider Bias | VCC, R1, R2, RC, RE, β, VBE | Exact/Thevenin (§6 ของ Lab 02) |

กรอกค่า (ตัวต้านทานหน่วย kΩ, 1 MΩ = 1000 kΩ) แล้วกด **Calculate DC Bias** — ผลจะคำนวณจาก Python backend ทุกครั้งที่กด และแสดงผลบนหน้าเดิมพร้อมคำเตือนเมื่อค่าอยู่นอกสมมติฐาน Forward-Active · ถ้ามี error หน้าเว็บจะไม่แสดงผลรอบก่อน

## การรันแบบทดสอบ (Automated Tests)

```bash
python -m unittest discover -s tests -v
```

ผลที่คาดหวัง: `OK` (37 tests ผ่านทั้งหมด)

ทดสอบครอบคลุม:
- การคำนวณตามสมการ Exact/Thevenin (อ้างอิงค่าจากเอกสาร Lab §6)
- Fixed Bias และ Emitter Bias (ค่าอ้างอิง A2–A4) รวมถึงทิศทางที่ถูกต้องเมื่อเพิ่ม RE
- การแปลงหน่วย kΩ → Ω (รวม RB = 1 MΩ = 1000 kΩ)
- การปฏิเสธค่าที่ไม่ใช่ตัวเลข, ค่าติดลบ/ศูนย์, ช่องว่าง, ฟิลด์ขาด, โหมดที่ไม่รู้จัก
- พื้นที่ทำงาน Cutoff / Saturation พร้อมคำเตือน
- Flask test client: GET / (ตามโหมด), POST /calculate, รหัสสถานะ 405 สำหรับ method ที่ไม่รองรับ, การคงค่าในฟอร์มหลัง submit ผิดพลาด, การไม่แสดงผลรอบก่อนเมื่อ error
- การเปรียบเทียบวิธี Approximate (stiff divider) ซึ่งแสดงเฉพาะโหมด Divider

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
│   ├── test_dc_bias.py         # unit tests วิศวกรรม (21 tests)
│   └── test_web.py             # Flask test-client tests (16 tests)
├── docs/
│   ├── design-note.md          # โน้ตออกแบบและบันทึกการตัดสินใจ
│   ├── validation.md           # ผลทดสอบจริง + หลักฐานเกณฑ์ A1–A7 (Lab 02) และ A1–A5 (Lab 03)
│   ├── reflection.md           # โครงคำถามสำหรับนักศึกษาเขียนสะท้อนคิด
│   ├── demo-active.png         # ภาพหน้าเว็บกรณีปกติ (แสดง 2 วิธีคำนวณ)
│   ├── demo-cutoff.png         # ภาพหน้าเว็บกรณี Cutoff
│   ├── lab03-baseline-a1.jpeg  # Baseline Divider ก่อนเพิ่มโหมด (A1)
│   └── lab03-a3-emitter.jpeg   # ภาพผล Emitter Bias (A3)
└── .gitignore                  # ข้าม .venv/, __pycache__/, *.pyc, .env
```

## ข้อจำกัดของแบบจำลอง (สำคัญ)

- แบบจำลอง **Forward-Active Approximation**: β คงที่, VBE คงที่ (ไม่ใช่ SPICE solver)
- `VCE_sat = 0.2 V` ใช้เป็นค่าตรวจภาวะ saturation
- ผลลัพธ์นอกพื้นที่ทำงาน Forward-Active (Cutoff / Saturation) จะแสดง **พร้อมคำเตือน** และไม่ควรอ้างว่าเป็นค่าจำลองที่แม่นยำทางกายภาพ
- โปรเจกต์นี้อยู่ในขอบเขต Lab 02–03 เท่านั้น: มี **3 รูปแบบไบอัส** (Fixed / Emitter / Voltage Divider) แต่ยัง **ไม่มี AC / small-signal / transient / SPICE / กราฟ**
- ค่าที่แสดงเป็นผลของแบบจำลอง Forward-Active ที่ β และ VBE คงที่ — ใช้เพื่อการเรียนรู้ ไม่ใช่ค่าที่รับประกันตรงกับวงจรจริง
- โหมด Fixed/Emitter เตือนเมื่อ `IB ≤ 0` (Cutoff) หรือ `VCE ≤ 0.2 V` (Saturation) · โหมด Divider คงกฎเดิมของ Lab 02 ทุกประการ

## เกณฑ์ที่ครอบคลุม

- **Lab 02:** A1–A7 (ดู `docs/validation.md` §1–§5)
- **Lab 03:** A1–A5 (Divider ไม่เปลี่ยน, Fixed/Emitter ค่าอ้างอิงถูก, A4 IC ลดเมื่อเพิ่ม RE, A5 error เมื่อ RB=0) — ดู `docs/validation.md` §6–§7

## หมายเหตุสำหรับการส่งงาน

- ทุกคำอธิบายบนหน้าเว็บเป็น **ภาษาไทย** พร้อม **สัญลักษณ์สากล** (VCC, R1, β, ฯลฯ)
- ทุก commit ทำผ่าน GitHub Desktop โดยตัวนักศึกษาเอง (Human Gate)
- ส่งผ่าน Moodle ด้วย Repository URL + Commit SHA + ภาพหน้าจอ + test log