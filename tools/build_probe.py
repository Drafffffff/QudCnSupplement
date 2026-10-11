#!/usr/bin/env python3
"""Create a test-only mod that queries every exported string key through the real engine."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=json.loads((ROOT/'data/audit-fields.json').read_text());cases={}
for x in a:
    path,attr=ast.literal_eval(x['path'])
    if path[-1][0]!='string' or attr not in {'#text','Value'}:continue
    attrs=dict(path[-1][1]);key=attrs.get('ID')
    if key is not None:cases[(attrs.get('Context',''),key)]=x['translation'].strip() if attr=='#text' else x['translation']
p=ROOT/'analysis/private/qa-mod';p.mkdir(parents=True,exist_ok=True)
(p/'manifest.json').write_text(json.dumps({'ID':'QudCnTestProbe','Title':'CN runtime QA probe','Version':'0.1.0','LoadAfter':['QudCnSupplement']}))
q=lambda s:json.dumps(s,ensure_ascii=False)
lines=['using System; using XRL;','[HasModSensitiveStaticCache] public static class QudCnTestProbe {','static int ok, fail;','[ModSensitiveCacheInit] public static void Init() { ok=fail=0;']
items=list(cases.items());chunks=[items[n:n+100] for n in range(0,len(items),100)]
for n in range(len(chunks)):lines.append('Check'+str(n)+'();')
lines.append('UnityEngine.Debug.Log("[CN-QA] runtime strings="+ok+"/"+(ok+fail)+"; mismatches="+fail); TestMessageQueue(); }')
for n,chunk in enumerate(chunks):
    lines.append('static void Check'+str(n)+'(){ string actual;')
    for (ctx,key),expected in chunk:
        lines.append('actual=XRL.Language.Strings._S('+q(ctx)+','+q(key)+'); if(actual==QudCnSupplement.TranslateExact('+q(expected)+')) ok++; else { fail++; if(fail<=30) UnityEngine.Debug.Log("[CN-QA] MISS " + '+q(ctx)+' + " => " + actual); }')
    lines.append('}')
lines.append('static void TestMessageQueue() { var queue = new XRL.Messages.MessageQueue(); queue.Add("You hit (x2) for 3 damage with 你的 青铜匕首! [7]"); queue.Add("You equip the {{W|火把}}."); foreach(var text in queue.Messages) UnityEngine.Debug.Log("[CN-QA] MessageQueue: " + text); }')
lines.append('}')
(p/'Probe.cs').write_text('\n'.join(lines))
print('runtime string cases',len(cases))
