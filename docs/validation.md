# Validation & Test Evidence — BJT DC Bias Web App

เอกสารนี้บันทึกผลการทดสอบจริง (ไม่ได้แต่งเติม) ใช้เป็นหลักฐานยืนยันว่าโปรเจกต์ผ่านเกณฑ์การรับ A1–A7 ของ Lab 02

## 1. ผลการรัน Automated Tests (ล่าสุด)

คำสั่งที่รัน:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ผลลัพธ์จริงจากเครื่อง (19 tests):

```
test_cutoff_when_vth_below_vbe (test_dc_bias.TestCalculate.test_cutoff_when_vth_below_vbe) ... ok
test_reference_case (test_dc_bias.TestCalculate.test_reference_case) ... ok
test_saturation_when_vce_low (test_dc_bias.TestCalculate.test_saturation_when_vce_low) ... ok
test_second_parameter_set_is_not_hardcoded (test_dc_bias.TestCalculate.test_second_parameter_set_is_not_hardcoded) ... ok
test_reference_case (test_dc_bias.TestCalculateApproximate.test_reference_case) ... ok
test_second_parameter_set_is_not_hardcoded
(test_dc_bias.TestCalculateApproximate.test_second_parameter_set_is_not_hardcoded) ... ok
test_converts_kohm_to_ohm (test_dc_bias.TestParseInputs.test_converts_kohm_to_ohm) ... ok
test_rejects_missing_field (test_dc_bias.TestParseInputs.test_rejects_missing_field) ... ok
test_rejects_non_numeric (test_dc_bias.TestParseInputs.test_rejects_non_numeric) ... ok
test_rejects_nonpositive (test_dc_bias.TestParseInputs.test_rejects_nonpositive) ... ok
test_rejects_whitespace_only (test_dc_bias.TestParseInputs.test_rejects_whitespace_only) ... ok
test_get_calculate_method_not_allowed (test_web.TestWeb.test_get_calculate_method_not_allowed) ... ok
test_get_index (test_web.TestWeb.test_get_index) ... ok
test_post_cutoff_hides_approximate_comparison (test_web.TestWeb.test_post_cutoff_hides_approximate_comparison) ... ok
test_post_cutoff_warning (test_web.TestWeb.test_post_cutoff_warning) ... ok
test_post_invalid_input (test_web.TestWeb.test_post_invalid_input) ... ok
test_post_invalid_keeps_form_values (test_web.TestWeb.test_post_invalid_keeps_form_values) ... ok
test_post_valid (test_web.TestWeb.test_post_valid) ... ok
test_post_valid_shows_approximate_comparison (test_web.TestWeb.test_post_valid_shows_approximate_comparison) ... ok

----------------------------------------------------------------------
Ran 19 tests in 0.054s
OK
```

- Unit tests (วิศวกรรม): 11 tests (test_dc_bias.py)
- Flask test-client tests: 8 tests (test_web.py)
- **รวม: 19/19 ผ่านทั้งหมด**

## 2. ตารางเทียบค่าอ้างอิง §6 ของเอกสาร Lab

ข้อมูลอินพุตมาตรฐาน: `VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V`

| ปริมาณ | ค่าอ้างอิง (§6) | ที่เว็บแสดง (Exact/Thevenin) | ต่างกันกี่ตำแหน่งทศนิยม | ผ่าน A3 |
|---|---|---|---|---|
| VTH | 2.1639 V | 2.1639 | 0 | ✓ |
| RTH | 18.0328 kΩ | 18.0328 | 0 | ✓ |
| IB | 12.2986 µA | 12.2986 | 0 | ✓ |
| IC | 1.2299 mA | 1.2299 | 0 | ✓ |
| IE | 1.2422 mA | 1.2422 | 0 | ✓ |
| VE | 1.2422 V | 1.2422 | 0 | ✓ |
| VB | 1.9422 V | 1.9422 | 0 | ✓ |
| VC | 9.2943 V | 9.2943 | 0 | ✓ |
| VCE | 8.0522 V | 8.0522 | 0 | ✓ |

ค่าที่เว็บแสดงตรงกับค่าอ้างอิงทุกตัว (รูปแบบ `%.4f` ตาม spec)

## 3. หลักฐานภาพหน้าจอ (จากการทดสอบจริงบน browser)

| ไฟล์ | สิ่งที่แสดง |
|---|---|
| `docs/demo-active.png` | กรอกค่ามาตรฐาน → ตาราง Exact (IC=1.2299 mA, VCE=8.0522 V, badge Forward-Active) + ตาราง Approximate (VB=2.1639, VE=1.4639, IC=1.4494, VCE=7.3473) |
| `docs/demo-cutoff.png` | R2=1 → Badge **Cutoff** + คำเตือนส้ม + ตาราง Approximate ถูกซ่อนอัตโนมัติ |

## 4. สรุปเกณฑ์การรับ A1–A7

| เกณฑ์ | รายละเอียด | ผล | หลักฐาน |
|---|---|---|---|
| **A1** | เปิด `http://127.0.0.1:5000/` ได้ ฟอร์มแสดงครบ (HTTP 200) | ✓ ผ่าน | test_get_index, browser demo |
| **A2** | POST `/calculate` → Python คำนวณจริง → แสดงผล (ไม่ใช่ hardcode) | ✓ ผ่าน | test_post_valid, server log `POST /calculate 200` |
| **A3** | ค่าตรงกับค่าอ้างอิง §6 ภายใต้แบบจำลองเดียวกัน | ✓ ผ่าน | ตารางข้างต้น, test_reference_case |
| **A4** | ค่าผิดพลาด → ข้อความ error ระบุฟิลด์ หน้าไม่ล้ม ค่ายังคงอยู่ | ✓ ผ่าน | test_post_invalid_input, test_post_invalid_keeps_form_values, browser demo (R1=-100) |
| **A5** | ค่านอก Active Region → มี Warning, ไม่อ้างว่าแม่นยำ | ✓ ผ่าน | test_post_cutoff_warning, browser demo (R2=1, RC=100) |
| **A6** | ≥3 unit tests + ≥1 Flask test-client test | ✓ ผ่าน | 11 unit + 8 web = 19 tests |
| **A7** | README clone-and-run ได้โดยไม่ต้องถามเพิ่ม | ✓ ผ่าน | README.md มีขั้นตอนครบถ้วน |

**สรุป: ผ่านทุกเกณฑ์ A1–A7**

## 5. หมายเหตุเกี่ยวกับวิธีคำนวณสองวิธี

- **ตารางหลัก (Exact/Thevenin)** ใช้สมการในหัวข้อ 06 ของเอกสาร Lab — เป็นมาตรฐานที่เกณฑ์ A3 ยึด
- **ตารางรอง (Approximate / stiff divider)** ถือว่า `VB = VTH` ละเลยกระแสโหลดของเบส — ตรงกับตัวเลขตัวอย่างในตำราบางเล่ม (VB≈2.2, IC≈1.5, VCE≈7.2 เมื่อปัดทศนิยม 1 ตำแหน่ง)
- เอกสาร Lab ระบุเองว่าตัวเลขในภาพตัวอย่างเป็น "ค่าประกอบภาพ ไม่ใช่คำตอบอ้างอิง" — แอปจึงยึดสมการในเอกสารเป็นหลัก พร้อมแสดงทั้งสองวิธีเพื่อเปรียบเทียบ

---
จัดทำโดย: นักศึกษา ENG29 2121 Lab 02 (2/2569)
วันที่: 2026-11-10