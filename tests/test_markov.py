"""Build-time invariants for the separate, language-conditional Chinese corpus.
These do not substitute for executing the shipped game generator.
"""
import hashlib
import importlib.util
import json
import logging
from pathlib import Path
import random
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_markov', ROOT/'tools/build_markov.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class ChineseMarkovTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads((ROOT/'mod/LibraryCorpus.CN.json').read_text())
        cls.audit = json.loads((ROOT/'data/markov-audit.json').read_text())
        cls.chain = dict(zip(cls.corpus['keys'], [v.split('\x01') for v in cls.corpus['values']]))

    def test_native_json_shape(self):
        self.assertEqual(set(self.corpus), {'order', 'OpeningWords', 'keys', 'values'})
        self.assertEqual(self.corpus['order'], 2)
        self.assertEqual(len(self.corpus['keys']), len(self.corpus['values']))
        self.assertEqual(len(self.chain), len(self.corpus['keys']))
        self.assertGreater(len(self.chain), 20000)
        self.assertTrue(all(len(k.split(' ')) == 2 for k in self.chain))
        self.assertTrue(all(len(k.split(' ')) == 2 and k in self.chain for k in self.corpus['OpeningWords']))

    def test_language_and_lexical_segmentation(self):
        for key, successors in self.chain.items():
            for word in key.split(' ') + successors:
                self.assertFalse(re.search(r'[A-Za-z=|{}@\x00]', word), word)
                self.assertNotIn(' ', word)
                self.assertNotIn('。', word)  # Native generator requires ASCII periods.
                self.assertLessEqual(len(word.rstrip(',.')), 8, word)
                self.assertRegex(word, r'[\u3400-\u9fff0-9]')

    def test_graph_has_terminating_transitions(self):
        ends = 0
        for key, successors in self.chain.items():
            for word in successors:
                if word.endswith('.'):
                    ends += 1
                else:
                    self.assertIn(key.split(' ')[1] + ' ' + word, self.chain)
        self.assertGreater(ends, 3000)

    def test_artifact_is_reproducible(self):
        builder.jieba.setLogLevel(logging.ERROR)
        tokenizer = builder.jieba.Tokenizer()
        tokenizer.initialize()
        corpus, _ = builder.build(json.loads(builder.INPUT.read_text()), tokenizer)
        self.assertEqual(corpus, self.corpus)
        payload = (ROOT/'mod/LibraryCorpus.CN.json').read_bytes()
        self.assertEqual(hashlib.sha256(payload).hexdigest(), self.audit['output_sha256'])
        self.assertEqual(hashlib.sha256(builder.INPUT.read_bytes()).hexdigest(), self.audit['input_sha256'])

    def test_reference_chain_sampling(self):
        # Bounded graph smoke check only: actual GenerateTitle/GenerateParagraph
        # output must be checked separately against the shipped Assembly-CSharp.
        for seed in range(100):
            rng = random.Random(seed)
            words = rng.choice(self.corpus['OpeningWords']).split(' ')
            for _ in range(100):
                word = rng.choice(self.chain[' '.join(words[-2:])])
                words.append(word)
                if word.endswith('.'):
                    break
            self.assertTrue(words[-1].endswith('.'), f'seed {seed}: no stop in 100 steps')
            self.assertLessEqual(len(''.join(words)), 400)

    def test_templates_excluded_and_colours_unwrapped(self):
        self.assertEqual(builder.strip_formatting('{{W|{{R|达贡}}之书}}'), '达贡之书')
        tokenizer = builder.jieba.Tokenizer()
        sample = {'file': 'Books.example.xml', 'path': "((('book', (('ID', 'sample'),), 1), ('page', (), 1)), '#text')",
                  'translation': '神秘的=entity.name=正在此地旅行。English book.演说家达贡以傲慢姿态统御西方。'}
        corpus, audit = builder.build([sample], tokenizer)
        self.assertEqual(audit['accepted_sentences'], 1)
        self.assertEqual(audit['excluded_sentences']['dynamic_template'], 1)
        self.assertEqual(audit['excluded_sentences']['residual_latin_or_identifier'], 1)
        self.assertNotIn('English', json.dumps(corpus, ensure_ascii=False))

if __name__ == '__main__':
    unittest.main()
