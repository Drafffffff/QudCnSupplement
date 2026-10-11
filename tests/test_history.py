import json,re,unittest,sys
from pathlib import Path
import json5
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_history import leaves,tokens
class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.output=json.loads((ROOT/'mod/historyspice.CN.json').read_text())
        self.base=dict(leaves(json5.loads((ROOT/'sources/HistorySpice.jsonc').read_text())['spice']))
        self.cn=dict(leaves(self.output['spice']))
    def test_language_and_coverage(self):
        self.assertEqual(self.output['lang'],'CN')
        self.assertEqual(set(self.base),set(self.cn))
        self.assertEqual(len(self.cn),1574)
    def test_replacement_semantics(self):
        def walk(x):
            for key,value in x.items():
                if isinstance(value,dict):walk(value)
                elif isinstance(value,list):self.assertTrue(key.endswith('='),key)
        walk(self.output['spice'])
    def test_code_and_weights(self):
        for path,bv in self.base.items():
            cv=self.cn[path]
            if path[-1].startswith('_'):self.assertEqual(bv,cv)
            bs=bv if isinstance(bv,list) else [bv];cs=cv if isinstance(cv,list) else [cv]
            self.assertEqual(len(bs),len(cs),path)
            for i,(b,c) in enumerate(zip(bs,cs)):
                if not isinstance(b,str):continue
                if path==('lovesick',) and i==4:continue
                self.assertEqual(tokens(b),tokens(c),(path,i))
                self.assertEqual((re.match(r'^\[x\d+\]',b) or [''])[0],(re.match(r'^\[x\d+\]',c) or [''])[0],(path,i))
    def test_no_visible_latin_fragments(self):
        for path,value in self.cn.items():
            if any(str(p).startswith(('_','@')) for p in path):continue
            for text in value if isinstance(value,list) else [value]:
                if not isinstance(text,str):continue
                visible=re.sub(r'=[^=]*=|\([^)]*\)|\{\{[^|]+\||\$[A-Za-z]+','',text)
                self.assertFalse(re.search(r'[A-Za-z]{3,}',visible),(path,text))
    def test_upstream_placeholder_repairs(self):
        self.assertEqual(self.cn[('gossip','twoFaction')][16],'=f1=为=f2=烹制了一顿腐败的餐点。')
        self.assertNotIn('PPPP',json.dumps(self.output,ensure_ascii=False))
if __name__=='__main__':unittest.main()
