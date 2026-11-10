import unittest
from dc_bias import VCE_SAT, parse_inputs, calculate, calculate_approximate

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

if __name__ == "__main__":
    unittest.main()
