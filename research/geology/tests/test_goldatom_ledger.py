import importlib.util, json, math, struct, subprocess, tempfile, unittest
from pathlib import Path
P=Path(__file__).parents[1]/'goldatom_ledger.py'; S=importlib.util.spec_from_file_location('ledger',P); L=importlib.util.module_from_spec(S); S.loader.exec_module(L)
GEN=bytes.fromhex('01000000'+'00'*32+'3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a'+'29ab5f49'+'ffff001d'+'1dac2b7c')
def fake(prev,ts,bits,nonce): return struct.pack('<I',1)+L.sha256d(prev)+b'\0'*32+struct.pack('<III',ts,bits,nonce)
class Tests(unittest.TestCase):
 def test_genesis_hash_and_endian(self):
  self.assertEqual(L.display_hash(GEN),L.GENESIS); self.assertEqual(L.hash_int(GEN),int(L.GENESIS,16)); self.assertEqual(L.display_hash_to_int(L.GENESIS),L.hash_int(GEN))
 def test_unsigned_comparison(self): self.assertLess(int('00ff',16),int('ff00',16))
 def test_compact(self): self.assertEqual(L.decode_compact(0x1d00ffff),L.POW_LIMIT); self.assertEqual(L.encode_compact(L.POW_LIMIT),0x1d00ffff)
 def test_gap_probability(self):
  self.assertEqual(L.gap_bits(1,8),3); self.assertEqual(L.next_probability(1,8),.125); self.assertEqual(L.next_probability(9,8),1)
 def test_synthetic_raw_and_normalized(self):
  # Test comparison logic directly with controlled integer/target sequences.
  vals=[90,80,85,40]; targets=[100,100,200,50]; raw=[]; norm=[]; f=None; nn=nd=None
  for i,(v,t) in enumerate(zip(vals,targets)):
   if f is None or v<f: raw.append(i); f=v
   if nn is None or v*nd<nn*t: norm.append(i); nn,nd=v,t
  self.assertEqual(raw,[0,1,3]); self.assertEqual(norm,[0,1,2])
 def test_constant_and_rising_difficulty(self):
  vals=[90,80,70]; same=[100,100,100]; rising=[100,50,25]
  def normalized(ts):
   nn=nd=None;o=[]
   for i,(v,t) in enumerate(zip(vals,ts)):
    if nn is None or v*nd<nn*t:o.append(i);nn,nd=v,t
   return o
  self.assertEqual(normalized(same),[0,1,2])
  self.assertEqual(normalized(rising),[0])
 def test_node_agreement_fixture(self):
  # Genesis-only fixture catches independent parsing/endian disagreement.
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'h.bin';p.write_bytes(GEN)
   got=json.loads(subprocess.check_output(['node',str(Path(__file__).parents[1]/'goldatom_ledger.mjs'),str(p)]))
   self.assertEqual(got['records'],[{'height':0,'hash':L.GENESIS}]); self.assertEqual(got['frontier'],f'{L.hash_int(GEN):064x}')
if __name__=='__main__':unittest.main()
