# Lab 03 Three Bias Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่ม Fixed Bias และ Emitter Bias ให้เว็บ Flask เดิม โดยเลือกโหมดได้ 3 แบบและคงผล Voltage Divider เดิมทุกประการ

**Architecture:** `dc_bias.py` ยังเป็น pure module — เพิ่ม `parse_inputs(raw, mode)` ที่ตรวจเฉพาะfieldของโหมดและฟังก์ชันคำนวณใหม่ 2 ตัวที่ส่ง `dict` รูปแบบเดียวกับ `calculate()` เดิม · `app.py` ตรวจโหมดแล้ว dispatch ด้วย `if/elif` · Jinja template แสดงเฉพาะช่องที่ใช้และไม่แสดงผลเก่าตอน error

**Tech Stack:** Python 3.15, Flask 3.1.3, unittest (built-in), Jinja2, OpenCode Browser (Playwright MCP NOT RUN)

**Spec:** `docs/superpowers/specs/2026-11-17-lab03-three-bias-modes-design.md` (อ่านพร้อมแผนนี้)

## Global Constraints

- ห้ามเปลี่ยนหรือลบ `calculate()` และ `calculate_approximate()` ใน `dc_bias.py` — 19 tests เดิมและ baseline A1 ต้องผ่านเหมือนเดิม
- `dc_bias.py` ห้าม import Flask · ไม่มี JavaScript คำนวณ · ไม่มีสมการใน template
- หน่วยภายใน V/A/Ω; ฟอร์มรับ kΩ → คูณ 1000 ครั้งเดียวใน `parse_inputs` (1 MΩ = 1000 kΩ = 1e6 Ω)
- ชื่อคีย์ผลคงเดิม: `vb, ve, vc, vce, ib, ic, ie, region, warnings` (V/A) — ใช้ชื่อนี้ต่อตามที่ใบงานอนุญาต
- โหมดใหม่เตือนเมื่อ `ib <= 0` หรือ `vce <= VCE_SAT (0.2)` · `calculate()` เดิมยังใช้ `VTH <= VBE` / `VCE < 0.2`
- โหมดที่ไม่รู้จัก → error เสมอ ห้ามแอบเป็น divider
- แสดงตัวเลขด้วย `"%.4f"|format(...)`; IC→mA, IB→µA เฉพาะตอนแสดง
- วิธีตรวจ: OpenCode Browser (built-in) เพราะ Playwright MCP NOT RUN — ต้องระบุวิธีจริงในตาราง A1–A5
- **รันเทส:** `.venv\Scripts\python.exe -m unittest discover -s tests -v` (Windows)
- **รันเว็บ:** `.venv\Scripts\python.exe -m flask --app app run` → http://127.0.0.1:5000/
- **Human Gate:** AI ห้าม commit/push — หลังแต่ละ task รายงานผล + ให้นักศึกษาตรวจ `git diff` และ commit ผ่าน GitHub Desktop เอง

## Review Focus

| เสี่ยง | พฤติกรรมที่คาด | ทดสอบที่คุ้มครอง |
|---|---|---|
| เปลี่ยนโหมดแล้วโชว์ result รอบก่อน (A5 RB=0) | ต้องไม่มีตารางผลปรากฏ มีแต่ error ระบุ RB | Task 2 `test_post_fixed_invalid_rb_shows_error_no_result` |
| A4 เปลี่ยน RE แต่ IC ไม่เปลี่ยน (ส่งฟอร์ม/parse ผิดช่อง) | IC ต้องลดจาก 1.0263 → 0.9401 mA | Task 1 `test_more_re_reduces_ic` + Task 2 `test_post_emitter_more_re_changes_ic` + browser A4 |
| Divider เสียจากการเพิ่ม mode | A1 ต้องยังได้ 1.2299 mA / 8.0522 V | Task 1 existing 19 tests + Task 2 `test_post_valid` + browser A1 |
| โหมดแปลก ๆ ถูกแอบเป็น divider | ต้อง error 「โหมดไม่รู้จัก」 | Task 1 `test_unknown_mode_error` + Task 2 `test_post_unknown_mode_error` |
| หน่วย kΩ → Ω ผิด (RB=1 MΩ ผ่าน 1000 kΩ) | IC Fixed ต้อง 1.1300 mA ไม่ใช่ 1130 mA | Task 1 `test_fixed_reference` + Task 2 `test_post_fixed_reference` |

