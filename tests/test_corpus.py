import collections,json,re,sys,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
class CorpusTests(unittest.TestCase):
 def test_export_scope_and_missing(self):
  summary=json.loads((ROOT/'data/coverage-summary.json').read_text())
  self.assertEqual(summary['total_source_fields'],25090)
  self.assertEqual(summary['unresolved_fields'],0)
  self.assertEqual(json.loads((ROOT/'data/unresolved.json').read_text()),[])
 def test_xml_and_export_markers(self):
  files=list((ROOT/'mod/languages/lang-CN').glob('*.xml'))
  self.assertGreaterEqual(len(files),21)
  for p in files:
   root=ET.parse(p).getroot()
   self.assertEqual(root.get('Lang'),'CN',p.name)
   self.assertNotIn('▶',p.read_text(),p.name)
 def test_new_translation_tokens(self):
  token=lambda s:collections.Counter(re.findall(r'=(?=[A-Za-z])[A-Za-z][^=]*=',s))
  for x in json.loads((ROOT/'data/audit-fields.json').read_text()):
   if x['status'] in {'manual','tw_converted','tw_id_fallback','cn_text_reuse','cn_id_fallback'}:
    self.assertEqual(token(x['source']),token(x['translation']),x['path'])
 def test_unchanged_input_snapshots(self):
  import hashlib
  for n,h in json.loads((ROOT/'data/snapshot-sha256.json').read_text()).items():
   self.assertEqual(hashlib.sha256((ROOT/'sources'/n).read_bytes()).hexdigest(),h,n)
if __name__=='__main__':unittest.main()
