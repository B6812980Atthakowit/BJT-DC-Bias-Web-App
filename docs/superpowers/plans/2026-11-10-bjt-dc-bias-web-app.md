# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web App คำนวณ DC Bias ของวงจร BJT NPN Common-Emitter แบบ Voltage-Divider Bias ที่รันที่ `http://127.0.0.1:5000/` ได้ พร้อม automated tests

**Architecture:** แยกชั้นชัดเจน — `dc_bias.py` เป็น pure functions (ไม่ import Flask) ทำการคำนวณ+validation · `app.py` เป็น Flask routes เรียกใช้ · `templates/index.html` + `static/style.css` แสดงผลอย่างเดียว ไม่มีการคำนวณใน JavaScript

**Tech Stack:** Python 3.15, Flask ≥3.0, unittest (built-in), Jinja2 (มากับ Flask)

**Spec:** `docs/design-note.md` — executor ต้องอ่านพร้อมแผนนี้ (สมการ, ค่าอ้างอิง, เกณฑ์ A1–A7 อยู่ใน spec)

## Global Constraints

- สมการ (spec §5 เป๊ะ): `VTH = VCC×R2/(R1+R2)`, `RTH = R1·R2/(R1+R2)`, `IB = (VTH−VBE)/(RTH+(β+1)RE)`, `IC = β·IB`, `IE = (β+1)·IB`, `VE = IE·RE`, `VB = VE+VBE`, `VC = VCC−IC·RC`, `VCE = VC−VE`
- `VCE_SAT = 0.2` V เป็นค่าคงที่ใน `dc_bias.py`
- ฟอร์มรับตัวต้านทานหน่วย **kΩ** → `parse_inputs` แปลงเป็น Ω ก่อนคำนวณ (แรงดันเป็น V, β ไม่มีหน่วย)
- `dc_bias.py` **ห้าม import flask**; หน่วยภายในเป็น SI (V, A, Ω) แปลงเป็น mA/µA/kΩ เฉพาะตอนแสดงผลใน template
- Invalid input → **re-render หน้าเดิม** พร้อมข้อความ error (HTTP 200) หน้าเว็บไม่ล้ม
- ค่าอ้างอิง (spec §6): IC = 1.2299 mA, IE = 1.2422 mA, IB = 12.2986 µA, VE = 1.2422 V, VB = 1.9422 V, VC = 9.2943 V, VCE = 8.0522 V, VTH = 2.1639 V, RTH = 18.0328 kΩ
- การแสดงผลตัวเลขใน template ใช้ `"%.4f"|format(...)`
- รันเทส: `.venv\Scripts\python.exe -m unittest discover -s tests -v` (Windows)
- รันเว็บ: `.venv\Scripts\python.exe -m flask --app app run --debug` → `http://127.0.0.1:5000/`
- ห้าม commit `.venv/`, `__pycache__/`, `.env`
- **ทุก commit เป็น Human Gate**: executor เสร็จงาน task → หยุดรายงานผล tests → นักศึกษาตรวจ diff และ commit ผ่าน GitHub Desktop เอง → executor ยืนยันด้วย `git log` ก่อนไป task ถัดไป

## Review Focus

1. **ชุดพารามิเตอร์อื่นต้องคำนวณถูก (กันผล hardcode)** → Task 1 `test_second_parameter_set_is_not_hardcoded`
2. **ช่องที่เว้นวรรคล้วน `"  "`** ต้องถูกปฏิเสธเป็น non-numeric ไม่ใช่ crash → Task 1 `test_rejects_whitespace_only`
3. **ขาดเพียงฟิลด์เดียว** error ต้องระบุชื่อฟิลด์นั้น → Task 1 `test_rejects_missing_field`
4. **ค่าที่ผู้ใช้กรอกต้องอยู่คงเดิมหลัง submit ผิดพลาด** (ไม่หายไปจากฟอร์ม) → Task 2 `test_post_invalid_keeps_form_values`
5. **`GET /calculate` (method ผิด)** ต้องได้ 405 ไม่ใช่ 500 → Task 2 `test_get_calculate_method_not_allowed`

---

### Task 1: Engineering Module `dc_bias.py`

**Files:**
- Create: `requirements.txt`, `.gitignore`, `dc_bias.py`, `tests/test_dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Produces: `VCE_SAT: float`, `parse_inputs(raw: dict[str, str]) -> tuple[dict[str, float] | None, list[str]]`, `calculate(values: dict[str, float]) -> dict` โดย
  - `raw` keys: `vcc, r1, r2, rc, re, beta, vbe` (string, R หน่วย kΩ) → คืน `(values, [])` เมื่อผ่าน (R เป็น Ω แล้ว) หรือ `(None, errors)` เมื่อไม่ผ่าน
  - `values` keys เดิม แต่เป็น float (Ω) → คืน dict keys: `vth, rth, ib, ic, ie, ve, vb, vc, vce, region, warnings` — หน่วย V/Ω/A, `region` ∈ `"forward-active" | "cutoff" | "saturation"`, `warnings` เป็น `list[str]`

- [ ] **Step 1: สร้าง environment และ scaffolding**

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install flask
```

