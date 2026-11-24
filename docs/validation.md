# Validation & Test Evidence — BJT DC Bias Web App

เอกสารนี้บันทึกผลการทดสอบจริง (ไม่ได้แต่งเติม) ใช้เป็นหลักฐานยืนยันว่าโปรเจกต์ผ่านเกณฑ์การรับ A1–A7 ของ Lab 02

## 0. Lab 03 — บันทึกผล Voltage Divider ก่อนแก้ (Baseline A1)

รันวันที่ 2026-11-17 ด้วย `.venv\Scripts\python.exe -m flask --app app run` **ก่อนแก้โค้ดใด ๆ** เปิด `http://127.0.0.1:5000/` กรอกชุดเดิมแล้วกด Calculate จริง วิธีที่ใช้: **OpenCode Browser** (built-in browser tool ของ OpenCode Desktop — อ่าน snapshot หน้าเว็บและดู network แทนการอ่านโค้ด)

**อินพุต:** VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, β = 100, VBE = 0.70 V

**ผลที่อ่านจากหน้าเว็บจริง (ตารางหลัก Exact/Thevenin):**

| ปริมาณ | ค่าที่เห็น | หน่วย |
|---|---|---|
| VTH | 2.1639 | V |
| RTH | 18.0328 | kΩ |
| VB | 1.9422 | V |
| VE | 1.2422 | V |
| VC | 9.2943 | V |
| **VCE** | **8.0522** | **V** |
| IB | 12.2986 | µA |
| **IC** | **1.2299** | **mA** |
| IE | 1.2422 | mA |

Operating Region: **Forward-Active** · ตาราง Approximate ที่แสดงร่วม: VB = 2.1639 V, VE = 1.4639 V, VC = 8.8112 V, VCE = 7.3473 V, IB = 14.4944 µA, IC = 1.4494 mA, IE = 1.4639 mA

**หลักฐาน:** `docs/lab03-baseline-a1.jpeg` (ภาพหน้าเว็บหลังกด Calculate) · network tool พบคำขอ `POST http://127.0.0.1:5000/calculate` จริง

**Playwright MCP: NOT RUN** — ตรวจแล้วเครื่องนี้ไม่มี `node`/`npx` บน PATH (และไม่พบ Node ในตำแหน่งติดตั้งมาตรฐาน) ไม่มี `opencode.json` ในโปรเจกต์ และ session นี้ไม่มี MCP server `playwright` ปรากฏ จึงใช้ OpenCode Browser ตามวิธีสำรองที่ใบงานอนุญาต โดยต้องระบุวิธีจริงในตาราง A1–A5 ว่าเป็น OpenCode Browser

> ค่าชุดนี้คือค่าที่ต้องได้อีกครั้งหลังเพิ่ม Fixed/Emitter Bias — ถ้า A1 เปลี่ยนแปลว่า Divider เสียจากการแก้

## 1. ผลการรัน Automated Tests — Lab 02 (ก่อนเพิ่มโหมด)

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

## 6. Lab 03 — ผลตรวจ A1–A5 บนหน้าเว็บจริง (Fixed / Emitter / Divider)

รันวันที่ 2026-11-17 หลังเพิ่มโหมด Fixed และ Emitter แล้ว · เซิร์ฟเวอร์ `.venv\Scripts\python.exe -m flask --app app run` → `http://127.0.0.1:5000/` · วิธีตรวจ: **OpenCode Browser** (เปิดหน้าเว็บจริง เลือกโหมดด้วย `<select name="mode">` + ปุ่ม "เปลี่ยนโหมด" กรอกช่องของโหมดนั้น กด **Calculate DC Bias** แล้วอ่าน snapshot หลังส่งฟอร์มทุกครั้ง — ไม่ได้อ่านค่าจากโค้ด)

**ชุดค่าคงที่ร่วม:** VCC = 12 V · RC = 2.2 kΩ · β = 100 · VBE = 0.70 V · อินพุตตัวต้านทานกรอกเป็น kΩ (1 MΩ = 1000 kΩ)

