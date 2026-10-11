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
  changes={(x['file'],x['path']):x for x in json.loads((ROOT/'data/unit-operation-audit.json').read_text())['entries']}
  for x in json.loads((ROOT/'data/audit-fields.json').read_text()):
   if x['status'] in {'manual','tw_converted','tw_id_fallback','cn_text_reuse','cn_id_fallback'}:
    if token(x['source'])==token(x['translation']):continue
    change=changes.get((x['file'],x['path']))
    self.assertIsNotNone(change,x['path'])
    self.assertEqual(change['source'],x['source'])
    self.assertEqual(change['translation'],x['translation'])
    # Every other variable must match the source before only the reviewed noun operation changes.
    self.assertEqual(token(x['source']),token(change['baseline_translation']),x['path'])
 def test_literal_unit_operation_audit(self):
  token=lambda s:collections.Counter(re.findall(r'=(?=[A-Za-z])[A-Za-z][^=]*=',s))
  units=json.loads((ROOT/'data/literal-units.json').read_text())
  rows=json.loads((ROOT/'data/unit-operation-audit.json').read_text())['entries']
  self.assertGreater(len(rows),30)
  for row in rows:
   rebuilt=row['baseline_translation'];expected=token(rebuilt)
   for change in row['changes']:
    old=change['removed_token'];match=re.fullmatch(r'=([A-Za-z][^=\n:]*?)\.(pluralize|things):([^=:\n|]+)=',old)
    self.assertIsNotNone(match,old)
    base,operation,word=match.groups();unit=units.get(word,word)
    self.assertRegex(unit,r'[\u3400-\u9fff]')
    replacement=unit if operation=='pluralize' else '='+base+'= '+unit
    self.assertEqual(change['replacement'],replacement)
    self.assertIn(old,rebuilt)
    rebuilt=rebuilt.replace(old,replacement,1)
    expected.subtract({old:1});expected.update(token(replacement))
    if operation=='things':self.assertIn('='+base+'=',replacement)
   self.assertEqual(rebuilt,row['translation'],row['path'])
   self.assertEqual(+expected,token(row['translation']),row['path'])
 def test_no_chinese_single_noun_pluralization(self):
  for row in json.loads((ROOT/'data/audit-fields.json').read_text()):
   self.assertNotRegex(row['translation'],r'=([A-Za-z][^=\n:]*?)\.(pluralize|things):[^=:\n|]*[\u3400-\u9fff][^=:\n|]*=',row['path'])
   self.assertNotRegex(row['translation'],r'\.(pluralize|things):dram=',row['path'])
 def test_unchanged_input_snapshots(self):
  import hashlib
  for n,h in json.loads((ROOT/'data/snapshot-sha256.json').read_text()).items():
   self.assertEqual(hashlib.sha256((ROOT/'sources'/n).read_bytes()).hexdigest(),h,n)
if __name__=='__main__':unittest.main()
