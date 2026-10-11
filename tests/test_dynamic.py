"""Source-data regression tests; real C# SelfTest also runs in the game at Init."""
import re
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT/'mod/QudCnSupplementData.cs').read_text()
PAIRS = re.findall(r'Tuple.Create\(new Regex\(@"((?:""|[^"])*)", RegexOptions.IgnoreCase\), "((?:\\.|[^"\\])*)"\)', DATA)
def translate(s):
    for pattern, value in PAIRS:
        m = re.match(pattern, s, re.I)
        if m:
            result = re.sub(r'\$(\d+)', lambda g: m.group(int(g[1])) or '', value)
            return re.sub(r'\b(?:the|a|an)\s+(?=[\u3400-\u9fff])', '', result, flags=re.I)
    return s
class DynamicTests(unittest.TestCase):
    def test_screenshots(self):
        self.assertEqual(translate('你 equip the 火把'), '你装备了火把。')
        self.assertEqual(translate('The 熊 misses 使用 his 撕咬 未命中你! [2 对 7]'), '熊用撕咬攻击你，但未命中！[2 对 7]')
        self.assertEqual(translate('你将 the 古怪小饰物 识别为 a 化学电池'), '你将古怪小饰物识别为化学电池。')
        self.assertEqual(translate('You hit (x2) for 3 damage with 你的 青铜匕首! [7]'), '你用 你的 青铜匕首 击中(x2)，造成 3 伤害[7]')
    def test_names_and_markup(self):
        for name in ['Will', 'Hope-in-Motion', 'Walk', 'Red Rock', 'May the 王']:
            self.assertEqual(translate(name), name)
        self.assertEqual(translate('You equip the {{W|火把}}.'), '你装备了 {{W|火把}}。')
        self.assertEqual(translate('You hit Hope-in-Motion for 3 damage with Will! [7]'), '你用 Will 击中 Hope-in-Motion，造成 3 伤害[7]')
    def test_typed_damage_ability_and_death(self):
        self.assertEqual(translate('You take 4 damage from freezing!'), '你因冰冻受到4伤害。')
        self.assertEqual(translate('The 熊 dies!'), '熊 死亡。')
        self.assertEqual(translate('You emit a freezing ray from your hands!'), '你从双手射出一道冰冻射线。')
        self.assertEqual(translate('The 熊 emits a flaming ray from its hands!'), '熊从双手射出一道火焰射线。')
        self.assertEqual(translate('You were killed by Hope-in-Motion!'), '你被 Hope-in-Motion 击杀。')
        self.assertEqual(translate('You toggle 力场 on.'), '你将力场开启。')
        self.assertEqual(translate('You toggle 力场 off.'), '你将力场关闭。')
    def test_combinations_and_idempotence(self):
        for target in ['Hope-in-Motion','Will','熊','{{R|熊}}']:
            for weapon in ['May','青铜匕首','{{W|青铜匕首}}']:
                for damage in ['1','9','300']:
                    text=f'You hit {target} for {damage} damage with {weapon}! [7]'
                    actual=translate(text)
                    self.assertEqual(actual,f'你用 {weapon} 击中 {target}，造成 {damage} 伤害[7]')
                    self.assertEqual(translate(actual),actual)
    def test_guards_and_bounds(self):
        source=(ROOT/'mod/QudCnSupplement.cs').read_text()
        self.assertIn('Options.Language == "CN"',source)
        for method in ['EffectPostfix','MessagePrefix','GeneratedPostfix','StringPostfix','DisplayPrefix','PopupPrefix']:
            body=source[source.index('public static void '+method):].split('\n    }',1)[0]
            self.assertIn('!IsChinese',body)
        self.assertIn('MaxDiagnosticEntries = 256', source)
        self.assertIn('type.ContainsGenericParameters', source)
        self.assertIn('method.ContainsGenericParameters', source)
        self.assertIn('method.IsAbstract', source)
        self.assertIn('NeedsReview(__result)', source)
        self.assertNotIn('VariableReplacer(', source)
    def test_patterns_are_anchored(self):
        self.assertGreater(len(PAIRS),90)
        for p,_ in PAIRS:
            self.assertTrue(p.startswith('^') and p.endswith('$'),p)
if __name__=='__main__':unittest.main()