| กรณี | โหมด + อินพุตที่กรอก | ค่าคาดหมายอิสระ (ก่อนรัน) | ค่าที่อ่านได้จริงจากหน้าเว็บ | Δ | สถานะ | หลักฐาน |
|---|---|---|---|---|---|---|
| **A1** | Divider · R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | IC = 1.2299 mA · VCE = 8.0522 V | IC = **1.2299 mA** · VCE = **8.0522 V** · region Forward-Active · ตาราง Approximate แสดง | 0 | **PASS** | `docs/lab03-baseline-a1.jpeg` (baseline) + ตรวจซ้ำหลังแก้ |
| **A2** | Fixed · RB=1000 kΩ | IC = 1.1300 mA · VCE = 9.5140 V | IC = **1.1300 mA** · VCE = **9.5140 V** · IB = 11.3000 µA · VE = 0.0000 V · ไม่มีตาราง Approximate | 0 | **PASS** | ตรวจใน OpenCode Browser (snapshot หลัง POST) |
| **A3** | Emitter · RB=1000 kΩ, RE=1 kΩ | IC = 1.0263 mA · VCE = 8.7054 V | IC = **1.0263 mA** · VCE = **8.7054 V** · IB = 10.2634 µA · VE = 1.0366 V | 0 | **PASS** | `docs/lab03-a3-emitter.jpeg` |
| **A4** | Emitter · RB=1000 kΩ, RE=2 kΩ | IC = 0.9401 mA · VCE = 8.0328 V และ **ต้องน้อยกว่า A3** | IC = **0.9401 mA** · VCE = **8.0328 V** · IB = 9.4010 µA · น้อยกว่า A3 (1.0263 → 0.9401 mA) จริง | 0 | **PASS** | ตรวจใน OpenCode Browser (เปลี่ยน RE แล้วกด Calculate ใหม่) |
| **A5** | Fixed · RB=0 kΩ | error `RB ต้องมีค่ามากกว่า 0` และไม่มีตารางผล | แสดง `RB ต้องมีค่ามากกว่า 0` ในกล่อง error (โหมด Fixed Bias) · **ไม่มี** `DC Bias Results` | — | **PASS** | ตรวจใน OpenCode Browser (snapshot หลัง POST) |

**เกณฑ์ผ่าน:** |ΔIC| ≤ 0.01 mA และ |ΔVCE| ≤ 0.02 V เทียบค่าก่อนปัด · ทุกกรณี Δ = 0 (ค่าที่แสดงตรงกับค่าอ้างอิง 4 ตำแหน่ง)

**สมการที่ใช้คำนวณค่าคาดหมายอิสระ (คำนวณจากใบงานด้วยมือ/Fraction ไม่ใช้โค้ดแอป):**

- Fixed: `IB = (VCC − VBE)/RB`, `VE = 0`, `IC = β·IB`, `VB = VBE`, `VC = VCC − IC·RC`, `VCE = VC`
- Emitter (แหล่งจ่ายเดียว): `IB = (VCC − VBE)/[RB + (β+1)RE]`, `IC = β·IB`, `IE = (β+1)IB`, `VE = IE·RE`, `VB = VE + VBE`, `VC = VCC − IC·RC`, `VCE = VC − VE`
- Divider: คงสมการ Exact/Thevenin เดิมของ Lab 02 (§2)

**หมายเหตุวิธีตรวจ:** **Playwright MCP: NOT RUN** — เครื่องนี้ไม่มี `node`/`npx` บน PATH ไม่มี `opencode.json` และ session ไม่มี MCP server `playwright` จึงใช้ **OpenCode Browser** ซึ่งเป็นวิธีสำรองที่ใบงานอนุญาต โดยตารางนี้ระบุวิธีจริงตามที่ใช้

## 7. Lab 03 — ผลรัน Automated Tests ล่าสุด (37 tests)

คำสั่ง: `.venv\Scripts\python.exe -m unittest discover -s tests -v`

```
Ran 37 tests in 0.051s

OK
```

