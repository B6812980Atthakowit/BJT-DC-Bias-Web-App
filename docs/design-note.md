# Lab 2 Design Note — BJT DC Bias Web App (ENG29 2121 · 2/2569)

วันที่: 2026-11-10 · สถานะ: รออนุมัติจากนักศึกษา

## 1. Intent — เราสร้างอะไร และทำไม

สร้าง **Flask Web Application หลายไฟล์** คำนวณ DC Operating Point ของวงจรขยาย
NPN Common-Emitter แบบ **Voltage-Divider Bias** ให้เสร็จภายในคาบ Lab 2
(180 นาที) เป็น vertical slice แรกของระบบ Virtual Transistor Laboratory
ที่จะต่อยอด W3–W11

เหตุผล: ให้นักศึกษาเห็นความแตกต่างระหว่าง (1) เปิดไฟล์ HTML ตรง ๆ กับ
(2) Web App ที่มี Python Backend คำนวณจริงผ่าน HTTP Request พร้อม Automated
Tests และประวัติ Git — ทุกค่าที่แสดงบนหน้าจอต้องมาจากการคำนวณของโมดูล
วิศวกรรม ไม่ใช่ค่าที่เขียนค้างไว้ใน HTML

## 2. Goals — สิ่งที่ต้องทำให้ได้

- เปิดใช้ผ่าน `http://127.0.0.1:5000/` (Flask dev server) ได้
- ฟอร์มรับ `VCC, R1, R2, RC, RE, β, VBE` → Backend คำนวณและแสดง
  `VB, VE, VC, VCE, IC` พร้อม `IB, IE` และหน่วยกำกับครบ
- Validation: `R ≤ 0`, `β ≤ 0`, `VCC ≤ 0`, ไม่ใช่ตัวเลข หรือขาด → ข้อความ
  error อ่านได้ หน้าเว็บไม่ล้ม
- Region warning: กรณี cutoff (`VTH ≤ VBE`) หรือ saturation (`VCE` ต่ำเกิน
  สมมติฐาน active) → แสดงคำเตือนพร้อมผล ไม่อ้างว่าค่าเชื่อถือได้
- Automated tests: ≥3 unit tests (คณิตศาสตร์วิศวกรรม) + ≥1 test ผ่าน Flask
  test client — รันด้วย `python -m unittest discover -s tests -v`
- README: ผู้อื่น clone แล้วสร้าง venv, ติดตั้ง dependencies, รันเว็บ และรัน
  tests ตามได้โดยไม่ต้องถามเพิ่ม (เกณฑ์ A7)

## 3. Non-goals — ไม่ทำใน Lab นี้ (Week 2 scope)

- ไม่มี AC / small-signal / gain / Bode plot (W5)
- ไม่มี transient / signal generator / knob ความถี่ (W6)
- ไม่มี bias types อื่น เช่น Fixed Bias, Emitter Bias (W3)
- ไม่มี SPICE/ngspice solver (W4)
- ไม่มี interactive schematic / overlay animation (W7)
- UI ตกแต่งระดับพื้นฐานพอ — CSS แยกไฟล์ อ่านง่าย ใช้งานได้ พอ

## 4. Anti-goals — สิ่งที่ถือเป็นความล้มเหลวแม้โปรแกรมรันได้

- Hardcode ค่าผลลัพธ์ใน HTML/JS — ตกเกณฑ์ A2 ทันที
- คำนวณที่ฝั่ง Browser ด้วย JavaScript — ไม่ผ่าน A2/A3
- แสดงผลเมื่อค่าอยู่นอกสมมติฐาน Forward-Active โดยไม่มี warning — ผิด A5
- `.venv/` หรือ secrets ปนขึ้น GitHub

## 5. Constraints — แบบจำลองและสมการที่ใช้

แบบจำลอง **Forward-Active Approximation**: β คงที่, VBE คงที่ (ไม่ใช่ SPICE)

```
VTH = VCC × R2 / (R1 + R2)
RTH = R1·R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
IC  = β·IB          IE = (β+1)·IB
VE  = IE·RE         VB  = VE + VBE
VC  = VCC − IC·RC   VCE = VC − VE
```

เงื่อนไขตรวจ region (ภายใต้แบบจำลองนี้):

- **Cutoff เตือน** เมื่อ `VTH ≤ VBE` (IB ≤ 0 ตามสมการ)
- **Saturation เตือน** เมื่อ `VCE < VCE_sat` โดยใช้ `VCE_sat = 0.2 V`
  เป็นค่าตั้งต้นแสดงผลร่วมกับค่าที่คำนวณได้ พร้อมระบุว่าเป็น approximation
- กรณีผ่านทั้งสองข้อ → "Forward-Active (approximation)"

## 6. Engineering Reference — ค่าอ้างอิงจากการคำนวณอิสระ

ข้อมูลทดลองมาตรฐานของ Lab: `VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ,
RE=1 kΩ, β=100, VBE=0.70 V` คำนวณมือ (สำหรับตรวจรับ A3):

| ปริมาณ | ค่าอ้างอิง |
|---|---|
| VTH | 2.1639 V |
| RTH | 18.0328 kΩ |
| IB | 12.2986 µA |
| IC | 1.2299 mA |
| IE | 1.2422 mA |
| VE | 1.2422 V |
| VB | 1.9422 V |
| VC | 9.2943 V |
| VCE | 8.0522 V |

