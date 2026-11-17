import unittest
from dc_bias import VCE_SAT, parse_inputs, calculate, calculate_approximate, calculate_fixed, calculate_emitter

REFERENCE = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
             "re": "1", "beta": "100", "vbe": "0.7"}
FRAME = {"vcc": "12", "rc": "2.2", "beta": "100", "vbe": "0.7"}

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

class TestCalculateApproximate(unittest.TestCase):
    def test_reference_case(self):
        values, errors = parse_inputs(REFERENCE)
        self.assertEqual(errors, [])
        r = calculate_approximate(values)
        self.assertAlmostEqual(r["vb"], 2.1639344, delta=1e-5)
        self.assertAlmostEqual(r["ve"], 1.4639344, delta=1e-5)
        self.assertAlmostEqual(r["ie"], 1.4639344e-3, delta=1e-7)
        self.assertAlmostEqual(r["ic"], 1.4494400e-3, delta=1e-7)
        self.assertAlmostEqual(r["ib"], 1.4494400e-5, delta=1e-9)
        self.assertAlmostEqual(r["vc"], 8.8112319, delta=1e-5)
        self.assertAlmostEqual(r["vce"], 7.3472975, delta=1e-5)

    def test_second_parameter_set_is_not_hardcoded(self):
        r = calculate_approximate({"vcc": 15, "r1": 47000, "r2": 10000,
                                   "rc": 1000, "re": 470, "beta": 200,
                                   "vbe": 0.7})
        vth = 15 * 10000 / 57000
        ve = vth - 0.7
        ie = ve / 470
        self.assertAlmostEqual(r["ic"], ie * 200 / 201, delta=1e-9)
        self.assertNotAlmostEqual(r["ic"], 1.4494400e-3, delta=1e-6)

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

    def test_fixed_cutoff_when_vbe_above_vcc(self):
        # VCC 0.5 V < VBE 0.7 V → IB < 0 → ต้องรายงาน Cutoff พร้อมคำเตือน
        values, errors = parse_inputs(
            dict(FRAME, vcc="0.5", vbe="0.7", rb="470"), mode="fixed"
        )
        self.assertEqual(errors, [])
        r = calculate_fixed(values)
        self.assertLess(r["ib"], 0.0)
        self.assertEqual(r["region"], "cutoff")
        self.assertEqual(len(r["warnings"]), 1)

    def test_emitter_saturation_when_vce_low(self):
        # RC = 12 kΩ ทำให้ VC ต่ำกว่า VE มาก → VCE ≤ 0.2 V → Saturation
        values, errors = parse_inputs(
            dict(FRAME, rb="1000", re="1", rc="12"), mode="emitter"
        )
        self.assertEqual(errors, [])
        r = calculate_emitter(values)
        self.assertLessEqual(r["vce"], VCE_SAT)
        self.assertEqual(r["region"], "saturation")
        self.assertEqual(len(r["warnings"]), 1)

    def test_fixed_second_parameter_set_is_not_hardcoded(self):
        # คนละชุดกับ A2 ทั้งหมด (VCC, RB, RC, β) — ต้องคำนวณจริงไม่ใช่ค่าคงที่
        values, errors = parse_inputs(
            {"vcc": "15", "rc": "1", "beta": "200", "vbe": "0.7", "rb": "470"},
            mode="fixed",
        )
        self.assertEqual(errors, [])
        r = calculate_fixed(values)
        self.assertAlmostEqual(r["ib"], 3.0425531914893615e-05, delta=1e-15)
        self.assertAlmostEqual(r["ic"], 6.085106382978723e-03, delta=1e-12)
        self.assertAlmostEqual(r["vce"], 8.914893617021277, delta=1e-9)
        self.assertEqual(r["region"], "forward-active")

    def test_emitter_second_parameter_set_is_not_hardcoded(self):
        # คนละชุดกับ A3/A4: β=50, RB=220 kΩ, RE=2 kΩ, VBE=0.65 V, VCC=15 V
        values, errors = parse_inputs(
            {"vcc": "15", "rc": "1", "beta": "50", "vbe": "0.65",
             "rb": "220", "re": "2"},
            mode="emitter",
        )
        self.assertEqual(errors, [])
        r = calculate_emitter(values)
        self.assertAlmostEqual(r["ic"], 2.2282608695652173e-03, delta=1e-12)
        self.assertAlmostEqual(r["ve"], 4.545652173913044, delta=1e-9)
        self.assertAlmostEqual(r["vce"], 8.226086956521739, delta=1e-9)
        self.assertEqual(r["region"], "forward-active")


if __name__ == "__main__":
    unittest.main()
