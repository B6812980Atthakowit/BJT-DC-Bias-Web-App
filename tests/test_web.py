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
        rv = self.client.post("/calculate", data=REFERENCE)
        self.assertEqual(rv.status_code, 200)
        html = rv.data.decode()
        self.assertIn("วิธี Approximate", html)
        self.assertIn("1.4639", html)   # VE approx [V]
        self.assertIn("14.4944", html)  # IB approx [µA]
        self.assertIn("1.4494", html)   # IC approx [mA]
        self.assertIn("7.3473", html)   # VCE approx [V]

    def test_post_cutoff_hides_approximate_comparison(self):
        rv = self.client.post("/calculate", data=dict(REFERENCE, r2="1"))
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn("วิธี Approximate", rv.data.decode())

    def test_get_calculate_method_not_allowed(self):
        rv = self.client.get("/calculate")
        self.assertEqual(rv.status_code, 405)

if __name__ == "__main__":
    unittest.main()
