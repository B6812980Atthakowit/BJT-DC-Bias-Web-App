import unittest
from app import app
import spice_engine


class TestSpiceEngine(unittest.TestCase):
    def test_resolve_ngspice(self):
        exe = spice_engine.resolve_ngspice()
        self.assertTrue(exe)

    def test_dc_op_reference(self):
        params = dict(vcc=12, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, rl=10e3,
                      cin=10e-6, cout=10e-6, vin_amp=0.01, freq=1000, bf=100,
                      model_name='Q2N2222_LAB', is_=14.34e-15, nf=1)
        r = spice_engine.run_simulation(params, 'dc')
        d = r['dc']
        self.assertEqual(r['run_status'], 'ok')
        self.assertAlmostEqual(d['vb'], 1.93, delta=0.15)
        self.assertAlmostEqual(d['ve'], 1.28, delta=0.15)
        self.assertAlmostEqual(d['vc'], 9.21, delta=0.25)
        self.assertGreater(d['vce'], 0.2)

    def test_ac_changes_with_re(self):
        base = dict(vcc=12, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, rl=10e3,
                    cin=10e-6, cout=10e-6, vin_amp=0.01, freq=1000, bf=100,
                    ac_mag=0.01, fstart=10, fstop=1e6, points=10,
                    model_name='Q2N2222_LAB', is_=14.34e-15, nf=1)
        r1 = spice_engine.run_simulation(base, 'ac')
        r2 = spice_engine.run_simulation(dict(base, re=2e3), 'ac')
        g1 = max(x['gain_db'] for x in r1['ac'] if x['gain_db'] == x['gain_db'])
        g2 = max(x['gain_db'] for x in r2['ac'] if x['gain_db'] == x['gain_db'])
        self.assertNotAlmostEqual(g1, g2, places=2)

    def test_tran_returns_waveform(self):
        params = dict(vcc=12, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, rl=10e3,
                      cin=10e-6, cout=10e-6, vin_amp=0.01, freq=1000, bf=100,
                      tstop=0.005, tstep=10e-6, model_name='Q2N2222_LAB', is_=14.34e-15, nf=1)
        r = spice_engine.run_simulation(params, 'tran')
        self.assertGreater(len(r['tran']), 100)
        self.assertGreater(r['tran_summary']['vout_pp_v'], 0)


class TestLab04Web(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_get_ce_amp_mode(self):
        html = self.client.get('/?mode=ce_amp').data.decode()
        self.assertIn('Analysis Mode', html)
        self.assertIn('Run Simulation', html)
        self.assertIn('name="analysis"', html)

    def test_post_ce_amp_dc(self):
        data = dict(mode='ce_amp', analysis='dc', vcc='12', r1='100', r2='22', rc='2.2', re='1',
                    rl='10', cin='10', cout='10', beta='100', vbe='0.7', vin_amp='10', freq='1',
                    fstart='10', fstop='1000000', points='10', tstop='5', tstep='10')
        html = self.client.post('/calculate', data=data).data.decode()
        self.assertIn('SPICE DC Operating Point', html)
        self.assertIn('ngspice', html)
        self.assertIn('Run: ok', html)

    def test_post_ce_amp_invalid_re(self):
        data = dict(mode='ce_amp', analysis='dc', vcc='12', r1='100', r2='22', rc='2.2', re='0',
                    rl='10', cin='10', cout='10', beta='100', vbe='0.7', vin_amp='10', freq='1',
                    fstart='10', fstop='1000000', points='10', tstop='5', tstep='10')
        html = self.client.post('/calculate', data=data).data.decode()
        self.assertIn('RE', html)
        self.assertNotIn('SPICE DC Operating Point', html)
