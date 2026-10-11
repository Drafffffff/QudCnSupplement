#!/usr/bin/env python3
"""Isolated tests for the user's 2026-10-11 Steam screenshots."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'analysis/private/qa-mod/SteamProbe.cs'
p.write_text(r'''using System;using XRL;
[HasModSensitiveStaticCache] public static class QudCnSteamProbe {
 [ModSensitiveCacheInit] public static void Init() {
  string before=XRL.UI.Options.Language;int passed=0,total=0;
  try {
   XRL.UI.Options.Language="CN";
   var sitting=new XRL.World.Effects.Sitting();string sit=sitting.GetDescription();total++;if(sit=="{{C|坐着}}")passed++;
   var lying=new XRL.World.Effects.Prone(false,false,false,XRL.World.GameObject.Create("Bed"));string lie=lying.GetDescription();total++;if((lie.Contains("躺在")||lie.Contains("俯卧"))&&!lie.Contains("lying"))passed++;
   UnityEngine.Debug.Log("[CN-STEAM-QA] native effects="+sit+" | "+lie);
   var gender=(XRL.World.Gender)typeof(object).GetMethod("MemberwiseClone",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).Invoke(XRL.World.Gender.Get("female"),null);
   gender.FormalAddressTerm="human friend";
   var provider=new XRL.World.Text.GenderedNoun("CN-QA",gender,true);
   string formal=XRL.Language.Strings._T("CN-QA Steam","=pronouns.formalAddressTerm=").SetArgument("pronouns",provider).ToString();total++;if(formal=="人类朋友")passed++;UnityEngine.Debug.Log("[CN-STEAM-QA] custom isolated provider="+formal);
   var tagEvent=new XRL.World.GetDisplayNameEvent();var dbField=typeof(XRL.World.GetDisplayNameEvent).GetField("DB");
   if(dbField.GetValue(tagEvent)==null)dbField.SetValue(tagEvent,Activator.CreateInstance(dbField.FieldType));
   tagEvent.AddTag("[{{B|lying on a 床}}]",0);string tag=dbField.GetValue(tagEvent).ToString();total++;if(tag.Contains("躺在床上"))passed++;UnityEngine.Debug.Log("[CN-STEAM-QA] native tag="+tag);
   foreach(string blueprint in new[]{"HumanApothecary","HumanTinker"}) {
    var obj=XRL.World.GameObject.Create(blueprint);XRL.UI.Options.Language="en";string original=obj.formalAddressTerm;XRL.UI.Options.Language="CN";
    string actual=XRL.Language.Strings._T("CN-QA Steam","=subject.formalAddressTerm=").SetSubject(obj).ToString();
    string expected=QudCnSupplement.TranslateTemplatePronoun("FormalAddressTerm",original);total++;if(actual==expected)passed++;
    UnityEngine.Debug.Log("[CN-STEAM-QA] formal "+blueprint+" "+original+" => "+actual);
   }
   foreach(var pair in new[]{new[]{"你在日志的 {{Y|Sultan Histories > 瑞谢夫}} 区段中记下这项资讯。","你在日志的 {{Y|苏丹历史 > 瑞谢夫}} 区段中记下这项资讯。"},new[]{"你在日志的 Sultan Histories > 瑞谢夫 区段中记下这项资讯。","你在日志的 苏丹历史 > 瑞谢夫 区段中记下这项资讯。"},new[]{"Will and Hope Sultan Histories","Will and Hope Sultan Histories"},new[]{"14th 日","14 日"},new[]{"21st 日","21 日"},new[]{"22nd 日","22 日"},new[]{"23rd 日","23 日"},new[]{"14th captain","14th captain"}}) {
    string actual=QudCnHud.Translate(pair[0]);total++;if(actual==pair[1])passed++;else UnityEngine.Debug.Log("[CN-STEAM-QA] FAIL "+pair[0]+" => "+actual);
   }
   total++;if(QudCnSupplement.TranslateTemplatePronoun("FormalAddressTerm","human friend")=="人类朋友")passed++;
   XRL.UI.Options.Language="en";total++;if(sitting.GetDescription()=="{{C|sitting}}"&&QudCnSupplement.TranslatePosture("{{C|lying on a 床}}")=="{{C|lying on a 床}}")passed++;
   total++;if(QudCnHud.NormalizeDate("14th 日")=="14th 日")passed++;
   UnityEngine.Debug.Log("[CN-STEAM-QA] checks="+passed+"/"+total);
  }catch(Exception e){UnityEngine.Debug.Log("[CN-STEAM-QA] FAIL "+e);}
  finally{XRL.UI.Options.Language=before;}
 }
}
''');print(p)