`requirements.txt`: `flask>=3.0` · `.gitignore`: `.venv/`, `__pycache__/`, `*.pyc`, `.env`

- [ ] **Step 2: เขียน failing tests ใน `tests/test_dc_bias.py`**

```python
import unittest
from dc_bias import VCE_SAT, parse_inputs, calculate

REFERENCE = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
             "re": "1", "beta": "100", "vbe": "0.7"}

class TestCalculate(unittest.TestCase):
    def test_reference_case(self):
        values, errors = parse_inputs(REFERENCE)
        self.assertEqual(errors, [])
        r = calculate(values)
        self.assertAlmostEqual(r["vth"], 2.1639344, delta=1e-5)
        self.assertAlmostEqual(r["rth"], 18032.7869, delta=1e-2)
        self.assertAlmostEqual(r["ib"], 1.2298581e-5, delta=1e-9)
        self.assertAlmostEqual(r["ic"], 1.2298581e-3, delta=1e-7)
        self.assertAlmostEqual(r["ie"], 1.2421567e-3, delta=1e-7)
        self.assertAlmostEqual(r["ve"], 1.2421567, delta=1e-5)
        self.assertAlmostEqual(r["vb"], 1.9421567, delta=1e-5)
        self.assertAlmostEqual(r["vc"], 9.2943122, delta=1e-5)
        self.assertAlmostEqual(r["vce"], 8.0521555, delta=1e-5)
        self.assertEqual(r["region"], "forward-active")
        self.assertEqual(r["warnings"], [])

    def test_second_parameter_set_is_not_hardcoded(self):
        r = calculate({"vcc": 15, "r1": 47000, "r2": 10000, "rc": 1000,
                        "re": 470, "beta": 200, "vbe": 0.7})
        vth = 15 * 10000 / 57000
        rth = 47000 * 10000 / 57000
        ib = (vth - 0.7) / (rth + 201 * 470)
        self.assertAlmostEqual(r["ic"], 200 * ib, delta=1e-9)
        self.assertNotAlmostEqual(r["ic"], 1.2298581e-3, delta=1e-6)

    def test_cutoff_when_vth_below_vbe(self):
        values, errors = parse_inputs(dict(REFERENCE, r2="1"))
        self.assertEqual(errors, [])
        r = calculate(values)
        self.assertEqual(r["region"], "cutoff")
        self.assertTrue(len(r["warnings"]) >= 1)

    def test_saturation_when_vce_low(self):
        values, errors = parse_inputs(dict(REFERENCE, rc="100"))
        self.assertEqual(errors, [])
        r = calculate(values)
        self.assertEqual(r["region"], "saturation")
        self.assertTrue(len(r["warnings"]) >= 1)

class TestParseInputs(unittest.TestCase):
    def test_converts_kohm_to_ohm(self):
        values, errors = parse_inputs(REFERENCE)
        self.assertEqual(errors, [])
        self.assertEqual(values["r1"], 100000.0)
        self.assertEqual(values["rc"], 2200.0)
        self.assertEqual(values["beta"], 100.0)

    def test_rejects_non_numeric(self):
        values, errors = parse_inputs(dict(REFERENCE, r2="abc"))
        self.assertIsNone(values)
        self.assertTrue(any("R2" in e for e in errors))

    def test_rejects_whitespace_only(self):
        values, errors = parse_inputs(dict(REFERENCE, vcc="  "))
        self.assertIsNone(values)
        self.assertEqual(len(errors), 1)

    def test_rejects_missing_field(self):
        bad = {k: v for k, v in REFERENCE.items() if k != "re"}
        values, errors = parse_inputs(bad)
        self.assertIsNone(values)
        self.assertTrue(any("RE" in e for e in errors))

    def test_rejects_nonpositive(self):
        for field in ("vcc", "r1", "r2", "rc", "re", "beta"):
            with self.subTest(field=field):
                values, errors = parse_inputs(dict(REFERENCE, **{field: "-5"}))
                self.assertIsNone(values)
                self.assertTrue(len(errors) >= 1)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: รันยืนยัน fail**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 4: Implement `dc_bias.py`**

- `VCE_SAT = 0.2`
- `parse_inputs`: เช็คครบทุก field (แสดงชื่อสัญลักษณ์ VCC/R1/R2/RC/RE/β/VBE ในข้อความไทย) → `float()` ล้มเหลวหรือ strip แล้วว่าง = non-numeric → ค่า ≤ 0 ของ `vcc, r1, r2, rc, re, beta` = invalid; `vbe` เช็คเฉพาะ numeric/missing; ตัวต้านทานคูณ 1000 เป็น Ω; คืน `(None, errors)` ทันทีที่มี error ใด ๆ
- ข้อความ error ตายตัว (web tests ยึดสตริงเหล่านี้): ขาด field → `"ต้องกรอกค่า {sym}"` · non-numeric → `"{sym} ต้องเป็นตัวเลข"` · ค่า ≤ 0 → `"{sym} ต้องมีค่ามากกว่า 0"`
- `calculate`: คำนวณตามสมการ Global Constraints; region/warnings:
  - `vth <= vbe` → `region="cutoff"`, warning: `"คำเตือน: VTH ≤ VBE ไบแอสไม่เพียงพอ ทรานซิสเตอร์น่าจะอยู่ในภาวะ Cutoff — ค่าที่แสดงมาจากสมการ Forward-Active ซึ่งใช้ไม่ได้จริงในภาวะนี้"`
  - `vce < VCE_SAT` → `region="saturation"`, warning: `"คำเตือน: VCE < VCE(sat) ≈ 0.2 V ทรานซิสเตอร์น่าจะอยู่ในภาวะ Saturation — ค่าที่แสดงมาจากสมการ Forward-Active ซึ่งใช้ไม่ได้จริงในภาวะนี้"`
  - ไม่งั้น `region="forward-active"`, `warnings=[]`

- [ ] **Step 5: รันยืนยัน pass**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS ทั้ง 8 tests (OK)

- [ ] **Step 6: Human Commit Gate — GitHub Desktop**

ผลลัพธ์ tests รายงานให้นักศึกษา → ตรวจ diff → commit message:
`feat: add dc_bias engineering module with tests` → executor ยืนยัน `git log`

---

### Task 2: Flask App + Template + CSS + Web Tests

**Files:**
- Create: `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`

**Interfaces:**
- Consumes: `dc_bias.parse_inputs`, `dc_bias.calculate` จาก Task 1 (signature ตาม Interfaces ของ Task 1)
- Produces: Flask app ชื่อ `app` ที่ import ได้ (`from app import app`) — ใช้โดย `flask --app app run` และ test client

- [ ] **Step 1: เขียน failing tests ใน `tests/test_web.py`**

```python
import unittest
from app import app
from tests.test_dc_bias import REFERENCE

