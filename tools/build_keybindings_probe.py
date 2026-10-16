#!/usr/bin/env python3
"""Generate an isolated, read-only native keybinding screen regression probe."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'analysis/private/keybindings-qa/KeybindingsProbe.cs'
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(r'''
using System;
using System.Collections;
using System.Reflection;
using UnityEngine;
using XRL;
using HarmonyLib;
[HasModSensitiveStaticCache]
public static class QudCnKeybindingsProbeInit {
 [ModSensitiveCacheInit] public static void Init() {
  GameManager.Instance.uiQueue.queueTask(delegate { var go=new UnityEngine.GameObject("CN keybindings QA");UnityEngine.Object.DontDestroyOnLoad(go);go.AddComponent<QudCnKeybindingsProbe>(); });
 }
}
public class QudCnKeybindingsProbe:MonoBehaviour {
 float next;int stage;int passed,total;
 void Start(){next=Time.realtimeSinceStartup+15;}
 void Check(bool ok,string name){total++;if(ok)passed++;else Debug.Log("[CN-KEY-QA] FAIL "+name);}
 static object Get(object o,string f){return AccessTools.Field(o.GetType(),f).GetValue(o);}
 void Update(){
  if(stage>=2||Time.realtimeSinceStartup<next)return;
  try {
   var t=AccessTools.TypeByName("Qud.UI.KeybindsScreen");
   if(stage==0){stage=1;next=Time.realtimeSinceStartup+5;AccessTools.Method(t,"ShowKeybindsClick").Invoke(null,null);return;}
   stage=2;var objects=Resources.FindObjectsOfTypeAll(t);object screen=null;
   foreach(var obj in objects)if((obj as Component).gameObject.activeInHierarchy){screen=obj;break;}
   if(screen==null)throw new Exception("No active keybindings screen");
   var rows=Get(screen,"menuItems") as IList;Check(rows.Count>200,"native rows populated");
   foreach(var row in rows){
    var id=AccessTools.Field(row.GetType(),"KeyId");var category=AccessTools.Field(row.GetType(),"CategoryId");
    var d=AccessTools.Field(row.GetType(),"KeyDescription")??AccessTools.Field(row.GetType(),"CategoryDescription");
    string text=d.GetValue(row) as string;Check(System.Text.RegularExpressions.Regex.IsMatch(text,@"[\u3400-\u9fff]"),"Chinese description "+text);
    if(id!=null){
     string before=(string)id.GetValue(row),cat=(string)category.GetValue(row),bind=(string)Get(row,"Bind1");
     string cn=text;XRL.UI.Options.Language="en";AccessTools.Method(t,"FilterItems").Invoke(screen,null);
     string en=(string)d.GetValue(row);Check(en!=cn,"English restore "+before);
     XRL.UI.Options.Language="CN";AccessTools.Method(t,"FilterItems").Invoke(screen,null);
     Check((string)d.GetValue(row)==cn && (string)id.GetValue(row)==before && (string)category.GetValue(row)==cat && (string)Get(row,"Bind1")==bind,"IDs and bindings "+before);
    }
   }
   foreach(string query in new string[]{"鼠标","Mouse","保存","Save","再生","Regenerate"}){
    AccessTools.Field(t,"searchText").SetValue(screen,query);AccessTools.Method(t,"FilterItems").Invoke(screen,null);
    var filtered=Get(screen,"filteredItems") as IList;Check(filtered.Count>0,"search "+query);
    Debug.Log("[CN-KEY-QA] search "+query+" rows="+filtered.Count);
   }
   AccessTools.Field(t,"searchText").SetValue(screen,"");AccessTools.Method(t,"FilterItems").Invoke(screen,null);
   var conflicts=new System.Collections.Generic.List<string>{"{{C|Save game}}","{{C|Mouse smart use}}"};
   string popup=XRL.Language.Strings._T("KeybindsScreen ConfirmConflictBind","=description|color:W= is already bound to =conflicting.andList=.\n\nDo you want to bind it to =newcommand|color:C= instead?").SetArgument("description","F5").SetArgument("conflicting",conflicts).SetArgument("newcommand","Regenerate limb").ToString();
   Check(popup.Contains("保存游戏") && popup.Contains("鼠标智能使用") && popup.Contains("再生肢体") && popup.Contains("F5"),"conflict popup "+popup);
   Check(conflicts[0]=="{{C|Save game}}","conflict source not mutated");
   Debug.Log("[CN-KEY-QA] conflict popup="+popup.Replace("\n"," "));
   foreach(var scroll in (screen as Component).GetComponentsInChildren<UnityEngine.UI.ScrollRect>(true))scroll.verticalNormalizedPosition=0;
   Debug.Log("[CN-KEY-QA] checks="+passed+"/"+total+"; native rows="+rows.Count);
  }catch(Exception e){stage=2;Debug.Log("[CN-KEY-QA] ERROR "+e);}
 }
}
''')
(p.parent/'manifest.json').write_text('{"ID":"QudCnTestProbe","Title":"Keybinding QA","Version":"1","Author":"QA","LoadAfter":["QudCnSupplement"]}\n')
print(p)