- Unit tests (วิศวกรรม): 21 tests (`tests/test_dc_bias.py`) — 11 เดิม + 10 ใหม่ (parse ตามโหมด, Fixed/Emitter reference, A4 ทิศทาง, RB=0, โหมดไม่รู้จัก, cutoff/saturation ของโหมดใหม่, พารามิเตอร์ชุดที่ 2 กัน hardcode)
- Flask test-client tests: 16 tests (`tests/test_web.py`) — 8 เดิม + 8 ใหม่ (GET ตามโหมด, POST Fixed/Emitter, A4 เปลี่ยน IC, A5 ไม่มีผล, โหมดไม่รู้จัก, คำเตือน Saturation)
- **รวม 37/37 ผ่าน** และ 19 tests เดิมของ Lab 02 ยังผ่านทั้งหมด

---
จัดทำโดย: นักศึกษา ENG29 2121 Lab 02 (2/2569) · เพิ่มเติม Lab 03 วันที่ 2026-11-17
วันที่: 2026-11-10 (Lab 02) · 2026-11-17 (Lab 03)

## 8. Lab 04 ? CE Amplifier Simulator v1 (SPICE/ngspice) validation notes

> Added by implementation session. Browser B1-B8 evidence should be captured on the target machine; automated checks below were run in this workspace.

### Automated checks run

- Command: `py -3 -m unittest discover -s tests -v` (GitHub repo, venv from existing project)
- Result: **44 tests, OK** (includes 37 prior Lab 03 tests + 7 new Lab 04 SPICE/web tests)
- ngspice version: `ngspice-47`
- Engine path resolved outside repo (`NGSPICE_EXE`/PATH/local install), binaries not copied into repo.

### SPICE reference sanity (automated, ngspice real run)

Reference CE Voltage Divider: VCC=12V, R1=100k, R2=22k, RC=2.2k, RE=1k, RL=10k, Cin=10u, Cout=10u, Vin=10mVpk, f=1kHz, Q2N2222_LAB (BF=100, IS=14.34e-15, NF=1).

| Check | Expected/behavior | Observed | Status |
|---|---|---:|---|
| DC .op | ngspice returns node voltages, VCE>0.2V active-ish | VB~1.935V, VE~1.283V, VC~9.206V, VCE~7.923V | PASS (auto) |
| AC .ac | Bode data from wrdata, gain changes when RE changes | max gain differs for RE=1k vs 2k; plotted from parsed rows | PASS (auto) |
| Tran .tran | Vin/Vout waveform from wrdata, Vout has amplitude | 508 points, Vin p-p~20mV, Vout p-p~35mV | PASS (auto) |
| Invalid input | RE=0 rejected by validation | Error shown, no SPICE result table | PASS (auto/web) |
| Provenance | Netlist/log/engine/model/status visible | Included in UI details | PASS (code) |

### B1-B8 browser acceptance

| Case | Status | Evidence |
|---|---|---|
| B1 Regression Lab 3 modes | NOT RUN in browser MCP (no Playwright MCP in session) / covered by 37 regression tests | unittest |
| B2 DC SPICE | PARTIAL (automated + local run), browser screenshot pending | test_spice/test_web |
| B3 Change RE | PASS (auto AC gain changes) browser evidence pending | test_spice |
| B4 AC | PASS (auto parsed rows) browser evidence pending | test_spice |
| B5 Transient | PASS (auto waveform) browser evidence pending | test_spice |
| B6 Change source | NOT RUN | pending browser |
| B7 Invalid/fail | PASS (auto invalid RE), engine-missing path handled in code | test_web |
| B8 UI responsive | NOT RUN | pending browser |

### Known limitations

- SPICE DC currents IC/IE/IB are derived from node voltages and resistor values for display; raw ngspice node voltages are authoritative.
- BJT model is a simple educational model (`Q2N2222_LAB`) with BF tied to user beta input; not a full manufacturer model.
- AC/Tran charts are rendered by lightweight canvas JS (no external chart dependency); they plot parsed ngspice data only.
- Browser acceptance B1-B8 screenshots should be captured by student on local machine before submission.
