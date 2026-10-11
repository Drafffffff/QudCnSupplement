#!/usr/bin/env python3
"""Generate UI inventory only in the isolated QA mod; no original game data is changed."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'analysis/private/qa-mod/UiProbe.cs'
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(r'''
using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using XRL;
[HasModSensitiveStaticCache]
public static class QudCnUiProbeInit {
 [ModSensitiveCacheInit] public static void Init() {
  GameManager.Instance.uiQueue.queueTask(delegate {
   var go=new UnityEngine.GameObject("CN UI QA"); UnityEngine.Object.DontDestroyOnLoad(go); go.AddComponent<QudCnUiProbe>();
  });
 }
}
public class QudCnUiProbe : MonoBehaviour {
 float next; bool done;
 void Start() { next=Time.realtimeSinceStartup+10; }
 void Update() {
  if(done || Time.realtimeSinceStartup<next)return; done=true;
  var assembly=typeof(XRL.UI.Options).Assembly;
  foreach(string name in new string[]{"XRL.UI.UITextSkin","ModelShark.TooltipTrigger"}) {
   var t=assembly.GetType(name); if(t==null)continue;
   foreach(var obj in Resources.FindObjectsOfTypeAll(t)) {
    try {
     var c=obj as Component; if(c==null)continue;
     if(name.EndsWith("UITextSkin")) {
      var f=t.GetField("text",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic);
      Log(c,"skin",f.GetValue(obj) as string);
     } else {
      var f=t.GetField("parameterizedTextFields",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic);
      var list=f.GetValue(obj) as IEnumerable; if(list==null)continue;
      foreach(var entry in list) {
       var ef=entry.GetType().GetField("value",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic);
       if(ef!=null)Log(c,"tooltip",ef.GetValue(entry) as string);
      }
     }
    } catch(Exception e) { Debug.Log("[CN-UI-QA] error="+e.Message); }
   }
  }
  Debug.Log("[CN-UI-QA] inventory done");
  TestHud(assembly);
 }

 static readonly BindingFlags Flags=BindingFlags.Instance|BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;
 static void TestHud(Assembly assembly) {
  string language=XRL.UI.Options.Language; int passed=0,total=0;
  try {
   XRL.UI.Options.Language="CN";
   var tt=assembly.GetType("ModelShark.TooltipTrigger");var mt=assembly.GetType("ModelShark.TooltipManager");
   var managers=Resources.FindObjectsOfTypeAll(mt);object manager=managers.Length>0?managers[0]:null;
   var labels=new HashSet<string>();
   foreach(var obj in Resources.FindObjectsOfTypeAll(tt)) {
    var entries=tt.GetField("parameterizedTextFields",Flags).GetValue(obj) as IEnumerable;if(entries==null)continue;
    string source=null,expected=null;
    foreach(var entry in entries) { var value=entry.GetType().GetField("value",Flags).GetValue(entry) as string;
     if(value!=null && QudCnHudData.Labels.TryGetValue(value,out expected)){source=value;break;} }
    if(source==null || !labels.Add(source))continue; total++;
    try {
     tt.GetMethod("Initialize",Flags).Invoke(obj,null);
     var tip=tt.GetProperty("Tooltip",Flags).GetValue(obj,null);
     tip.GetType().GetMethod("Deactivate",Flags).Invoke(tip,null);tip.GetType().GetMethod("WarmUp",Flags).Invoke(tip,null);
     mt.GetMethod("SetTextAndSize",Flags).Invoke(manager,new object[]{obj});
     var go=tip.GetType().GetProperty("GameObject",Flags).GetValue(tip,null) as UnityEngine.GameObject;
     string rendered="";if(go!=null)foreach(var text in go.GetComponentsInChildren<TMPro.TMP_Text>(true))rendered+=text.text+" | ";
     bool restored=false;foreach(var entry in entries)if((string)entry.GetType().GetField("value",Flags).GetValue(entry)==source)restored=true;
     bool ok=rendered.Contains(expected)&&restored;if(ok)passed++;
     Debug.Log("[CN-UI-QA] tooltip "+(ok?"PASS":"FAIL")+"; source="+source+"; rendered="+rendered+"; source_restored="+restored);
     if(source=="Autoexplore") {
      total++;XRL.UI.Options.Language="en";tip.GetType().GetMethod("Deactivate",Flags).Invoke(tip,null);tip.GetType().GetMethod("WarmUp",Flags).Invoke(tip,null);mt.GetMethod("SetTextAndSize",Flags).Invoke(manager,new object[]{obj});
      string en="";foreach(var text in go.GetComponentsInChildren<TMPro.TMP_Text>(true))en+=text.text;
      if(en.Contains(source))passed++;Debug.Log("[CN-UI-QA] tooltip English guard="+en.Contains(source));XRL.UI.Options.Language="CN";
     }
    }catch(Exception e){Debug.Log("[CN-UI-QA] tooltip FAIL "+source+" "+e);}
   }
   var st=assembly.GetType("XRL.UI.UITextSkin");
   foreach(var obj in Resources.FindObjectsOfTypeAll(st)) {
    var f=st.GetField("text",Flags);var before=f.GetValue(obj) as string;
    if(before==null || (before.Trim()!="Nearby objects"&&before.Trim()!="附近物品"))continue;
    foreach(var pair in QudCnHudData.Labels) {
     f.SetValue(obj,pair.Key);st.GetMethod("Apply",Flags).Invoke(obj,null);total++;
     var target=(obj as Component).GetComponent<TMPro.TMP_Text>();bool match=target!=null&&target.text==pair.Value;
     if(match)passed++;else Debug.Log("[CN-UI-QA] label FAIL "+pair.Key+" => "+(target==null?"missing TMP":target.text));
    }
    f.SetValue(obj," Nearby objects");st.GetMethod("Apply",Flags).Invoke(obj,null);total++;
    var component=obj as Component;var tmp=component.GetComponent<TMPro.TMP_Text>();
    bool cn=tmp!=null&&tmp.text.Contains("附近物品");if(cn)passed++;
    XRL.UI.Options.Language="en";st.GetMethod("Apply",Flags).Invoke(obj,null);total++;bool en=tmp!=null&&tmp.text.Contains("Nearby objects");if(en)passed++;
    Debug.Log("[CN-UI-QA] nearby header CN="+cn+"; EN restore="+en);
    XRL.UI.Options.Language="CN";f.SetValue(obj,before);st.GetMethod("Apply",Flags).Invoke(obj,null);
   }
  }catch(Exception e){Debug.Log("[CN-UI-QA] HUD FAIL "+e);}
  finally {XRL.UI.Options.Language=language;}
  Debug.Log("[CN-UI-QA] HUD checks="+passed+"/"+total);
  try {
   var tt=assembly.GetType("ModelShark.TooltipTrigger");
   foreach(var obj in Resources.FindObjectsOfTypeAll(tt))if((obj as Component).name=="ExploreButton") {
    var tip=tt.GetProperty("Tooltip",Flags).GetValue(obj,null);tip.GetType().GetMethod("Deactivate",Flags).Invoke(tip,null);
    tt.GetMethod("StartHover",Flags).Invoke(obj,null);Debug.Log("[CN-UI-QA] visible Autoexplore hover requested");break;
   }
  }catch(Exception e){Debug.Log("[CN-UI-QA] hover screenshot FAIL "+e);}

 }
 static void Log(Component c,string kind,string text) {
  if(string.IsNullOrEmpty(text)||text.Length>1600||!System.Text.RegularExpressions.Regex.IsMatch(text,@"[A-Za-z]{2,}"))return;
  string path=c.name;var p=c.transform.parent;int n=0;while(p!=null&&n++<8){path=p.name+"/"+path;p=p.parent;}
  Debug.Log("[CN-UI-QA] "+kind+" active="+c.gameObject.activeInHierarchy+" | "+path+" | "+text.Replace("\n","\\n").Replace("\r",""));
 }
}
''')
print(p)
