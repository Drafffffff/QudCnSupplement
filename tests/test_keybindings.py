import json,re,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class KeybindingsTests(unittest.TestCase):
 def test_all_shipped_commands_and_categories(self):
  labels=json.loads((ROOT/'data/keybindings-ui.json').read_text())
  xml=ET.parse(ROOT/'sources/Commands.xml')
  expected={n.get(a).strip() for n in xml.iter('command') for a in ['DisplayText','Category'] if n.get(a)}
  self.assertEqual(set(labels),expected)
  for key,value in labels.items():
   self.assertRegex(value,r'[\u3400-\u9fff]',key)
   self.assertEqual(re.findall(r'\d[\d,]*',key),re.findall(r'\d[\d,]*',value),key)
 def test_screenshot_labels(self):
  labels=json.loads((ROOT/'data/keybindings-ui.json').read_text())
  for key in ['Mouse smart use','Mouse interact All','Show reachability map','Show FPS','Save game','Debug','Mouse-specific','Basic Move / Attack']:
   self.assertIn(key,labels)
  self.assertEqual(labels['Show FPS'],'显示帧率')
