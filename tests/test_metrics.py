import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from metrics import auc,catch_rate
from validate import _same_up_to_container
class MetricsTests(unittest.TestCase):
 def test_ties(self):
  self.assertEqual(auc([0,0],[0]),0.5)
  self.assertAlmostEqual(catch_rate([0]*100,[0]),0.02)
 def test_separation(self):
  self.assertEqual(auc([0,1],[2]),1)
  self.assertEqual(auc([2],[0,1]),0)
  self.assertEqual(catch_rate([0]*98+[3]*2,[0,0]),0)
 def test_boundaries(self):
  self.assertEqual(catch_rate([0],[1],0),0)
  self.assertEqual(catch_rate([0],[1],1),1)
  for b in [-0.1,1.1]:
   with self.assertRaises(ValueError):catch_rate([0],[1],b)
  with self.assertRaises(ValueError):auc([], [1])
 def test_documented_validator_blind_spot(self):
  # Preserve historical labeling; expose that the current checker ignores order.
  self.assertTrue(_same_up_to_container('[1,2]','[2,1]'))
if __name__=='__main__':unittest.main()
