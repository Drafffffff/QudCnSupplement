#!/usr/bin/env python3
"""Isolated native TextBuilder/HistorySpice tests for cooking articles and units."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
spice=json.loads((ROOT/'mod/historyspice.CN.json').read_text())['spice']
patterns=[s.replace('=^:', '=spice:cooking.').replace('$terrain','General') for s in spice['cooking']['ingredient=']]
q=lambda s:json.dumps(s,ensure_ascii=False)
code=r'''using System; using System.Collections.Generic; using System.Text.RegularExpressions; using XRL;
[HasModSensitiveStaticCache] public static class QudCnCookingProbe {
 [ModSensitiveCacheInit] public static void Init() {
  string before=XRL.UI.Options.Language;int passed=0,total=0;
  try {
   XRL.UI.Options.Language="CN";HistoryKit.HistoricSpice.CheckInit();
   string[] patterns=new string[]{PATTERNS};
   var ingredients=new List<string>();
   foreach(string pattern in patterns)for(int i=0;i<25;i++) {
    string item=XRL.Language.Strings._T("CN-QA cooking",pattern).ToString();
    total++;bool good=!Regex.IsMatch(item,@"\b(?:a|an)\s",RegexOptions.IgnoreCase)&&Regex.IsMatch(item,@"[\u3400-\u9fff]");
    if(good)passed++;else UnityEngine.Debug.Log("[CN-COOK-QA] ingredient FAIL "+pattern+" => "+item);
    if(ingredients.Count<3)ingredients.Add(item);
   }
   ingredients.Clear();
   foreach(string source in new[]{"声誉良好的杏子","好奇的一根草","大刺叶"}) {
    string item=XRL.Language.Strings._T("CN-QA cooking","=ingredient|article=").SetArgument("ingredient",source).ToString();
    total++;if(item==source)passed++;ingredients.Add(item);
   }
   string meal=XRL.Language.Strings._T("Campfire DescribeMeal","=spice:cooking.cookTemplate.!random=").SetArgument("ingredients",ingredients).ToString();
   total++;if(!Regex.IsMatch(meal,@"\b(?:a|an)\s",RegexOptions.IgnoreCase)&&meal.Contains(ingredients[0]))passed++;
   UnityEngine.Debug.Log("[CN-COOK-QA] meal="+meal.Replace("\n","\\n"));
   foreach(var pair in new[]{new[]{"杏子","杏子"},new[]{"声誉良好的 杏子","声誉良好的 杏子"},new[]{"{{W|杏子}}","{{W|杏子}}"},new[]{"apple","an apple"}}) {
    string item=XRL.Language.Strings._T("CN-QA cooking","=ingredient|article=").SetArgument("ingredient",pair[0]).ToString();total++;if(item==pair[1])passed++;else UnityEngine.Debug.Log("[CN-COOK-QA] article FAIL "+item);
   }
   foreach(var pair in new[]{new[]{"你必须补上 10 打兰 淡水来平衡交易。","你必须补上 10 德拉姆 淡水来平衡交易。"},new[]{"1打蓝水","1德拉姆水"},new[]{"{{C|2.5}} 打兰","{{C|2.5}} 德拉姆"},new[]{"打兰花","打兰花"},new[]{"[-] Food","[-] 食物"},new[]{"{{C|Water Containers |12 lbs.|}}","{{C|水容器 |12 lbs.|}}"},new[]{"化学电池 (Full)","化学电池 (充满)"},new[]{"10 德拉姆","10 德拉姆"}}) {
    string actual=QudCnHud.Translate(pair[0]);total++;if(actual==pair[1])passed++;else UnityEngine.Debug.Log("[CN-COOK-QA] unit FAIL "+actual);
   }
   XRL.UI.Options.Language="en";
   string en=XRL.Language.Strings._T("CN-QA cooking","=ingredient|article=").SetArgument("ingredient","apple").ToString();total++;if(en=="an apple")passed++;
   total++;if(QudCnHud.NormalizeUnits("10 打兰")=="10 打兰")passed++;
   UnityEngine.Debug.Log("[CN-COOK-QA] checks="+passed+"/"+total);
  }catch(Exception e){UnityEngine.Debug.Log("[CN-COOK-QA] FAIL "+e);}
  finally{XRL.UI.Options.Language=before;}
 }
}
'''.replace('PATTERNS',','.join(map(q,patterns)))
p=ROOT/'analysis/private/qa-mod/CookingProbe.cs';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(code);print(p)
