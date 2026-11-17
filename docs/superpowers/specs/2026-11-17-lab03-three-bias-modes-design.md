# Lab 03 Design — หนึ่งเว็บ สามวงจรไบอัส (ENG29 2121 · 2/2569)

วันที่: 2026-11-17 · สถานะ: **รอนักศึกษาตรวจอนุมัติก่อนเขียนโค้ด**

## Intent

ต่อยอด Flask app จาก Lab 2 (Voltage Divider วงจรเดียว) ให้เลือกได้ 3 โหมด: Fixed Bias, Emitter Bias (แหล่งจ่ายเดียว), Voltage Divider Bias **โดยผล Divider เดิมต้องไม่เปลี่ยน** (baseline A1 บันทึกไว้แล้วใน `docs/validation.md` ข้อ 0) เพื่อให้ AI ช่วยเขียนตามสมการ แล้วนักศึกษาตรวจสมการ/หน่วย/ผลจากหน้าเว็บจริงตามใบงาน Lab 03

## Goals

- `dc_bias.py` มีฟังก์ชันคำนวณแยกตามโหมด ส่ง `dict` ชื่อคีย์และหน่วยเหมือน `calculate()` เดิม
- `app.py` เลือกฟังก์ชันด้วย `if/elif` ตรวจเฉพาะช่องที่โหมดนั้นใช้ โหมดไม่รู้จัก → error (ไม่เดาเป็น Divider)
- ฟอร์มเลือกโหมดได้ เห็นเฉพาะช่องที่ใช้ ผล/error ระบุโหมด ไม่โชว์ผลรอบก่อน
- ตาราง A1–A5 มีค่าคาดหมายอิสระ หน่วย วิธีตรวจ สถานะ และหลักฐานจากหน้าเว็บ
- 19 tests เดิมยังผ่าน (TDD: เขียน test ใหม่ก่อนโค้ดใหม่)

## Non-goals / Anti-goals

- ไม่ทำ Cutoff/Saturation แบบจริง, SPICE, AC, กราฟ, JavaScript คำนวณ, unittest จำนวนมาก
- ห้ามเปลี่ยนสมการ/พฤติกรรมของ `calculate()` และ `calculate_approximate()` เดิม
- ห้ามคำนวณใน template/JS, ห้าม `dc_bias.py` import Flask
- ห้าม commit/push เอง — Human Gate ผ่าน GitHub Desktop

## Constraints

- V, A, Ω ภายใน · ฟอร์มรับ kΩ (1 MΩ = 1000 kΩ) · แปลงครั้งเดียวตอน parse
- `VCE_SAT = 0.2` V · เตือนเมื่อ `IB ≤ 0` หรือ `VCE ≤ 0.2` สำหรับโหมดใหม่ (Lab 03)
- หมายเหตุ: `calculate()` เดิมใช้ `VTH ≤ VBE` / `VCE < 0.2` — คงไว้เป๊ะเพื่อไม่ให้ 19 tests เสีย
- แสดงผล `"%.4f"|format(...)` เหมือนเดิม IC→mA, IB→µA

## Approaches (ตัดสินแล้ว — เป็น call ของ AI ที่คุณอาจแก้ได้)

1. **สลับโหมด: GET `?mode=` + ปุ่ม "เปลี่ยนโหมด" (เลือก)** — `<form method="get" action="/">` มี select + submit; reload แล้ว render เฉพาะช่องที่ใช้ อ่านง่ายใน browser snapshot ไม่มี JS ทางเลือกอื่น: (ก) disabled ช่องที่ไม่ใช้ → ยังเห็นช่องเกินใน snapshot, (ข) แยก 3 route → เสี่ยงทำให้ Divider เพี้ยน
2. **Tests: คง 19 เดิม + เพิ่ม test ใหม่แบบ TDD จำนวนน้อย (เลือก)** — ใบงานบอก "ไม่ต้องสร้าง unittest ใหม่" ไม่ได้ห้าม และ `AGENTS.md` บอกให้เขียน test ก่อนโค้ด → ผ่านทั้งสองข้อ ทางเลือก: ใช้ 19 เดิมอย่างเดียว (ตรงใบงานแต่ขัด AGENTS.md)
3. **Playwright MCP: NOT RUN** — เครื่องนี้ไม่มี node/npx และไม่มี opencode.json → ใช้ OpenCode Browser ตามวิธีสำรองที่ใบงานอนุญาต ระบุวิธีจริงในตาราง ไม่เพิ่ม Playwright ใน requirements.txt

