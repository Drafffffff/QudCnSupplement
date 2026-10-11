#!/usr/bin/env python3
"""Create isolated real-engine runtime verb probes; root installs module separately."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'analysis/private/qa-verbs/QudCnVerbProbe.cs'
TARGET.parent.mkdir(parents=True,exist_ok=True)
(TARGET.parent/'manifest.json').write_text(json.dumps({'ID':'QudCnVerbProbe','Title':'CN dynamic verb QA','Version':'0.1.0','LoadAfter':['QudCnSupplement']}))
TARGET.write_text(r'''using System;
using XRL;
[HasModSensitiveStaticCache]
public static class QudCnVerbProbe {
 [ModSensitiveCacheInit] public static void Init() {
  string language=XRL.UI.Options.Language;int passed=0,total=0;
  try {
   XRL.UI.Options.Language="CN";
   var subject=XRL.World.GameObject.Create("Door");
   foreach(var pair in new[]{new[]{"beep","哔哔作响"},new[]{"butcher","屠宰"},new[]{"harvest","收获"},new[]{"leak","泄漏"},new[]{"reflect","反射"},new[]{"refract","折射"},new[]{"jump","跳跃"},new[]{"fabricate","造出"},new[]{"appear","出现"}}) {
    string actual=XRL.Language.Strings._T("CN-QA runtime verbs","=subject.Does#verb=").SetSubject(subject).SetArgument("verb",pair[0]).ToString();
    total++;if(actual.Contains(pair[1])&&!actual.Contains(pair[0])&&!actual.StartsWith("The "))passed++;
    UnityEngine.Debug.Log("[CN-QA] dynamic verb "+pair[0]+" => "+actual);
    string only=XRL.Language.Strings._T("CN-QA runtime verbs","=subject.verb#ArriveVerb=").SetSubject(subject).SetArgument("ArriveVerb",pair[0]).ToString();
    total++;if(only==pair[1])passed++;
   }
   string kept=QudCnRuntimeVerbs.TranslateRendered("{{W|Captain Reflect}} reflects","reflect",false);total++;if(kept=="{{W|Captain Reflect}} 反射")passed++;
   string unknown=QudCnRuntimeVerbs.TranslateRendered("Captain Reflect customverb","customverb",false);total++;if(unknown=="Captain Reflect customverb")passed++;
   string multi=QudCnRuntimeVerbs.TranslateRendered("{{W|Will and Hope}} breaks down","break down",false);total++;if(multi=="{{W|Will and Hope}} 拆解")passed++;
   string near=QudCnRuntimeVerbs.TranslateRendered("Captain Reflect reflected","reflect",false);total++;if(near=="Captain Reflect reflected")passed++;
   string cn=XRL.Language.Strings._T("CN-QA runtime verbs","=subject.Does#verb=").SetSubject(subject).SetArgument("verb","跳跃").ToString();total++;if(cn.Contains("跳跃"))passed++;
   XRL.UI.Options.Language="en";
   string en=XRL.Language.Strings._T("CN-QA runtime verbs","=subject.Does#verb=").SetSubject(subject).SetArgument("verb","reflect").ToString();total++;if(en.Contains("reflect")&&!en.Contains("反射"))passed++;
   string guard=QudCnRuntimeVerbs.TranslateRendered("Captain Reflect reflects","reflect",false);total++;if(guard=="Captain Reflect reflects")passed++;
   UnityEngine.Debug.Log("[CN-QA] dynamic verbs="+passed+"/"+total+"; EN="+en);
  }catch(Exception e){UnityEngine.Debug.Log("[CN-QA] dynamic verbs FAIL "+e);}
  finally{XRL.UI.Options.Language=language;}
 }
}
''')
print(TARGET)