class TestWeb(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_index(self):
        rv = self.client.get("/")
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'name="vcc"', rv.data)
        self.assertIn(b'name="beta"', rv.data)

    def test_post_valid(self):
        rv = self.client.post("/calculate", data=REFERENCE)
        self.assertEqual(rv.status_code, 200)
        html = rv.data.decode()
        self.assertIn("8.0522", html)      # VCE
        self.assertIn("1.2299", html)      # IC [mA]
        self.assertIn("Forward-Active", html)

    def test_post_invalid_input(self):
        rv = self.client.post("/calculate", data=dict(REFERENCE, r1="-100"))
        self.assertEqual(rv.status_code, 200)
        html = rv.data.decode()
        self.assertIn("R1 ต้องมีค่ามากกว่า 0", html)  # error ระบุฟิลด์ที่ผิด
        self.assertNotIn("Forward-Active", html)

    def test_post_invalid_keeps_form_values(self):
        rv = self.client.post("/calculate", data=dict(REFERENCE, beta="-100"))
        html = rv.data.decode()
        self.assertIn('value="12"', html)  # ค่าที่กรอกถูกยังอยู่

    def test_post_cutoff_warning(self):
        rv = self.client.post("/calculate", data=dict(REFERENCE, r2="1"))
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Cutoff", rv.data.decode())

    def test_get_calculate_method_not_allowed(self):
        rv = self.client.get("/calculate")
        self.assertEqual(rv.status_code, 405)

if __name__ == "__main__":
    unittest.main()