---

### Task 1: Engineering module — parse ตามโหมด + ฟังก์ชัน Fixed/Emitter

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `VCE_SAT` เดิม, รูปแบบ `parse_inputs(raw)` เดิม
- Produces:
  - `MODE_FIELDS: dict[str, tuple[str, ...]]` — `fixed: (vcc, rc, beta, vbe, rb)`, `emitter: (vcc, rc, beta, vbe, rb, re)`, `divider: (vcc, rc, beta, vbe, r1, r2, re)`
  - `parse_inputs(raw, mode="divider") -> tuple[dict|None, list[str]]` — default ต้องเท่ากับของเดิมทุกประการ; field ของโหมดอื่นไม่ต้องกรอก
  - `calculate_fixed(values: dict[str,float]) -> dict` และ `calculate_emitter(values: dict[str,float]) -> dict` — คืน keys `vb, ve, vc, vce, ib, ic, ie, region, warnings` (V/A)

- [ ] **Step 1: เขียน failing tests ต่อท้าย `tests/test_dc_bias.py`**

แก้บรรทัด import เป็น `from dc_bias import VCE_SAT, parse_inputs, calculate, calculate_approximate, calculate_fixed, calculate_emitter` แล้วเขียน 6 test ต่อไปนี้ (Define `FRAME = {"vcc":"12","rc":"2.2","beta":"100","vbe":"0.7"}` ที่ระดับโมดูล):

```python
class TestModeParsing(unittest.TestCase):
    def test_fixed_accepts_rb_without_r1_r2_re(self):
        values, errors = parse_inputs(dict(FRAME, rb="1000"), mode="fixed")
        self.assertEqual(errors, [])
        self.assertEqual(values["rb"], 1_000_000.0)
        self.assertNotIn("r1", values)
        self.assertNotIn("re", values)

    def test_emitter_accepts_rb_and_re(self):
        values, errors = parse_inputs(dict(FRAME, rb="1000", re="1"), mode="emitter")
        self.assertEqual(errors, [])
        self.assertEqual(values["rb"], 1_000_000.0)
        self.assertEqual(values["re"], 1000.0)

    def test_fixed_rejects_zero_rb(self):
        values, errors = parse_inputs(dict(FRAME, rb="0"), mode="fixed")
        self.assertIsNone(values)
        self.assertTrue(any("RB ต้องมีค่ามากกว่า 0" in e for e in errors))

    def test_unknown_mode_returns_error(self):
        values, errors = parse_inputs(dict(FRAME, rb="1000"), mode="bogus")
        self.assertIsNone(values)
        self.assertTrue(any("โหมดไม่รู้จัก" in e for e in errors))

class TestFixedAndEmitter(unittest.TestCase):
    def test_fixed_reference(self):
        values, errors = parse_inputs(dict(FRAME, rb="1000"), mode="fixed")
        r = calculate_fixed(values)
        self.assertAlmostEqual(r["ic"], 1.13e-3, delta=1e-9)
        self.assertAlmostEqual(r["vce"], 9.514, delta=1e-9)
        self.assertEqual(r["ve"], 0.0)
        self.assertEqual(r["region"], "forward-active")
        self.assertEqual(r["warnings"], [])

    def test_emitter_reference_and_more_re_reduces_ic(self):
        v3, _ = parse_inputs(dict(FRAME, rb="1000", re="1"), mode="emitter")
        v4, _ = parse_inputs(dict(FRAME, rb="1000", re="2"), mode="emitter")
        a3, a4 = calculate_emitter(v3), calculate_emitter(v4)
        self.assertAlmostEqual(a3["ic"], 1.0263396911898275e-3, delta=1e-12)
        self.assertAlmostEqual(a3["vce"], 8.705449591280654, delta=1e-9)
        self.assertAlmostEqual(a4["ic"], 0.940099833610649e-3, delta=1e-12)
        self.assertAlmostEqual(a4["vce"], 8.032778702163062, delta=1e-9)
        self.assertLess(a4["ic"], a3["ic"])
```

