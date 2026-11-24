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

    def test_post_valid_shows_approximate_comparison(self):
        data = dict(
            vcc="12", r1="100", r2="22", rc="2.2", re="1",
            beta="100", vbe="0.7", mode="divider",
        )
        html = self.client.post("/calculate", data=data).data.decode()
        self.assertIn("Approximate", html)
        self.assertIn("1.4639", html)   # approx VE
        self.assertIn("7.3473", html)   # approx VCE

    def test_post_cutoff_hides_approximate_comparison(self):
        rv = self.client.post("/calculate", data=dict(REFERENCE, r2="1"))
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn("วิธี Approximate", rv.data.decode())

    def test_get_calculate_method_not_allowed(self):
        rv = self.client.get("/calculate")
        self.assertEqual(rv.status_code, 405)

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
        self.assertIn("RB", html)
        self.assertIn("0", html)
        self.assertNotIn("DC Bias Results ? Fixed Bias (Analytical)", html)

    def test_post_unknown_mode_error(self):
        data = dict(vcc="12", rb="1000", rc="2.2", beta="100", vbe="0.7", mode="bogus")
        html = self.client.post("/calculate", data=data).data.decode()
        self.assertIn("bogus", html)
        self.assertNotIn("DC Bias Results ?", html)

    def test_post_emitter_saturation_shows_warning(self):
        data = dict(vcc="12", rb="1000", re="1", rc="12", beta="100", vbe="0.7", mode="emitter")
        html = self.client.post("/calculate", data=data).data.decode()
        self.assertIn("Saturation", html)
        self.assertIn("แบบจำลอง Forward-Active อาจใช้ไม่ได้", html)


if __name__ == "__main__":
    unittest.main()
