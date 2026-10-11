"""Source-data regression tests; real C# SelfTest also runs in the game at Init."""
import re
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT/'mod/QudCnSupplementData.cs').read_text()
PAIRS = re.findall(r'Tuple.Create\(new Regex\(@"((?:""|[^"])*)", RegexOptions.IgnoreCase\), "((?:\\.|[^"\\])*)"\)', DATA)
COMPILED = [(re.compile(p,re.I),v) for p,v in PAIRS]
def translate(s):
    frame=re.fullmatch(r'\{\{([^{}|]+)\|(.*)\}\}(\s*\[[^\]]*\])?',s,re.S)
    if frame:
        inner=translate(frame[2])
        if inner!=frame[2]:return '{{'+frame[1]+'|'+inner+'}}'+(frame[3] or '')
    for pattern, value in COMPILED:
        m = pattern.match(s)
        if m:
            result = re.sub(r'\$(\d+)', lambda g: m.group(int(g[1])) or '', value)
            return re.sub(r'\b(?:the|a|an)\s+(?=(?:\{\{[^{}|]+\|)*[\u3400-\u9fff])', '', result, flags=re.I)
    return s
class DynamicTests(unittest.TestCase):
    def test_screenshots(self):
        self.assertEqual(translate('你 equip the 火把'), '你装备了火把。')
        self.assertEqual(translate('The 熊 misses 使用 his 撕咬 未命中你! [2 对 7]'), '熊用撕咬攻击你，但未命中！[2 对 7]')
        self.assertEqual(translate('你将 the 古怪小饰物 识别为 a 化学电池'), '你将古怪小饰物识别为化学电池。')
        self.assertEqual(translate('You hit (x2) for 3 damage with 你的 青铜匕首! [7]'), '你用 你的 青铜匕首 击中(x2)，造成 3 伤害[7]')
    def test_live_log_mixed_grammar(self):
        self.assertEqual(translate('你 take the 皮甲。'), '你拿取了皮甲。')
        self.assertEqual(translate('{{r|你 miss 使用 你的 {{w|青铜}}匕首 未命中！}} [2 对 5]'), '{{r|你用你的 {{w|青铜}}匕首攻击，但未命中！}} [2 对 5]')
    def test_live_running_and_source_effects(self):
        self.assertEqual(translate('你 begin 疾跑！'),'你开始疾跑！')
        self.assertEqual(translate('你 stop 疾跑。'),'你停止疾跑。')
        self.assertEqual(translate('{{freezing|冰封}} 熊 因 your freezing effect 受到 4 伤害'),'{{freezing|冰封}} 熊因你的冰冻效果受到4伤害')
        for subject in ['Will', 'Hope-in-Motion', '{{R|熊}}']:
            for verb,cn in [('begin','开始'),('begins','开始'),('began','开始'),('start','开始'),('stop','停止'),('stops','停止'),('stopped','停止')]:
                for suffix in ['！','!','。','.','']:
                    self.assertEqual(translate(f'{subject} {verb} 疾跑{suffix}'),f'{subject}{cn}疾跑{suffix}')
            for possessive,zh in [('your','你的'),('his','他的'),('her','她的'),('its','它的'),('their','他们的')]:
                for effect,cn in [('freezing','冰冻'),('burning','燃烧'),('electricity','电击')]:
                    actual=translate(f'{subject} 因 {possessive} {effect} effect 受到 17 伤害！')
                    self.assertEqual(actual,f'{subject}因{zh}{cn}效果受到17伤害！')
                    self.assertEqual(translate(actual),actual)
        self.assertEqual(translate("熊 因 Hope-in-Motion's freezing effect 受到 3 伤害。"),'熊因Hope-in-Motion的冰冻效果受到3伤害。')
    def test_mixed_ray_anatomy(self):
        self.assertEqual(translate('{{G|你 emit 从 你的 hands 发出一道冻结射线！}}'),'{{G|你从双手发出一道冰冻射线！}}')
        for part,cn in [('hand','手'),('hands','双手'),('left hand','左手'),('right hand','右手'),('second left hand','第二只左手'),('eyes','双眼'),('mouth','嘴')]:
            for ray,zh in [('冻结','冰冻'),('燃焰','火焰')]:
                actual=translate(f'你 emit 从 你的 {part} 发出一道{ray}射线！')
                self.assertEqual(actual,f'你从{cn}发出一道{zh}射线！')
                self.assertEqual(translate(actual),actual)
                self.assertEqual(translate(f'{{R|Will}} emits 从 他的 {part} 发出一道{ray}射线。'),f'{{R|Will}}从{cn}发出一道{zh}射线。')
                self.assertEqual(translate('你 emit 从 你的 {{W|'+part+'}} 发出一道'+ray+'射线！'),'你从{{W|'+cn+'}}发出一道'+zh+'射线！')
        self.assertEqual(translate('你 emit 出一道冻结射线！'),'你发出一道冰冻射线！')
        self.assertEqual(translate('你 emit 发出一道电磁脉冲。'),'你发出一道电磁脉冲。')
        self.assertEqual(translate('Hope-in-Motion emits 出研磨般的噪声。'),'Hope-in-Motion发出研磨般的噪声。')
        self.assertEqual(translate('熊 emit 一股{{fiery|火焰羽流}}！'),'熊喷出一股{{fiery|火焰羽流}}！')
        self.assertEqual(translate('你 emit 一股{{fiery|火焰羽流}}！'),'你喷出一股{{fiery|火焰羽流}}！')
    def test_unknown_name_fragments_not_guessed(self):
        for fragment in ['begin 疾跑', 'your freezing effect', 'hands', '{{G|hands}}','Will begins']:
            self.assertEqual(translate(fragment),fragment)
        self.assertEqual(translate('你 emit 从 你的 Hope-in-Motion 发出一道冻结射线！'),'你 emit 从 你的 Hope-in-Motion 发出一道冻结射线！')
    def test_physics_articles(self):
        for article in ['a', 'an', 'the', 'A']:
            self.assertEqual(translate(f'你经过了 {article} 铁门。'), '你经过了铁门。')
            self.assertEqual(translate(f'道路被 {article} 熟铁栅栏 挡住了。'), '道路被熟铁栅栏挡住了。')
        self.assertEqual(translate('你经过了 {{W|a 铁门}}。'), '你经过了{{W|铁门}}。')
        self.assertEqual(translate('你经过了 a 铁门和 a 木门。'), '你经过了铁门和 木门。')
        self.assertEqual(translate('a 铁门'), 'a 铁门')
        self.assertEqual(translate('May the 王'), 'May the 王')
        source=(ROOT/'mod/QudCnSupplement.cs').read_text()
        self.assertIn('!English.IsMatch(text) && !Article.IsMatch(text)', source)
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
        for method in ['EffectPostfix','MessagePrefix','GeneratedPostfix','StringPostfix','DisplayPrefix','PopupPrefix','TemplatePronounPostfix']:
            body=source[source.index('public static void '+method):].split('\n    }',1)[0]
            self.assertIn('!IsChinese',body)
        self.assertIn('MaxDiagnosticEntries = 256', source)
        self.assertIn('type.ContainsGenericParameters', source)
        self.assertIn('method.ContainsGenericParameters', source)
        self.assertIn('method.IsAbstract', source)
        self.assertIn('NeedsReview(__result)', source)
        self.assertNotIn('VariableReplacer(', source)
    def test_pronouns_are_template_scoped(self):
        source=(ROOT/'mod/QudCnSupplement.cs').read_text()
        self.assertIn('XRL.World.Text.Delegates.GameObjectReplacers',source)
        self.assertIn('"SubstantivePossessive"',source)
        self.assertIn('return possessive ? result + "的" : result',source)
        self.assertEqual(translate('she'), 'she')
    def test_patterns_are_anchored(self):
        self.assertGreater(len(PAIRS),90)
        for p,_ in PAIRS:
            self.assertTrue(p.startswith('^') and p.endswith('$'),p)
if __name__=='__main__':unittest.main()
