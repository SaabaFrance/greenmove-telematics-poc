import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from moteur import contains

BASE = Path(__file__).parent.resolve()


class Demo(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.data = self.root/"data"
        shutil.copytree(BASE/"data", self.data)
        self.score = self.root/"daily_score.json"

    def run_demo(self, *args):
        return subprocess.run([sys.executable, str(BASE/"moteur.py"), "--data",
                               str(self.data), "--sortie", str(self.score), *args],
                              capture_output=True, text=True)

    def test_annexe(self):
        run = self.run_demo()
        self.assertEqual(run.returncode, 0)
        self.assertEqual(run.stdout.count("[ALERT ZFE]"), 1)
        self.assertIn("08:00:20 OUT", run.stdout)
        self.assertIn("08:00:30 IN [ALERT ZFE]", run.stdout)
        score = json.loads(self.score.read_text())
        self.assertEqual((score["mesures"], score["score_demo"]), (10,90))
        self.assertEqual(score["evenements"], [{"timestamp":1678880005,"min_y_m_s2":-3.45}])

    def test_unite_g(self):
        self.assertEqual(self.run_demo("--seuil","24.516625").returncode, 0)
        self.assertEqual(json.loads(self.score.read_text())["freinages"],0)

    def test_bord(self):
        poly = [(0,0),(2,0),(0,2),(0,0)]
        for point,expected in [((0,0),True),((1,1),True),((1.8,1.8),False),((3,3),False)]:
            self.assertEqual(contains(point,poly,(0,0,2,2)),expected)

    def test_csv_invalide(self):
        with (self.data/"accelerometer_data.csv").open("a") as f:
            f.write("1678880010,0,illisible,9.8\n")
        run = self.run_demo()
        self.assertEqual(run.returncode,0)
        self.assertIn("[CSV ignoré]",run.stdout)
        self.assertEqual(json.loads(self.score.read_text())["ignorees"],1)

    def test_geo_indisponible(self):
        (self.data/"lyon_polygon.json").write_text("{")
        run = self.run_demo()
        self.assertEqual(run.returncode,1)
        self.assertIn("[Geo indisponible]",run.stdout)
        self.assertTrue(self.score.exists())

    def test_seuil_et_regroupement(self):
        csv = self.data/"accelerometer_data.csv"
        csv.write_text("timestamp,acc_x,acc_y,acc_z\n"+ "".join(
            f"{1678880000+i},0,{y},9.81\n" for i,y in enumerate([-2.5,-3,-4,-2.4,-3,-1,-3])))
        self.assertEqual(self.run_demo().returncode,0)
        self.assertEqual(json.loads(self.score.read_text())["freinages"],2)


if __name__ == "__main__":
    unittest.main()
