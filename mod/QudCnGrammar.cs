using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text.RegularExpressions;
using HarmonyLib;

// Template display operations only; names and anatomical storage remain unchanged.
public static class QudCnGrammar
{
 [ThreadStatic] static int listDepth;
 [ThreadStatic] static int pluralDepth;
 static readonly Regex Article=new Regex(@"^((?:\{\{[^{}|]+\||&[A-Za-z])*)(?:a|an|the)\s+(?=(?:\{\{[^{}|]+\||&[A-Za-z])*[\u3400-\u9fff])",RegexOptions.IgnoreCase);
 static readonly Dictionary<string,string> Parts=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase) {
  {"hand","手"},{"hands","双手"},{"arm","手臂"},{"arms","双臂"},{"leg","腿"},{"legs","双腿"},{"foot","脚"},{"feet","双脚"},
  {"head","头"},{"heads","头部"},{"face","脸"},{"faces","脸部"},{"eye","眼"},{"eyes","双眼"},{"mouth","嘴"},{"mouths","嘴"},
  {"body","躯干"},{"bodies","躯干"},{"back","背"},{"backs","背部"},{"tail","尾巴"},{"tails","尾巴"},{"tentacle","触手"},{"tentacles","触手"},
  {"wing","翅膀"},{"wings","双翼"},{"root","根"},{"roots","根"},{"fin","鳍"},{"fins","鳍"},{"pseudopod","伪足"},{"pseudopods","伪足"},
  {"antenna","触角"},{"antennae","触角"},{"tread","履带"},{"treads","履带"},{"wheel","轮子"},{"wheels","轮子"},{"tendril","卷须"},{"tendrils","卷须"},
  {"floating nearby","漂浮在附近"},{"thrown weapon","投掷武器"},{"missile weapon","远程武器"}
 };
 static readonly Dictionary<string,string> Ordinals=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase) {
  {"first","第一"},{"second","第二"},{"third","第三"},{"fourth","第四"},{"fifth","第五"},{"sixth","第六"},{"seventh","第七"},{"eighth","第八"},{"ninth","第九"},{"tenth","第十"},{"eleventh","第十一"},{"twelfth","第十二"},{"thirteenth","第十三"},{"fourteenth","第十四"},{"fifteenth","第十五"},{"sixteenth","第十六"},{"seventeenth","第十七"},{"eighteenth","第十八"},{"nineteenth","第十九"},{"twentieth","第二十"},
  {"left","左"},{"right","右"},{"upper","上"},{"lower","下"},{"fore","前"},{"hind","后"}
 };
 public static int Install(Harmony h) {
  int count=0;
  foreach(string name in new[]{"XRL.World.Text.Delegates.BodyPartReplacers","XRL.World.Text.Delegates.GameObjectReplacers"}) {
   var t=AccessTools.TypeByName(name);if(t==null)continue;
   foreach(var m in AccessTools.GetDeclaredMethods(t))if(m.ReturnType==typeof(string)&&(m.Name=="OrdinalName"||m.Name=="BodyPartOrdinalName"||m.Name=="BodyPartOrdinalNameShuffled")) {
    h.Patch(m,postfix:new HarmonyMethod(typeof(QudCnGrammar),"PartPostfix"));count++;
   }
  }
  var objects=AccessTools.TypeByName("XRL.World.Text.Delegates.GameObjectReplacers");
  foreach(var m in AccessTools.GetDeclaredMethods(objects))if(m.ReturnType==typeof(string)&&(m.Name=="Does"||m.Name=="WithDefiniteArticle"||m.Name=="PossessiveWithDefiniteArticle"||m.Name=="WithDefiniteArticleStripped"||m.Name=="PossessiveWithDefiniteArticleStripped"||m.Name=="WithIndefiniteArticle"||m.Name=="PossessiveWithIndefiniteArticle"||m.Name=="ShortNameWithIndefiniteArticle"||m.Name=="CountableName"||m.Name=="TargetName"||m.Name=="TargetNameSingle"||m.Name=="TargetNameLong"||m.Name=="TargetNameReference"||m.Name=="WithDefiniteOrIndefiniteArticle"||m.Name=="WithIndefiniteOrStack"||m.Name=="IndefiniteForOthers")) {
   h.Patch(m,postfix:new HarmonyMethod(typeof(QudCnGrammar),"NamePostfix"));count++;
  }
  foreach(string name in new[]{"XRL.World.Text.Delegates.ListReplacers","XRL.World.Text.Delegates.LiquidReplacers"}) {
   var t=AccessTools.TypeByName(name);if(t==null)continue;
   foreach(var m in AccessTools.GetDeclaredMethods(t))if(m.Name=="AndList"||m.Name=="OrList"||m.Name=="EitherOrList") {
    h.Patch(m,prefix:new HarmonyMethod(typeof(QudCnGrammar),"ListPrefix"),finalizer:new HarmonyMethod(typeof(QudCnGrammar),"ListFinalizer"));count++;
   }
  }
  foreach(string name in new[]{"XRL.Language.Grammar","XRL.Language.Translator"}) {
   var t=AccessTools.TypeByName(name);if(t==null)continue;
   foreach(var m in AccessTools.GetDeclaredMethods(t))if(m.ReturnType==typeof(string)&&(m.Name=="MakeAndList"||m.Name=="MakeOrList")&&m.GetParameters().Length>0&&typeof(IEnumerable<string>).IsAssignableFrom(m.GetParameters()[0].ParameterType)) {
    h.Patch(m,prefix:new HarmonyMethod(typeof(QudCnGrammar),"JoinPrefix"));count++;
   }
  }
  foreach(string name in new[]{"GameObjectReplacers","ListReplacers","NumberReplacers","StringReplacers","PostProcessors"}) {
   var t=AccessTools.TypeByName("XRL.World.Text.Delegates."+name);if(t==null)continue;
   foreach(var m in AccessTools.GetDeclaredMethods(t))if(m.Name=="Pluralize"||m.Name=="PluralizeWord"||m.Name=="PluralName") {
    h.Patch(m,prefix:new HarmonyMethod(typeof(QudCnGrammar),"PluralPrefix"),finalizer:new HarmonyMethod(typeof(QudCnGrammar),"PluralFinalizer"));count++;
   }
  }
  var grammar=AccessTools.TypeByName("XRL.Language.Grammar");
  foreach(var m in AccessTools.GetDeclaredMethods(grammar))if(m.Name=="Pluralize"&&m.ReturnType==typeof(string)&&m.GetParameters().Length>0&&m.GetParameters()[0].ParameterType==typeof(string)) {
   h.Patch(m,prefix:new HarmonyMethod(typeof(QudCnGrammar),"PluralWordPrefix"));count++;
  }
  var post=AccessTools.TypeByName("XRL.World.Text.Delegates.PostProcessors");
  foreach(var m in AccessTools.GetDeclaredMethods(post))if(m.Name=="Article"&&m.GetParameters().Length==1) {
   h.Patch(m,prefix:new HarmonyMethod(typeof(QudCnGrammar),"ArticlePrefix"));count++;
  }
  return count;
 }
 // |article runs after a HistorySpice ingredient/adjective expands. Chinese
 // has no a/an; skip the English operation only when its value starts in CJK.
 public static bool ArticlePrefix(object __0) {
  if(!QudCnSupplement.IsChinese||__0==null)return true;
  var value=AccessTools.Field(__0.GetType(),"Value").GetValue(__0);
  return value==null||!Regex.IsMatch(value.ToString(),@"^\s*(?:\{\{[^{}|]*\||&[A-Za-z])*[\u3400-\u9fff]");
 }
 public static string Anatomy(string text) {
  if(string.IsNullOrEmpty(text))return text;
  var color=Regex.Match(text,@"^\{\{([^{}|]+)\|(.*)\}\}$",RegexOptions.Singleline);
  if(color.Success){string inner=Anatomy(color.Groups[2].Value);return "{{"+color.Groups[1].Value+"|"+inner+"}}";}
  string direct;if(Parts.TryGetValue(text,out direct))return direct;
  var match=Regex.Match(text,@"^((?:(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|[0-9]+(?:st|nd|rd|th)|left|right|upper|lower|fore|hind) )+)(.+)$",RegexOptions.IgnoreCase);
  if(!match.Success||!Parts.TryGetValue(match.Groups[2].Value,out direct))return text;
  string prefix="";foreach(var word in match.Groups[1].Value.Trim().Split(' '))prefix+=Ordinals.ContainsKey(word)?Ordinals[word]:"第"+Regex.Match(word,@"^[0-9]+").Value;
  return prefix+direct;
 }
 public static void PluralPrefix(out bool __state) {__state=QudCnSupplement.IsChinese;if(__state)pluralDepth++;}
 public static Exception PluralFinalizer(Exception __exception,bool __state) {if(__state)pluralDepth--;return __exception;}
 public static bool PluralWordPrefix(string __0,ref string __result) {
  if(pluralDepth>0&&QudCnSupplement.IsChinese&&__0!=null&&Regex.IsMatch(__0,@"[\u3400-\u9fff]")){__result=__0;return false;}return true;
 }
 public static void NamePostfix(object[] __args,ref string __result) {
  if(!QudCnSupplement.IsChinese||string.IsNullOrEmpty(__result)||!Article.IsMatch(__result))return;
  foreach(var arg in __args) {
   var obj=arg as XRL.World.GameObject;
   if(obj!=null){if(!obj.HasProperName)__result=Article.Replace(__result,"$1",1);return;}
  }
 }
 public static void PartPostfix(ref string __result) {if(QudCnSupplement.IsChinese)__result=Anatomy(__result);}
 public static bool ListPrefix(MethodBase __originalMethod,object[] __args,out int __state) {
  __state=0;if(!QudCnSupplement.IsChinese)return true;listDepth++;__state=1;
  if(__originalMethod.Name=="EitherOrList"&&__args.Length>1&&__args[1] is IEnumerable<string>) {
   var items=new List<string>((IEnumerable<string>)__args[1]);
   string joined=items.Count==0?"":items.Count==1?items[0]:items.Count==2?items[0]+"或"+items[1]:string.Join("、",items.GetRange(0,items.Count-1).ToArray())+"或"+items[items.Count-1];
   var field=AccessTools.Field(__args[0].GetType(),"Value");var value=field.GetValue(__args[0]);
   AccessTools.Method(value.GetType(),"Append",new[]{typeof(string)}).Invoke(value,new object[]{(items.Count>1?"要么":"")+joined});return false;
  }
  return true;
 }
 public static Exception ListFinalizer(Exception __exception,int __state) {
  if(__state>0)listDepth--;return __exception;
 }
 public static bool JoinPrefix(MethodBase __originalMethod,object[] __args,ref string __result) {
  if(listDepth==0||!QudCnSupplement.IsChinese)return true;
  var input=__args[0] as IEnumerable<string>;if(input==null)return true;
  var items=new List<string>(input);string separator=__originalMethod.Name=="MakeOrList"?"或":"和";
  if(items.Count==0)__result="";
  else if(items.Count==1)__result=items[0];
  else if(items.Count==2)__result=items[0]+separator+items[1];
  else __result=string.Join("、",items.GetRange(0,items.Count-1).ToArray())+separator+items[items.Count-1];
  return false;
 }
}