## สมการและค่าอ้างอิงอิสระ (คำนวณด้วย Fraction จากใบงาน — ไม่ใช้โค้ดแอป)

ใช้ร่วมกัน: VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V

| กรณี | อินพุต | IB | IC | VCE |
|---|---|---|---|---|
| A1 Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | 12.2986 µA | **1.2299 mA** | **8.0522 V** |
| A2 Fixed | RB=1 MΩ | 11.3000 µA | **1.1300 mA** | **9.5140 V** |
| A3 Emitter | RB=1 MΩ, RE=1 kΩ | 10.2634 µA | **1.0263 mA** | **8.7054 V** |
| A4 Emitter | RB=1 MΩ, RE=2 kΩ | 9.4010 µA | **0.9401 mA** | **8.0328 V** |

A4 เทียบ A3: RE เพิ่ม → ตัวหาร `(β+1)RE` เพิ่ม → IB ลด → **IC ลด** (1.0263 → 0.9401 mA)
A5: Fixed RB = 0 → error `RB ต้องมีค่ามากกว่า 0`, ไม่แสดงผล
Tolerance: IC ±0.01 mA, VCE ±0.02 V เทียบค่าก่อนปัด

สมการ: Fixed `IB=(VCC−VBE)/RB, VE=0` · Emitter `IB=(VCC−VBE)/[RB+(β+1)RE], VE=(β+1)IB·RE` · ทั้งคู่ `IC=βIB, VB=VE+VBE, VC=VCC−IC·RC, VCE=VC−VE`

## The Build — ไฟล์ที่จะเปลี่ยน

| ไฟล์ | การเปลี่ยน |
|---|---|
| `dc_bias.py` | เพิ่ม `rb` ใน field map · `parse_inputs(raw, mode="divider")` ตรวจตาม `MODE_FIELDS` (backward-compatible) · `calculate_fixed(values)`, `calculate_emitter(values)` + helper ตรวจ region ร่วม · **ไม่แตะ** `calculate()` / `calculate_approximate()` |
| `app.py` | `GET /` รับ `?mode=` · `POST /calculate` ตรวจ mode → parse ตามโหมด → dispatch · ส่ง `mode`, `result`, `approx` (เฉพาะ divider), `errors`, `form` ไป template |
| `templates/index.html` | select `name="mode"` + ปุ่มเปลี่ยนโหมด (GET) · render field ตามโหมด · แสดงชื่อโหมดในหัวผล/error · แสดง approx เฉพาะ divider + forward-active · ไม่โชว์ result ถ้ามี error |
| `static/style.css` | style selector/ปุ่มเปลี่ยนโหมดเล็กน้อย |
| `tests/test_dc_bias.py`, `tests/test_web.py` | เขียน failing test ก่อน: A2/A3 ค่าอ้างอิง, A4 ทิศทาง, A5 RB=0, mode ไม่รู้จัก, Divider ยังเหมือนเดิม |
| `docs/validation.md`, `README.md` | เติมตาราง A1–A5 + วิธีรัน/ข้อจำกัด Lab 03 |
| `docs/lab03-baseline-a1.jpeg` | ภาพ baseline ที่เก็บไว้แล้ว |

ไม่แตะ `requirements.txt` · ไม่สร้าง `opencode.json`

## หลักการตรวจ region ของโหมดใหม่

- `ib <= 0` → `region="cutoff"` + warning ว่าแบบจำลอง Forward-Active อาจใช้ไม่ได้
- `vce <= VCE_SAT` → `region="saturation"` + warning เดียวกัน
- ผลยังส่งกลับครบ (ไม่ต้องหาค่าจริงใน cutoff/saturation ตามใบงาน)

## Acceptance

รัน `.venv\Scripts\python.exe -m unittest discover -s tests -v` → OK ทุกตัว (19 เดิม + ใหม่) · เปิด browser กรอก A1–A5 จริง เทียบค่าอ้างอิงข้างต้น · ตรวจ A1 ว่ายังได้ 1.2299 mA / 8.0522 V · ตรวจ A4 ว่ากดคำนวณใหม่แล้ว IC เปลี่ยนจริง · หลังนั้นค่อยรายงานเพื่อให้คุณตรวจ diff และ commit เอง
