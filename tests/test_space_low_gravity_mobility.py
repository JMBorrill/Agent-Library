import json
import math
import unittest

from tests.helpers import assert_schema, load_script, rules, run_cli, run_json, skill_path

SKILL = "space-low-gravity-mobility"
lg = load_script(SKILL, "lowg_calc")
EX = skill_path(SKILL, "assets", "examples")
SCH = skill_path(SKILL, "assets", "schemas")

# Hand calculation for the synthetic ASTER-target sphere (r = 250 m, rho = 1900 kg/m^3):
# V = 4/3*pi*250^3 = 6.5449847e7 m^3; M = V*1900 = 1.2435471e11 kg; GM = 6.67430e-11*M = 8.29981 m^3/s^2
# g = GM/r^2 = 1.32797e-4 m/s^2; v_esc = sqrt(2GM/r) = 0.257679 m/s; v_circ = sqrt(GM/r) = 0.182207 m/s
G_ASTER = 1.32797e-4


class BodyTests(unittest.TestCase):
    def test_known_answer_sphere(self):
        b = lg.body(250.0, 1900.0)
        self.assertAlmostEqual(b["mass_kg"] / 1.2435e11, 1.0, delta=1e-4)
        self.assertAlmostEqual(b["surface_gravity_m_s2"], 1.328e-4, delta=0.001e-4)
        self.assertAlmostEqual(b["escape_speed_m_s"], 0.258, delta=0.0005)
        self.assertAlmostEqual(b["escape_speed_m_s"], 0.257679, delta=1e-6)
        self.assertAlmostEqual(b["circular_speed_m_s"], 0.182207, delta=1e-6)
        self.assertAlmostEqual(b["escape_speed_m_s"] / b["circular_speed_m_s"], math.sqrt(2), places=12)

    def test_mass_input_equivalent(self):
        a = lg.body(250.0, 1900.0)
        b = lg.body(250.0, mass_kg=a["mass_kg"])
        self.assertAlmostEqual(b["density_kg_m3"], 1900.0, places=6)

    def test_g_constant_codata_2018(self):
        self.assertEqual(lg.G, 6.67430e-11)
        self.assertIn("CODATA 2018", lg.G_SOURCE)

    def test_invalid_body_inputs(self):
        for args, kw in [((0, 1900), {}), ((-1, 1900), {}), ((250, -5), {}), ((250,), {}),
                         ((250, 1900), {"mass_kg": 1e11}), ((float("nan"), 1900), {})]:
            with self.assertRaises(lg.InputError):
                lg.body(*args, **kw)


class HopTests(unittest.TestCase):
    def test_known_answer_hop(self):
        # t = 2*0.05*sin45/g = 532.47 s; R = 0.05^2/g = 18.826 m; h = 0.05^2*0.5/(2g) = 4.7065 m
        h = lg.hop(0.05, 45.0, G_ASTER)
        self.assertAlmostEqual(h["flight_time_s"], 2 * 0.05 * math.sin(math.pi / 4) / G_ASTER, places=6)
        self.assertAlmostEqual(h["flight_time_s"], 532.47, delta=0.02)
        self.assertAlmostEqual(h["range_m"], 18.826, delta=0.001)
        self.assertAlmostEqual(h["apex_height_m"], 4.7065, delta=0.001)

    def test_vertical_hop_has_zero_range(self):
        h = lg.hop(0.01, 90.0, 1e-3)
        self.assertAlmostEqual(h["range_m"], 0.0, places=12)
        self.assertAlmostEqual(h["apex_height_m"], 0.05, places=12)

    def test_angle_and_speed_validation(self):
        for v, a in [(0.05, 0.0), (0.05, 95.0), (0.05, -10.0), (0.0, 45.0), (-1.0, 45.0)]:
            with self.assertRaises(lg.InputError):
                lg.hop(v, a, 1e-4)

    def test_escape_and_orbit_flags(self):
        base = {"radius_m": 250, "density_kg_m3": 1900, "angle_deg": 45}
        self.assertIn("exceeds-escape-speed", rules(lg.run("hop", {**base, "speed": 0.3})["findings"], "error"))
        self.assertIn("exceeds-orbital-speed", rules(lg.run("hop", {**base, "speed": 0.2})["findings"], "error"))
        res = lg.run("hop", {**base, "speed": 0.08})
        self.assertIn("flat-gravity-approx-questionable", rules(res["findings"], "warning"))
        self.assertTrue(res["passed"])
        ok = lg.run("hop", {**base, "speed": 0.05})
        self.assertEqual(ok["findings"], [])

    def test_hop_with_rotation_uses_net_gravity(self):
        res = lg.run("hop", {"preset": "aster-target", "speed": 0.02, "angle_deg": 45})
        rot = lg.rotation(250, lg.body(250, 1900)["gm_m3_s2"], 4.0)
        self.assertAlmostEqual(res["results"]["g_used_m_s2"], rot["net_radial_gravity_m_s2"], places=15)
        bad = lg.run("hop", {"preset": "fast-rotator-synthetic", "speed": 0.01})
        self.assertIn("no-ballistic-solution", rules(bad["findings"], "error"))


