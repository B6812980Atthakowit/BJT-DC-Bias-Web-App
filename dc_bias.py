"""Engineering module: BJT Common-Emitter Voltage-Divider Bias (DC).

Pure functions only — ไม่ import Flask/HTML ใด ๆ
แบบจำลอง: Forward-Active Approximation (β และ VBE คงที่)
หน่วยภายใน: V, A, Ω (ฟอร์มรับตัวต้านทานเป็น kΩ แล้วแปลงเป็น Ω ที่นี่)
"""

VCE_SAT = 0.2  # โวลต์ — ค่าประมาณ VCE(sat) ใช้ตรวจภาวะ saturation

# ชื่อ field ของฟอร์ม → สัญลักษณ์ที่แสดงต่อผู้ใช้
_FIELDS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}

# field ที่ต้องมีค่ามากกว่า 0 (VBE ตรวจเฉพาะว่าเป็นตัวเลขเท่านั้น)
_POSITIVE_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta")

# field ตัวต้านทาน (ฟอร์มรับหน่วย kΩ → แปลงเป็น Ω)
_RESISTOR_FIELDS = ("r1", "r2", "rc", "re")


def parse_inputs(raw):
    """ตรวจข้อมูลฟอร์มแล้วแปลงเป็นค่าที่ใช้คำนวณ

    raw: dict ของ string, keys: vcc, r1, r2, rc, re, beta, vbe
         (แรงดันเป็น V, ตัวต้านทานเป็น kΩ, β ไม่มีหน่วย)
    คืน (values, []) เมื่อผ่าน — values เป็น float, ตัวต้านทานเป็น Ω
    คืน (None, errors) เมื่อมีข้อผิดพลาดใด ๆ
    """
    errors = []
    values = {}
    for key, sym in _FIELDS.items():
        if key not in raw or raw[key] is None or raw[key].strip() == "":
            errors.append(f"ต้องกรอกค่า {sym}")
            continue
        try:
            value = float(raw[key])
        except (TypeError, ValueError):
            errors.append(f"{sym} ต้องเป็นตัวเลข")
            continue
        if key in _POSITIVE_FIELDS and value <= 0:
            errors.append(f"{sym} ต้องมีค่ามากกว่า 0")
            continue
        values[key] = value * 1000.0 if key in _RESISTOR_FIELDS else value

    if errors:
        return None, errors
    return values, []


def calculate(values):
    """คำนวณ DC operating point ตามสมการ Forward-Active Approximation

    values: dict ของ float — vcc [V], r1/r2/rc/re [Ω], beta, vbe [V]
    คืน dict: vth, rth, ib, ic, ie, ve, vb, vc, vce (V/Ω/A),
              region ("forward-active" | "cutoff" | "saturation"),
              warnings (list[str])
    """
    vcc = values["vcc"]
    r1 = values["r1"]
    r2 = values["r2"]
    rc = values["rc"]
    re = values["re"]
    beta = values["beta"]
    vbe = values["vbe"]

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)
    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    warnings = []
    if vth <= vbe:
        region = "cutoff"
        warnings.append(
            "คำเตือน: VTH ≤ VBE ไบแอสไม่เพียงพอ ทรานซิสเตอร์น่าจะอยู่ในภาวะ Cutoff — "
            "ค่าที่แสดงมาจากสมการ Forward-Active ซึ่งใช้ไม่ได้จริงในภาวะนี้"
        )
    elif vce < VCE_SAT:
        region = "saturation"
        warnings.append(
            "คำเตือน: VCE < VCE(sat) ≈ 0.2 V ทรานซิสเตอร์น่าจะอยู่ในภาวะ Saturation — "
            "ค่าที่แสดงมาจากสมการ Forward-Active ซึ่งใช้ไม่ได้จริงในภาวะนี้"
        )
    else:
        region = "forward-active"

    return {
        "vth": vth,
        "rth": rth,
        "ib": ib,
        "ic": ic,
        "ie": ie,
        "ve": ve,
        "vb": vb,
        "vc": vc,
        "vce": vce,
        "region": region,
        "warnings": warnings,
    }


def calculate_approximate(values):
    """คำนวณ DC operating point แบบ Approximate (stiff voltage divider)

    ต่างจาก calculate() ตรงที่ถือว่า divider แข็งแรงพอให้ VB = VTH
    (ละเลยกระแสโหลดของเบส) — ใช้เปรียบเทียบกับวิธี Exact/Thevenin
    คืน dict: vb, ve, vc, vce, ib, ic, ie (V/A)
    """
    vcc = values["vcc"]
    r1 = values["r1"]
    r2 = values["r2"]
    rc = values["rc"]
    re = values["re"]
    beta = values["beta"]
    vbe = values["vbe"]

    vb = vcc * r2 / (r1 + r2)   # VB = VTH
    ve = vb - vbe
    ie = ve / re
    ic = ie * beta / (beta + 1)
    ib = ie / (beta + 1)
    vc = vcc - ic * rc
    vce = vc - ve

    return {
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vce": vce,
        "ib": ib,
        "ic": ic,
        "ie": ie,
    }