VCE = 8.05 V > 0.2 V และ VTH > VBE → อยู่ใน Forward-Active region ✓
Unit tests ต้องตรวจค่าเหล่านี้ด้วย tolerance เช่น `±0.1%`
การแสดงผลบนหน้าเว็บใช้รูปแบบ `%.4f` (IC → `1.2299`, VCE → `8.0522`)

## 7. Approaches — ทางเลือกที่พิจารณา

| ทางเลือก | เหตุผลที่ตัด |
|---|---|
| **Flask multi-file** (เลือก) | ผ่านเกณฑ์ A1–A7 ครบ โครงสร้างตรงสเปก Lab ต่อยอด W3–W11 ได้ |
| HTML ไฟล์เดียว + JS คำนวณใน browser | ตก A2/A3 — ไม่มี Python backend, ค่าไม่ผ่าน server |
| Django | ใหญ่เกิน timebox 180 นาที สำหรับ app 1 route 2 หน้า |

การเลือก UI language: **สัญลักษณ์สากล + คำอธิบายภาษาไทย** (นักศึกษาเลือก)
เช่น label `VCC [V] — แรงดันจ่าย`, warning `ตัววงจรอาจเข้าสู่ Saturation...`

## 8. The Build — สิ่งที่ตัดสินใจแล้ว

### โครงสร้างไฟล์ (ที่ root ของ repo นี้)

```
BJT-DC-Bias-Web-App/
├── app.py                  # Flask routes: GET / , POST /calculate
├── dc_bias.py              # ฟังก์ชันคำนวณ+validation (ไม่ import Flask)
├── templates/index.html    # ฟอร์ม + ตารางผลลัพธ์ (Jinja2)
├── static/style.css        # หน้าตาเว็บ
├── tests/
│   ├── test_dc_bias.py     # คณิตศาสตร์ + validation + warning
│   └── test_web.py         # Flask test client: GET/POST เกณฑ์ A1–A5
├── requirements.txt        # Flask
├── README.md               # วิธี setup/รัน/ทดสอบ ตาม A7
├── AGENTS.md               # ข้อตกลงการทำงานกับ AI
├── .gitignore              # .venv/, __pycache__/
└── docs/
    ├── design-note.md      # เอกสารนี้
    ├── validation.md       # หลักฐานการตรวจสอบ (เขียนตอนท้าย Lab)
    └── reflection.md       # สิ่งที่เรียนรู้ (เขียนตอนท้าย Lab)
```

### พฤติกรรมหลัก

- `GET /` → ฟอร์มว่างพร้อมค่าตัวอย่างเป็น placeholder
- `POST /calculate` → `dc_bias.calculate()` คืน dict ผล + warnings หรือ
  errors → render ฟอร์มเดิมพร้อมผลลัพธ์/ข้อความ (ไม่ redirect, ไม่ใช้ JS)
- `dc_bias.py` เป็น pure functions รับพารามิเตอร์ตัวเลข ไม่รู้จัก HTML/HTTP
  เพื่อ test แยกได้และใช้ซ้ำ W3+
- หน่วย: ฟอร์มรับตัวต้านทานเป็น **kΩ** (แปลงเป็น Ω ภายในก่อนคำนวณ),
  แรงดันเป็น V, β ไม่มีหน่วย — ตารางผลแสดงทั้งค่าและหน่วย (IC/IE เป็น mA,
  IB เป็น µA)
- Environment: `python -m venv .venv` → `pip install -r requirements.txt`

## 9. What's left to the builder — ที่ผู้สร้างเลือกได้เอง

- สี/layout ของ CSS (แค่สะอาด อ่านง่าย พอ)
- ถูกเรียง/รูปแบบตารางผลลัพธ์
- ข้อความ error/warning ภาษาไทยถ้อยคำ (คงความหมายตามข้อ 5)
- จำนวน unit tests เพิ่มเติมเกินขั้นต่ำ

## 10. Acceptance — สรุปเกณฑ์ตรวจรับ (จากเอกสาร Lab)

A1 GET / 200 · A2 POST คำนวณจริง · A3 ตรงค่าอ้างอิงข้อ 6 · A4 invalid input
ไม่ล้ม · A5 warning cutoff/saturation · A6 tests ≥3+1 · A7 clone-and-run
ตาม README

**วิธีตรวจรับ (จากเอกสาร Lab):** มนุษย์สาธิตใน Browser + ส่ง Repository URL,
Commit SHA, ภาพหน้าจอเว็บที่คำนวณสำเร็จ และ Test Log ผ่าน Moodle —
**ไม่มี automated grader** ที่เรียก `/calculate` โดยตรง ชื่อ form field,
HTTP status สำหรับ invalid input (เลือก re-render พร้อมข้อความ) และรูปแบบ
ตารางจึงเป็นอิสระตามข้อ 9

**การแบ่งงาน AI/นักศึกษา (ตามหลักของเอกสาร Lab "ใช้ AI ช่วยสร้าง แต่ต้อง
ตรวจสอบเอง"):** AI ร่างโค้ด/tests/README/AGENTS.md เพื่อให้นักศึกษาตรวจ diff
ทุกขั้น · `validation.md` เก็บผลรัน tests จริงเป็นหลักฐาน · **`reflection.md`
นักศึกษาเขียนด้วยคำของตนเอง** (เอกสารเก็บแค่โครงคำถาม) · ทุก commit ทำผ่าน
GitHub Desktop ใน identity ของนักศึกษา