class RotatingFrameEscapeTests(unittest.TestCase):
    """F01 regression: escape/orbital checks must use the inertial (rotation-corrected) speed."""

    def test_reviewer_case_eastward_hop_exceeds_escape(self):
        # aster-target: omega*r = 2*pi/14400*250 = 0.109083 m/s; v_esc = 0.257679 m/s.
        # 0.15 m/s at 10 deg heading east: east 0.147721 + 0.109083 = 0.256804, up 0.026047
        # -> |v| = 0.258122 m/s > v_esc.
        res = lg.run("hop", {"preset": "aster-target", "speed": 0.15, "angle_deg": 10, "heading_deg": 90})
        self.assertFalse(res["passed"])
        self.assertIn("exceeds-escape-speed", rules(res["findings"], "error"))
        self.assertAlmostEqual(res["results"]["surface_rotation_speed_m_s"], 0.109083, delta=1e-6)
        self.assertAlmostEqual(res["results"]["inertial_launch_speed_m_s"], 0.258122, delta=1e-6)
        code = run_cli(SKILL, "lowg_calc", "hop", "--preset", "aster-target", "--speed", "0.15",
                       "--angle-deg", "10", "--heading-deg", "90", "--json").returncode
        self.assertEqual(code, 1)

    def test_no_heading_uses_worst_case(self):
        res = lg.run("hop", {"preset": "aster-target", "speed": 0.15, "angle_deg": 10})
        self.assertAlmostEqual(res["results"]["inertial_launch_speed_m_s"], 0.15 + 0.109083, delta=1e-6)
        self.assertIn("exceeds-escape-speed", rules(res["findings"], "error"))

    def test_westward_hop_and_warnings(self):
        res = lg.run("hop", {"preset": "aster-target", "speed": 0.15, "angle_deg": 10, "heading_deg": 270})
        self.assertNotIn("exceeds-escape-speed", rules(res["findings"], "error"))
        self.assertIn("surface-rotation-speed-significant", rules(res["findings"], "warning"))
        # worst case 0.03 + 0.109 = 0.139 m/s = 54 % of v_esc -> approaching warning, not error
        near = lg.run("hop", {"preset": "aster-target", "speed": 0.03, "angle_deg": 45})
        self.assertIn("approaching-escape-speed", rules(near["findings"], "warning"))
        self.assertTrue(near["passed"])
        with self.assertRaises(lg.InputError):
            lg.run("hop", {"preset": "aster-target", "speed": 0.01, "heading_deg": 400})

    def test_impulse_and_bounce_rotation_aware(self):
        imp = lg.run("impulse", {"preset": "aster-target", "mass_kg": 20, "speed": 0.16})
        self.assertIn("exceeds-escape-speed", rules(imp["findings"], "error"))
        # vertical rebound 0.24 m/s: sqrt(0.24^2 + 0.109^2) = 0.2636 > v_esc
        bn = lg.run("bounce", {"preset": "aster-target", "speed": 0.3, "restitution": 0.8,
                               "threshold_speed": 0.01})
        self.assertIn("rebound-exceeds-escape-speed", rules(bn["findings"], "error"))


