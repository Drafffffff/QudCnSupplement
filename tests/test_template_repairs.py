import collections
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('template_repairs', ROOT/'tools/build_template_repairs.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TemplateRepairsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repairs=json.loads((ROOT/'data/template-repairs.json').read_text())
        cls.baseline={(x['file'],x['path']):x for x in json.loads((ROOT/'data/template-grammar-baseline.json').read_text())}

    def test_unique_fields_and_exact_baseline(self):
        keys=[(x['file'],x['path']) for x in self.repairs]
        self.assertEqual(len(keys),len(set(keys)))
        for r in self.repairs:
            self.assertEqual(r['before'],self.baseline[(r['file'],r['path'])]['translation'])
            self.assertEqual(r['after'],m.fix(r['before'])[0])

    def test_only_explicit_tokens_change(self):
        for r in self.repairs:
            old=collections.Counter(m.TOKEN.findall(r['before']))
            new=collections.Counter(m.TOKEN.findall(r['after']))
            for c in r['changes']:
                self.assertTrue(c['reason'])
                if c.get('kind')=='literal':
                    self.assertEqual(c['before_token'],'关闭')
                    continue
                self.assertIn(c['before_token'],r['before'])
                old.subtract(m.TOKEN.findall(c['before_token']))
                new.subtract(m.TOKEN.findall(c['after']))
            self.assertEqual(+old,+new,r['before'])

    def test_untouched_numeric_and_object_variables(self):
        for r in self.repairs:
            touched=collections.Counter(c['before_token'] for c in r['changes'])
            for tok in m.TOKEN.findall(r['before']):
                if not touched[tok]:
                    inserted=sum(m.TOKEN.findall(c['after']).count(tok) for c in r['changes'])
                    self.assertEqual(m.TOKEN.findall(r['before']).count(tok)+inserted,m.TOKEN.findall(r['after']).count(tok),(r['before'],tok))

    def test_idempotence_and_exact_apply(self):
        for r in self.repairs:
            self.assertEqual(m.fix(r['after'])[0],r['after'])
            def apply(value):
                if value==r['after']:return value
                if value!=r['before']:raise ValueError('stale exact-field repair')
                return r['after']
            self.assertEqual(apply(r['before']),r['after'])
            self.assertEqual(apply(r['after']),r['after'])
            with self.assertRaises(ValueError):apply('changed baseline:'+r['before'])

    def test_all_static_english_verbs_repaired(self):
        for r in self.repairs:
            for tok in m.TOKEN.findall(r['after']):
                self.assertIsNone(m.VERB.fullmatch(tok),(r['after'],tok))

    def test_proper_names_colors_and_player_input_preserved(self):
        s="{{G|=subject.Does:emit= 从 =subject.its= =part.ordinalName= 发出一道冻结射线！}} [=damage=] =playerName= =generatedPlace="
        a=m.fix(s)[0]
        self.assertIn('{{G|',a)
        for t in ['=subject.its=','=part.ordinalName=','=damage=','=playerName=','=generatedPlace=']:
            self.assertIn(t,a)
        self.assertEqual(m.fix('Captain John 与 Camp Qud')[0],'Captain John 与 Camp Qud')

    def test_pronoun_verb_only_and_possessive_semantics(self):
        self.assertEqual(m.fix('=subject.it.does:gain= +8')[0],'=subject.it=获得 +8')
        self.assertEqual(m.fix('=subject.thisCreature= =subject.verb:are= 被点燃')[0],'=subject.thisCreature=  被点燃')
        self.assertEqual(m.fix("=object.the.name's:withTitles= 的肢体")[0],'=object.the.name:withTitles= 的肢体')
        self.assertEqual(m.fix("=object.The.name's=肢体")[0],'=object.The.name=的肢体')
        self.assertEqual(m.fix("=user.The.name's.item#subject=")[0],"=user.The.name's.item#subject=")
        self.assertEqual(m.fix('=subject.Does#verb=')[0],'=subject.Does#verb=')

    def test_context_sensitive_idioms(self):
        examples={
         '=subject.Does:swim= 在你眼前晃动！':'=subject.The.name= 在你眼前晃动！',
         '=subject.Does:wade= 涉过 =object.a.name=。':'=subject.The.name= 涉过 =object.a.name=。',
         '=subject.Does:extrude= 出 =object.a.name=！':'=subject.The.name=挤 出 =object.a.name=！',
         '=subject.Does:grow= 满身细小棘刺。':'=subject.The.name=长 满身细小棘刺。',
         '=subject.Does:staunch= 用 =item.a.name= 为 =object.the.name= 的伤口止血。':'=subject.The.name= 用 =item.a.name= 为 =object.the.name= 的伤口止血。',
         '=subject.Does:don\'t= 没有足够电量。':'=subject.The.name= 没有足够电量。',
        }
        for b,a in examples.items():self.assertEqual(m.fix(b)[0],a)

if __name__=='__main__':unittest.main()