```

หมายเหตุ: `tests/` ต้องมี `tests/__init__.py` (ไฟล์ว่าง) เพื่อให้ `from tests.test_dc_bias import REFERENCE` ทำงานได้

- [ ] **Step 2: รันยืนยัน fail**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: ERROR — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Implement `app.py`**

- `from flask import Flask, render_template, request` + `import dc_bias`
- `GET /` → `render_template("index.html")`
- `POST /calculate` → `values, errors = dc_bias.parse_inputs(request.form.to_dict())` → มี errors: `render_template("index.html", errors=errors, form=request.form)` → ไม่มี: `result = dc_bias.calculate(values)` แล้ว `render_template("index.html", result=result, form=request.form)`

- [ ] **Step 4: Implement `templates/index.html` + `static/style.css`**

สัญญาที่ template ต้องทำ (หน้าตา/สีเป็นของ builder ตาม spec §9):
- ฟอร์ม `method="POST" action="/calculate"` ฟิลด์ `name="vcc|r1|r2|rc|re|beta|vbe"` type=number step=any, label ไทย+สัญลักษณ์ (`VCC [V] — แรงดันจ่าย`, `R1 [kΩ]` …), `value="{{ form.get('vcc', '') }}"` เพื่อ refill, placeholder ค่าตัวอย่าง 12/100/22/2.2/1/100/0.7
- กล่อง errors (แดง) แสดงทุกข้อความจาก `errors`
- ตารางผล: VB, VE, VC, VCE [V] · IC, IE [mA] · IB [µA] · VTH [V], RTH [kΩ] — ทุกค่า `"%.4f"|format(...)` (ic/ie × 1000, ib × 1e6, rth ÷ 1000)
- badge region: ข้อความ `Forward-Active` / `Cutoff` / `Saturation` (จาก `result.region`)
- กล่อง warnings (ส้ม) แสดงทุกข้อความจาก `result.warnings` + ข้อความแบบจำลอง: "แบบจำลอง: Forward-Active Approximation (β และ VBE คงที่)"
- ไม่มี JavaScript คำนวณใด ๆ; `<link rel="stylesheet" href="/static/style.css">`

- [ ] **Step 5: รันยืนยัน pass**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS ทั้งหมด (unit 8 + web 6 = 14 tests, OK)

- [ ] **Step 6: Browser smoke demo**

```
.venv\Scripts\python.exe -m flask --app app run --debug   # background
```
เปิด `http://127.0.0.1:5000/` ใน browser → กรอกค่า reference → Calculate → เห็นผล IC=1.2299 mA, VCE=8.0522 V, badge Forward-Active → ลอง R1=-100 เห็น error → ลอง R2=1 เห็น Cutoff warning → screenshot เก็บเป็นหลักฐาน demo → ปิด server

- [ ] **Step 7: Human Commit Gate — GitHub Desktop**

commit message: `feat: add Flask web app with form, results and warnings`

---

### Task 3: Documentation และหลักฐานส่งงาน

**Files:**
- Create: `README.md`, `AGENTS.md`, `tests/__init__.py` (ถ้ายังไม่มีจาก Task 2), `docs/validation.md`, `docs/reflection.md`

**Interfaces:**
- Consumes: ผลรัน tests จริงล่าสุดจาก Task 1–2 (ต้องรันใหม่เพื่อคัดลอก log จริง ไม่ใช้ค่าคาดการณ์)

- [ ] **Step 1: เขียน `README.md`** — หัวข้อบังคับ: โปรเจกต์คืออะไร (1 ย่อหน้า) · สิ่งที่ต้องมี (Python ≥3.11, Git) · การติดตั้ง (`python -m venv .venv`, activate ทั้ง Windows/Linux/macOS, `pip install -r requirements.txt`) · การรัน (`flask --app app run --debug` → 127.0.0.1:5000) · การทดสอบ (`unittest discover -s tests`) · โครงสร้างไฟล์ · ข้อจำกัดแบบจำลอง (Forward-Active approximation, VCE_sat=0.2V)

- [ ] **Step 2: เขียน `AGENTS.md`** — ข้อตกลง AI: คำนวณเฉพาะใน `dc_bias.py` (ห้ามใน template/JS) · Thai UI copy + สัญลักษณ์สากล · TDD: เขียน test ก่อน implement · commit ทำโดยนักศึกษาผ่าน GitHub Desktop เท่านั้น · ห้าม commit `.venv/` หรือ secrets

- [ ] **Step 3: เขียน `docs/validation.md`** — รัน tests ใหม่ แล้วคัดลอก output จริง (ไม่แต่ง) + ตารางเทียบค่าอ้างอิง §6 ของ spec กับที่เว็บแสดง + ภาพ screenshot จาก Task 2 Step 6 + สรุปเกณฑ์ A1–A7 ผ่าน/ไม่ผ่าน

- [ ] **Step 4: เขียน `docs/reflection.md` (โครงคำถามเท่านั้น — นักศึกษาเขียนคำตอบเอง)** — คำถามรายบุคคลจากเอกสาร Lab: เหตุใดเปิด `templates/index.html` ตรง ๆ จึงไม่เท่ากับรัน Flask · ฟอร์มส่งข้อมูลไป Python อย่างไร · แก้สมการใน `dc_bias.py` แล้วต้องแก้ HTML หรือไม่ · ทำไมผลนอก Active Region ต้องมี Warning

- [ ] **Step 5: รัน full suite ยืนยันสุดท้าย + Human Commit Gate**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v` → Expected: OK 14 tests
commit message: `docs: add README, AGENTS.md and lab documentation` → push → ส่ง Repository URL + Commit SHA ทาง Moodle พร้อม screenshot และ test log