class ImpulseBounceRotationTests(unittest.TestCase):
    def test_impulse_known_answer(self):
        r = lg.impulse(20.0, 0.05, angle_deg=30.0, push_time_s=0.5, g=G_ASTER, friction_coefficient=0.5)
        self.assertAlmostEqual(r["impulse_n_s"], 1.0, places=12)
        self.assertAlmostEqual(r["impulse_vertical_n_s"], 0.5, places=12)
        self.assertAlmostEqual(r["mean_force_n"], 2.0, places=12)
        self.assertAlmostEqual(r["weight_n"], 20 * G_ASTER, places=15)
        self.assertAlmostEqual(r["max_drive_accel_m_s2"], 0.5 * G_ASTER, places=15)
        with self.assertRaises(lg.InputError):
            lg.impulse(0, 0.05)
        with self.assertRaises(lg.InputError):
            lg.impulse(20, 0.05, friction_coefficient=0.5)

    def test_bounce_known_answer(self):
        # v0=0.1, e=0.5, vt=0.01: rebounds 0.05, 0.025, 0.0125 (0.00625 < vt) -> 3 rebounds;
        # time = 2*(0.05+0.025+0.0125)/0.001 = 175 s; infinite series 2*0.1*0.5/(0.001*0.5) = 200 s
        b = lg.bounce(0.1, 0.5, 0.01, 0.001)
        self.assertEqual(b["rebounds_above_threshold"], 3)
        self.assertEqual(b["contacts_to_settle"], 4)
        self.assertAlmostEqual(b["time_to_settle_s"], 175.0, places=9)
        self.assertAlmostEqual(b["infinite_series_time_s"], 200.0, places=9)
        self.assertLessEqual(b["time_to_settle_s"], b["infinite_series_time_s"])

    def test_bounce_below_threshold_and_validation(self):
        b = lg.bounce(0.005, 0.5, 0.01, 0.001)
        self.assertEqual(b["rebounds_above_threshold"], 0)
        self.assertEqual(b["time_to_settle_s"], 0.0)
        for e in (0.0, 1.0, 1.5, -0.1):
            with self.assertRaises(lg.InputError):
                lg.bounce(0.1, e, 0.01, 0.001)
        with self.assertRaises(lg.InputError):
            lg.bounce(0.1, 0.5, 0.0, 0.001)

    def test_rotation_known_answer_and_sign_flip(self):
        gm = lg.body(250, 1900)["gm_m3_s2"]
        r = lg.rotation(250, gm, 4.0)
        omega = 2 * math.pi / (4 * 3600)
        self.assertAlmostEqual(r["centrifugal_equator_m_s2"], omega ** 2 * 250, places=15)
        self.assertAlmostEqual(r["net_radial_gravity_m_s2"], G_ASTER - omega ** 2 * 250, delta=1e-9)
        # critical period = sqrt(3*pi/(G*rho)) = 2.3947 h for rho = 1900
        self.assertAlmostEqual(r["critical_period_h"], math.sqrt(3 * math.pi / (6.67430e-11 * 1900)) / 3600, places=9)
        pole = lg.rotation(250, gm, 4.0, latitude_deg=90)
        self.assertAlmostEqual(pole["centrifugal_radial_m_s2"], 0.0, places=15)
        fast = lg.run("rotation", {"preset": "fast-rotator-synthetic"})
        self.assertIn("net-gravity-outward", rules(fast["findings"], "error"))
        with self.assertRaises(lg.InputError):
            lg.rotation(250, gm, 4.0, latitude_deg=100)


class CliTests(unittest.TestCase):
    def test_pass_batch(self):
        code, out = run_json(SKILL, "lowg_calc", "batch", EX / "lowg-cases-pass.json")
        self.assertEqual(code, 0, out["findings"])
        assert_schema(self, out, SCH / "lowg-report.schema.json")
        assert_schema(self, json.loads((EX / "lowg-cases-pass.json").read_text(encoding="utf-8")),
                      SCH / "lowg-cases.schema.json")

    def test_fail_batch(self):
        code, out = run_json(SKILL, "lowg_calc", "batch", EX / "lowg-cases-fail.json")
        self.assertEqual(code, 1)
        errs = rules(out["findings"], "error")
        for r in ["exceeds-escape-speed", "exceeds-orbital-speed", "net-gravity-outward",
                  "rebound-exceeds-escape-speed"]:
            self.assertIn(r, errs)
        warns = rules(out["findings"], "warning")
        self.assertIn("flat-gravity-approx-questionable", warns)
        self.assertIn("range-large-vs-radius", warns)
        assert_schema(self, out, SCH / "lowg-report.schema.json")

    def test_single_commands_json(self):
        code, out = run_json(SKILL, "lowg_calc", "body", "--radius-m", "250", "--density", "1900")
        self.assertEqual(code, 0)
        self.assertAlmostEqual(out["results"]["body"]["surface_gravity_m_s2"], 1.328e-4, delta=1e-7)
        assert_schema(self, out, SCH / "lowg-report.schema.json")
        code, out = run_json(SKILL, "lowg_calc", "hop", "--g", "1.32797e-4", "--speed", "0.05")
        self.assertEqual(code, 0)
        self.assertIn("no-body-check", rules(out["findings"], "info"))

    def test_invalid_inputs_exit_2(self):
        cases = [("bounce", "--g", "0.001", "--speed", "0.1", "--restitution", "1.2", "--threshold-speed", "0.01"),
                 ("hop", "--g", "0.001", "--speed", "0.1", "--angle-deg", "120"),
                 ("body", "--radius-m", "-5", "--density", "1900"),
                 ("body", "--radius-m", "250"),
                 ("impulse", "--mass-kg", "0", "--speed", "0.1"),
                 ("batch", "missing.json")]
        for c in cases:
            self.assertEqual(run_cli(SKILL, "lowg_calc", *c).returncode, 2, c)

    def test_empty_batch_is_input_error(self):
        with self.assertRaises(lg.InputError):
            lg.run_batch({"cases": []})
        with self.assertRaises(lg.InputError):
            lg.run_batch({"cases": [{"id": "X", "command": "fly", "params": {}}]})


if __name__ == "__main__":
    unittest.main()
