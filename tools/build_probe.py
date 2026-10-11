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
lines.append('UnityEngine.Debug.Log("[CN-QA] runtime strings="+ok+"/"+(ok+fail)+"; mismatches="+fail); TestMessageQueue(); TestHistory(); TestPronouns(); TestGrammar(); }')
for n,chunk in enumerate(chunks):
    lines.append('static void Check'+str(n)+'(){ string actual;')
    for (ctx,key),expected in chunk:
        lines.append('actual=XRL.Language.Strings._S('+q(ctx)+','+q(key)+'); if(actual==QudCnSupplement.TranslateExact('+q(expected)+')) ok++; else { fail++; if(fail<=30) UnityEngine.Debug.Log("[CN-QA] MISS " + '+q(ctx)+' + " => " + actual); }')
    lines.append('}')
lines.append('static void TestMessageQueue() { var queue = new XRL.Messages.MessageQueue(); queue.Add("You hit (x2) for 3 damage with 你的 青铜匕首! [7]"); queue.Add("You equip the {{W|火把}}."); queue.Add("你经过了 a 铁门。"); queue.Add("道路被 a 熟铁栅栏 挡住了。"); queue.Add("你 take the 皮甲。"); queue.Add("{{r|你 miss 使用 你的 {{w|青铜}}匕首 未命中！}} [2 对 5]"); queue.Add("你 begin 疾跑！"); queue.Add("你 stop 疾跑。"); queue.Add("{{freezing|冰封}} 熊 因 your freezing effect 受到 4 伤害"); queue.Add("{{G|你 emit 从 你的 hands 发出一道冻结射线！}}"); foreach(var text in queue.Messages) UnityEngine.Debug.Log("[CN-QA] MessageQueue: " + text); UnityEngine.Debug.Log("[CN-QA] Chinese pluralize="+XRL.Language.Grammar.Pluralize("打兰")); string before=XRL.UI.Options.Language; try { XRL.UI.Options.Language="en"; string original="You equip the torch."; string after=original; QudCnSupplement.MessagePrefix(ref after); UnityEngine.Debug.Log("[CN-QA] English guard="+(after==original)); } finally { XRL.UI.Options.Language=before; } }')
lines.append('''static void TestHistory() {
    try {
        HistoryKit.HistoricSpice.CheckInit();
        var field=typeof(HistoryKit.HistoricSpice).GetField("_root",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);
        if(field==null) throw new Exception("HistoricSpice._root missing");
        var root=field.GetValue(null) as Newtonsoft.Json.Linq.JObject;
        if(root==null) throw new Exception("HistoricSpice._root not loaded JObject");
        int passed=0;
        string glass=(string)root["elements"]["glass"]["materials"][0];
        string dice=(string)root["elements"]["chance"]["nouns"][0];
        string redirect=(string)root["friendOrFoe"]["_failureredirect"];
        if(glass=="玻璃") passed++; else UnityEngine.Debug.Log("[CN-QA] history FAIL glass="+glass);
        if(dice=="=spice:numbers.!random=面骰子") passed++; else UnityEngine.Debug.Log("[CN-QA] history FAIL dice="+dice);
        if(redirect=="spice.friendOrFoe.default") passed++; else UnityEngine.Debug.Log("[CN-QA] history FAIL redirect="+redirect);
        UnityEngine.Debug.Log("[CN-QA] history="+passed+"/3; glass="+glass+"; dice="+dice+"; redirect="+redirect);
        string expanded=HistoryKit.HistoricStringExpander.ExpandString("=spice:elements.glass.materials.!random=",new System.Random(1234));
        bool expandedChinese=expanded=="玻璃" || expanded=="沙子";
        UnityEngine.Debug.Log("[CN-QA] history expansion="+(expandedChinese?"PASS":"FAIL")+"; value="+expanded);
    } catch(Exception e) { UnityEngine.Debug.Log("[CN-QA] history=FAIL EX "+e.GetType().Name+": "+e.Message); }
}''')
lines.append(r'''static void TestPronouns() {
    string language=XRL.UI.Options.Language;
    try {
        var obj=new XRL.World.GameObject(); obj.SetGender("female");
        var assembly=typeof(XRL.World.GameObject).Assembly;
        var ctx=System.Activator.CreateInstance(assembly.GetType("XRL.World.Text.Delegates.VariableContext"), true);
        var type=assembly.GetType("XRL.World.Text.Delegates.GameObjectReplacers");
        var flags=System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic;
        var subjective=type.GetMethod("Subjective",flags);
        var possessive=type.GetMethod("Possessive",flags);
        string cn=(string)subjective.Invoke(null,new object[]{ctx,obj});
        string cnPossessive=(string)possessive.Invoke(null,new object[]{ctx,obj});
        string raw=obj.GetPronounProvider().Subjective;
        XRL.UI.Options.Language="en";
        string en=(string)subjective.Invoke(null,new object[]{ctx,obj});
        int passed=(cn=="她"?1:0)+(cnPossessive=="她的"?1:0)+(raw=="she"?1:0)+(en=="she"?1:0);
        UnityEngine.Debug.Log("[CN-QA] template pronouns="+passed+"/4; CN="+cn+"; possessive="+cnPossessive+"; raw="+raw+"; EN="+en);
    } catch(Exception e) { UnityEngine.Debug.Log("[CN-QA] template pronouns=FAIL EX "+e); }
    finally { XRL.UI.Options.Language=language; }
}''')
lines.append(r'''static void TestGrammar() {
 string language=XRL.UI.Options.Language;int passed=0,total=0;
 try {
  XRL.UI.Options.Language="CN";
  var list=new System.Collections.Generic.List<string>{"Will and Hope","铁门","{{W|木门}}"};
  foreach(string op in new[]{"andList","orList","either.or"}) {
   string actual=XRL.Language.Strings._T("CN-QA", "=items."+op+"=").SetArgument("items",list).ToString();
   string expected=op=="andList"?"Will and Hope、铁门和{{W|木门}}":op=="orList"?"Will and Hope、铁门或{{W|木门}}":"要么Will and Hope、铁门或{{W|木门}}";
   total++;if(actual==expected)passed++;UnityEngine.Debug.Log("[CN-QA] list "+op+" "+(actual==expected?"PASS":"FAIL")+" => "+actual);
  }
  string plural=XRL.Language.Strings._T("CN-QA","=word|pluralize=").SetArgument("word","铁门").ToString();total++;if(plural=="铁门")passed++;
  string outside=XRL.Language.Grammar.Pluralize("铁门");total++;if(outside!="铁门")passed++;
  UnityEngine.Debug.Log("[CN-QA] dynamic noun plural template="+plural+"; native="+outside);
  var provider=new XRL.World.Text.GenderedNoun("花",XRL.World.Gender.Get("female"),true);
  string nounPronoun=XRL.Language.Strings._T("CN-QA","=pronouns.subjective= =pronouns.possessive=").SetArgument("pronouns",provider).ToString();total++;
  if(nounPronoun=="她 她的")passed++;UnityEngine.Debug.Log("[CN-QA] gender pronoun="+nounPronoun);
  var item=XRL.World.GameObject.Create("Door");
  string named=XRL.Language.Strings._T("CN-QA","=subject.a.name=").SetSubject(item).ToString();total++;
  bool article=item!=null && named.Contains("门") && !named.Contains("=subject") && !System.Text.RegularExpressions.Regex.IsMatch(named,@"\b(?:a|an|the)\s+(?=[\u3400-\u9fff])");if(article)passed++;
  UnityEngine.Debug.Log("[CN-QA] template article="+named+"; PASS="+article);
  var part=new XRL.World.Anatomy.BodyPart();part.Name="hand";part.Description="hand";part.Type="Hand";
  total++;if(QudCnGrammar.Anatomy("{{W|12th left hand}}") == "{{W|第12左手}}")passed++;
  string raw=part.GetOrdinalName();
  string cn=XRL.Language.Strings._T("CN-QA","=part.ordinalName=").SetArgument("part",part).ToString();
  total++;if(cn=="手")passed++;total++;if(raw=="hand")passed++;
  UnityEngine.Debug.Log("[CN-QA] anatomy raw="+raw+"; template="+cn);
  string plain=XRL.Language.Grammar.MakeAndList(list);total++;if(plain.Contains("Will and Hope")&&plain!= "Will and Hope、铁门和{{W|木门}}")passed++;
  XRL.UI.Options.Language="en";
  string en=XRL.Language.Strings._T("CN-QA","=items.andList=").SetArgument("items",list).ToString();total++;if(en==XRL.Language.Grammar.MakeAndList(list))passed++;
  UnityEngine.Debug.Log("[CN-QA] list outside scope="+plain+"; EN="+en);
 }catch(Exception e){UnityEngine.Debug.Log("[CN-QA] grammar FAIL "+e);}
 finally{XRL.UI.Options.Language=language;}
 UnityEngine.Debug.Log("[CN-QA] grammar checks="+passed+"/"+total);
}''')
lines.append('}')
(p/'Probe.cs').write_text('\n'.join(lines))
print('runtime string cases',len(cases))