- [ ] **Step 2: รันยืนยัน fail**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: ERROR/FAIL — `MODE_FIELDS`, `calculate_fixed`, `calculate_emitter` ไม่มี หรือ `parse_inputs` ไม่รับ `mode`

- [ ] **Step 3: Implement ใน `dc_bias.py`**

- เพิ่ม `"rb": "RB"` ใน `_FIELDS` และ `"rb"` ใน `_POSITIVE_FIELDS` / `_RESISTOR_FIELDS`
- เปลี่ยน signature เป็น `parse_inputs(raw, mode="divider")`; ถ้า `mode not in MODE_FIELDS` → คืน `(None, [f"โหมดไม่รู้จัก: {mode}"])` ทันที; ตรวจเฉพาะ field ใน `MODE_FIELDS[mode]` ด้วย logic เดิมทุกข้อความ error
- เพิ่ม helper ส่วนตัว `_assemble_new(ib, vcc, rc, re_ohm, has_re, beta, vbe)` ที่คำนวณ `ic, ie, ve, vb, vc, vce` ตาม spec และกำหนด `region/warnings` ด้วยกฎใหม่ (`ib <= 0` → cutoff, `vce <= VCE_SAT` → saturation) โดยข้อความ warning เป็นภาษาไทยอธิบายว่าแบบจำลอง Forward-Active อาจใช้ไม่ได้
- `calculate_fixed`: `ib=(vcc-vbe)/rb` → เรียก helper ด้วย `re_ohm=0, has_re=False`
- `calculate_emitter`: `ib=(vcc-vbe)/(rb+(beta+1)*re)` → เรียก helper ด้วย `re_ohm=re, has_re=True`
- **ห้ามแก้** `calculate()` และ `calculate_approximate()`

- [ ] **Step 4: รันชุดเต็มยืนยันผ่าน**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: OK (19 เดิม + 6 ใหม่ = 25)

- [ ] **Step 5: Human Gate**

รายงานผล tests ให้นักศึกษาตรวจ `git diff` — **ห้าม commit เอง**

---

### Task 2: Flask route + ฟอร์มเลือกโหมด

**Files:**
- Modify: `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`

**Interfaces:**
- Consumes: `dc_bias.MODE_FIELDS`, `parse_inputs(raw, mode)`, `calculate_fixed`, `calculate_emitter`, `calculate`, `calculate_approximate`
- Produces: `GET /?mode=<fixed|emitter|divider>` render ฟอร์มตามโหมด · `POST /calculate` อ่าน `form["mode"]` → render พร้อม `mode, result, approx, errors, form` · `approx` ไม่ใช่ None เฉพาะ divider+forward-active

- [ ] **Step 1: เขียน failing web tests ต่อท้าย `tests/test_web.py`**

