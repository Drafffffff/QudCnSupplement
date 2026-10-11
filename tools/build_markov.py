#!/usr/bin/env python3
"""Build a separate CN Markov corpus from reviewed localized prose (offline).
Install requirements-markov.txt. Run build_corpus.py first. This does not replace
LibraryCorpus.json: the runtime must select LibraryCorpus.CN.json only for CN.
"""
from pathlib import Path
import ast
import collections
import hashlib
import json
import logging
import re
import jieba

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/audit-fields.json'
OUTPUT = ROOT / 'mod/LibraryCorpus.CN.json'
CJK = re.compile(r'[\u3400-\u9fff]')
LATIN = re.compile(r'[A-Za-z]')
DYNAMIC = re.compile(r'=[^=\n]+=|@[^@\n]+@|\*[^*\n]+\*|<(?:spice|entity)[^>]*>', re.I)
FILES = {'Books.example.xml', 'Furniture.example.xml', 'Items.example.xml', 'Creatures.example.xml'}

def eligible(row):
    if row['file'] not in FILES:
        return False
    path, attr = ast.literal_eval(row['path'])
    return (row['file'] == 'Books.example.xml' and path[-1][0] == 'page' and attr == '#text') or (
        attr == 'Short' and path[-1][0] == 'part' and ('Name', 'Description') in path[-1][1])

def strip_formatting(text):
    # Formatting contains English color/style names; discard heads, keep prose.
    for _ in range(12):
        changed = re.sub(r'\{\{[^|{}]+\|([^{}]*)\}\}', r'\1', text)
        if changed == text:
            break
        text = changed
    text = re.sub(r'&[A-Za-z0-9^]|\^[A-Za-z0-9]', '', text)
    text = re.sub(r'\[\[([^\[\]]+)\]\]', r'\1', text)
    return text.replace('▶', '').replace('\u00a0', ' ')

def sentences(text):
    # Sentence boundaries remain ASCII periods in the chain, as required by the
    # shipped GenerateFragment/GenerateSentence implementation. Display code
    # may collapse spaces and restore Chinese punctuation after generation.
    text = strip_formatting(text)
    text = DYNAMIC.sub('@DYNAMIC@', text)
    return [s.strip() for s in re.split(r'[。！？.!?\n\r]+', text) if s.strip()]

def tokenize(sentence, tokenizer):
    # No arbitrary long "word": genuine Chinese lexical segmentation followed
    # by a conservative size cap for unknown proper names. Punctuation is joined
    # to a preceding word so engine word counting remains meaningful.
    sentence = re.sub(r'[，、；：]', ',', sentence)
    sentence = re.sub(r'[“”‘’「」『』（）()【】\[\]<>《》"\\/|{}=_~#*+•·—…]', '', sentence)
    result = []
    for word in tokenizer.cut(sentence, HMM=False):
        word = word.strip()
        if not word:
            continue
        if word == ',':
            if result and not result[-1].endswith(','):
                result[-1] += ','
            continue
        if not (CJK.search(word) or word.isdecimal()):
            continue
        if len(word) > 8:
            result.extend(word[i:i+2] for i in range(0, len(word), 2))
        else:
            result.append(word)
    if result:
        result[-1] = result[-1].rstrip(',') + '.'
    return result

def build(rows, tokenizer):
    chain = collections.defaultdict(list)
    openings = []
    excluded = collections.Counter()
    contributions = []
    accepted = 0
    tokens = 0
    for row in rows:
        if not eligible(row):
            continue
        count = 0
        for sentence in sentences(row['translation']):
            if DYNAMIC.search(sentence):
                excluded['dynamic_template'] += 1
                continue
            if LATIN.search(sentence):
                excluded['residual_latin_or_identifier'] += 1
                continue
            if not CJK.search(sentence):
                excluded['no_chinese_prose'] += 1
                continue
            words = tokenize(sentence, tokenizer)
            if len(words) < 4:
                excluded['fewer_than_four_tokens'] += 1
                continue
            openings.append(' '.join(words[:2]))
            # A state always consists of two lexical words, including punctuation
            # attached to words. Never flatten translated paragraphs into keys.
            for i in range(len(words)-2):
                chain[' '.join(words[i:i+2])].append(words[i+2])
            count += 1
            accepted += 1
            tokens += len(words)
        if count:
            contributions.append({'file': row['file'], 'path': row['path'], 'sentences': count})
    keys = sorted(chain)
    corpus = {'order': 2, 'OpeningWords': openings, 'keys': keys,
              'values': ['\x01'.join(chain[key]) for key in keys]}
    audit = {'input': 'data/audit-fields.json', 'input_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(),
             'output': 'mod/LibraryCorpus.CN.json', 'language': 'CN', 'order': 2,
             'jieba_version': jieba.__version__, 'segmentation': 'jieba HMM=False; max lexical token length 8',
             'scope': sorted(FILES), 'accepted_sentences': accepted, 'lexical_tokens': tokens,
             'opening_words': len(openings), 'chain_states': len(keys),
             'excluded_sentences': dict(sorted(excluded.items())), 'contributions': contributions,
             'runtime_selection_required': True, 'rewrites_existing_saved_titles': False}
    return corpus, audit

def main():
    jieba.setLogLevel(logging.ERROR)
    tokenizer = jieba.Tokenizer()
    tokenizer.initialize()
    corpus, audit = build(json.loads(INPUT.read_text()), tokenizer)
    if not corpus['keys']:
        raise ValueError('No eligible translated prose')
    payload = json.dumps(corpus, ensure_ascii=False, separators=(',', ':')) + '\n'
    OUTPUT.write_text(payload, encoding='utf-8')
    audit['output_sha256'] = hashlib.sha256(payload.encode()).hexdigest()
    dictionary = Path(jieba.__file__).parent / 'dict.txt'
    audit['segmenter_dictionary_sha256'] = hashlib.sha256(dictionary.read_bytes()).hexdigest()
    (ROOT / 'data/markov-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='contributions'}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