```python
class TestLab03Modes(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_mode_fixed_shows_rb_only(self):
        html = self.client.get("/?mode=fixed").data.decode()
        self.assertIn('name="rb"', html)
        self.assertNotIn('name="re"', html)
        self.assertNotIn('name="r1"', html)

    def test_get_mode_emitter_shows_rb_and_re(self):
        html = self.client.get("/?mode=emitter").data.decode()
        self.assertIn('name="rb"', html)
        self.assertIn('name="re"', html)
        self.assertNotIn('name="r1"', html)

    def test_post_fixed_reference(self):
        data = dict(vcc="12", rb="1000", rc="2.2", beta="100", vbe="0.7", mode="fixed")
        html = self.client.post("/calculate", data=data).data.decode()
        self.assertIn("Fixed Bias", html)
        self.assertIn("1.1300", html)
        self.assertIn("9.5140", html)

    def test_post_emitter_reference(self):
        data = dict(vcc="12", rb="1000", re="1", rc="2.2", beta="100", vbe="0.7", mode="emitter")
        html = self.client.post("/calculate", data=data).data.decode()
        self.assertIn("Emitter Bias", html)
        self.assertIn("1.0263", html)
        self.assertIn("8.7054", html)

    def test_post_emitter_more_re_changes_ic(self):
        data = dict(vcc="12", rb="1000", re="2", rc="2.2", beta="100", vbe="0.7", mode="emitter")
        html = self.client.post("/calculate", data=data).data.decode()
        self.assertIn("0.9401", html)
        self.assertNotIn("1.0263", html)

    def test_post_fixed_invalid_rb_shows_error_no_result(self):
        data = dict(vcc="12", rb="0", rc="2.2", beta="100", vbe="0.7", mode="fixed")
        html = self.client.post("/calculate", data=data).data.decode()
        self.assertIn("RB ต้องมีค่ามากกว่า 0", html)
        self.assertNotIn("DC Bias Results", html)

    def test_post_unknown_mode_error(self):
        data = dict(vcc="12", rb="1000", rc="2.2", beta="100", vbe="0.7", mode="bogus")
        html = self.client.post("/calculate", data=data).data.decode()
        self.assertIn("โหมดไม่รู้จัก", html)
        self.assertNotIn("DC Bias Results", html)
```

- [ ] **Step 2: รันยืนยัน fail**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: FAIL — ไม่มี_select `name="mode"`, ไม่มีข้อความโหมดในผล, RB ไม่ถูกตรวจ

- [ ] **Step 3: Implement `app.py`**

- `index()` อ่าน `mode = request.args.get("mode", "divider")`; ถ้าไม่มีใน `dc_bias.MODE_FIELDS` → ตั้ง `errors=["โหมดไม่รู้จัก: ..."]` และใช้ `mode="divider"` เพื่อโชว์ฟอร์มได้; ส่ง `mode=mode, errors=errors, form={}` ไป template
- `calculate()`: `form = request.form.to_dict()`, `mode = form.get("mode", "divider")`; ถ้า mode ไม่รู้จัก → render พร้อม error และไม่มี result; มิฉะนั้น `values, errors = dc_bias.parse_inputs(form, mode)` → มี error: render `errors, form, mode` **โดยไม่ส่ง result/approx**; ไม่มี error: dispatch `fixed→calculate_fixed`, `emitter→calculate_emitter`, `divider→calculate` + `calculate_approximate` (ถ้า region forward-active) → render พร้อม `result, approx, form, mode`
- เก็บ method/route เดิม `/` (GET) และ `/calculate` (POST) ไว้ — `test_get_calculate_method_not_allowed` ต้องยังผ่าน

- [ ] **Step 4: Implement `templates/index.html`**

- เพิ่มฟอร์ม GET แยกก่อนฟอร์มหลัก: `<select name="mode" id="mode">` มี option `fixed/emitter/divider` พร้อม `{% if mode == ... %}selected{% endif %}` + ปุ่ม `เปลี่ยนโหมด` (form `method="get" action="/"`) — ห้าม JS
- ในฟอร์ม POST หลัก: `<input type="hidden" name="mode" value="{{ mode }}">` และโชว์ชื่อโหมดที่เลือกในหัวข้อ ("Fixed Bias" / "Emitter Bias" / "Voltage Divider Bias") ทั้งในกล่อง error และหัวตารางผล
- field: `vcc, rc, beta, vbe` แสดงเสมอ · `rb` เฉพาะ fixed/emitter · `re` เฉพาะ emitter/divider · `r1, r2` เฉพาะ divider · ทุก `value="{{ form.get('...', '') if form else '' }}"` เหมือนเดิม
- ตารางผลใช้ `result.*` เหมือนเดิม แต่ให้แสดงแถว VTH/RTH เฉพาะเมื่อมีคีย์ (`{% if result.vth is defined %}`); ตาราง Approximate แสดงเฉพาะ `mode == 'divider' and result.region == 'forward-active'`
- ปิด CSS class เล็กน้อยใน `static/style.css` สำหรับ `.mode-card`

- [ ] **Step 5: รันชุดเต็มยืนยันผ่าน**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: OK (25 เดิม + 7 ใหม่ = 32)

- [ ] **Step 6: Human Gate**

รายงานผล + รายการไฟล์ให้ตรวจ — **ห้าม commit เอง**

---

### Task 3: ตรวจผ่าน Browser จริง + เอกสารส่งงาน

**Files:**
- Modify: `docs/validation.md`, `README.md`
- Create (ถ้าจำเป็น): `docs/lab03-a3-emitter.jpeg`

**Interfaces:**
- Consumes: แอปที่รันอยู่ + ตาราง A1–A5 จาก spec · เซิร์ฟเวอร์เดิมที่รันค้างอยู่ (ตรวจว่า Flask ยังตอบ http://127.0.0.1:5000/ อยู่)
- Produces: ตาราง A1–A5 ที่กรอกผลจริง พร้อมวิธีตรวจ OpenCode Browser และสถานะ

- [ ] **Step 1: รอบตรวจ A1–A5 ใน OpenCode Browser**

เปิด/refresh http://127.0.0.1:5000/ แล้วสำหรับแต่ละกรณี: เลือกโหมดด้วย select + กด "เปลี่ยนโหมด" → อ่าน snapshot ใหม่ → กรอกเฉพาะช่องที่โหมดใช้ → กด **Calculate DC Bias** → อ่านค่าจาก snapshot หลังส่งฟอร์มจริง (ห้ามใช้ผลรอบก่อน) บันทึก IC/VCE และข้อความ error ของ A5 พร้อม screenshot อย่างน้อย 1 กรณีของโหมดใหม่

- [ ] **Step 2: เทียบค่าคาดหมาย (จาก spec — ห้ามใช้ค่าจากโค้ดเป็นคำตอบอ้างอิง)**

| กรณี | คาดหมายก่อนรัน |
|---|---|
| A1 | IC 1.2299 mA · VCE 8.0522 V (ต้องตรง baseline ก่อนแก้) |
| A2 | IC 1.1300 mA · VCE 9.5140 V |
| A3 | IC 1.0263 mA · VCE 8.7054 V |
| A4 | IC 0.9401 mA · VCE 8.0328 V และต้อง **น้อยกว่า A3** |
| A5 | ข้อความ `RB ต้องมีค่ามากกว่า 0`, ไม่มีตารางผล |

เกณฑ์: |ΔIC| ≤ 0.01 mA, |ΔVCE| ≤ 0.02 V เทียบค่าก่อนปัด · ใช้ PASS/FAIL/NOT RUN ตามผลจริง

- [ ] **Step 3: อัปเดตเอกสาร**

- `docs/validation.md`: เพิ่มตาราง A1–A5 ที่กรอกผลจริง+หน่วย+วิธีตรวจ `OpenCode Browser`+สถานะ+หลักฐาน, พร้อมสมการอิสระที่ใช้คำนวณค่าคาดหมาย และหมายเหตุ Playwright MCP NOT RUN
- `README.md`: เปลี่ยนคำอธิบายจากวงจรเดียวเป็น 3 โหมด, อธิบายปุ่ม "เปลี่ยนโหมด", อัปเดตจำนวน tests, เพิ่มหมายเหตุขอบเขต Lab 03

- [ ] **Step 4: รัน full suite ครั้งสุดท้าย**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: OK 32 tests · แล้ว `git status --short` ตรวจว่าไม่มี `.venv/`, `__pycache__/`, `.env` ปน

- [ ] **Step 5: Human Gate สุดท้าย**

รายงานสรุป + ผล A1–A5 ให้นักศึกษาตรวจ `git diff` / `git diff --staged` แล้ว commit–push ผ่าน GitHub Desktop เอง และตอบ `docs/reflection.md` ด้วยคำของตนเอง — **AI ห้าม commit/push/ตอบ reflection**
