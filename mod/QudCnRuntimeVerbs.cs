using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using System.Text.RegularExpressions;
using HarmonyLib;

// Only TextBuilder's displayed Does/Verb delegates. Never alter GameObject verbs,
// shared invocation arguments, blueprint properties, internal IDs, or names.
public static class QudCnRuntimeVerbs
{
 static readonly Dictionary<string,string> Words=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase) {
  {"see","看见"},{"spot","发现"},{"notice","注意到"},{"hear","听见"},{"sense","感应到"},
  {"fabricate","造出"},{"produce","制造"},{"extrude","挤出"},{"create","创造"},{"generate","生成"},
  {"excavate","挖掘"},{"clack","咔哒作响"},{"whirl","旋转"},{"sputter","噗噗作响"},{"cough","咳响"},{"whir","呼鸣"},{"whine","尖鸣"},{"thunk","咚响"},{"break down","拆解"},{"fwoosh","呼啸"},{"vibrate","振动"},{"chime","鸣响"},{"still","静止"},
  {"beep","哔哔作响"},{"click","咔嗒作响"},{"bloop","咕噜作响"},{"hum","嗡鸣"},{"whirr","呼呼作响"},{"buzz","嗡嗡作响"},
  {"butcher","屠宰"},{"harvest","收获"},{"gather","采集"},{"collect","收集"},{"pick","采摘"},{"pluck","摘取"},
  {"leak","泄漏"},{"drip","滴出"},{"ooze","渗出"},{"seep","渗出"},{"spill","溢出"},{"pour","倒出"},
  {"reflect","反射"},{"refract","折射"},{"deflect","偏转"},{"scatter","散射"},{"absorb","吸收"},
  {"jump","跳跃"},{"leap","跃起"},{"hop","跳起"},{"bound","跃进"},{"vault","跃过"},
  {"arrive","到达"},{"appear","出现"},{"materialize","显现"},{"rematerialize","重新显现"},{"emerge","出现"},{"teleport","传送"},
  {"fall","落下"},{"land","落地"},{"move","移动"},{"walk","行走"},{"run","奔跑"},{"fly","飞行"},
  {"stumble","踉跄"},{"tumble","翻滚"},{"blink","闪现"},{"pop","突然出现"},{"phase","相位移动"}
 };
 static readonly HashSet<string> ReviewedUnknown=new HashSet<string>(StringComparer.Ordinal);
 static bool CaptureError;
 static readonly BindingFlags Flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
 public static int Install(Harmony harmony) {
  int count=0;
  var type=AccessTools.TypeByName("XRL.World.Text.Delegates.GameObjectReplacers");
  if(type==null)return count;
  foreach(var method in AccessTools.GetDeclaredMethods(type)) {
   if(method.ReturnType!=typeof(string)||(method.Name!="Does"&&method.Name!="Verb")||method.IsAbstract||method.ContainsGenericParameters)continue;
   harmony.Patch(method,prefix:new HarmonyMethod(typeof(QudCnRuntimeVerbs),"Capture"),postfix:new HarmonyMethod(typeof(QudCnRuntimeVerbs),"Render"));count++;
  }
  return count;
 }
 public static void Capture(MethodBase __originalMethod,object[] __args,out string __state) {
  __state=null;if(!QudCnSupplement.IsChinese)return;
  try {
   var pars=__originalMethod.GetParameters();
   for(int i=0;i<pars.Length;i++)if(pars[i].Name=="Verb"&&__args[i] is string){__state=(string)__args[i];return;}
   if(__args.Length==0||__args[0]==null)return;
   // Capture before native TakeParameter can consume the parameter list.
   var method=__args[0].GetType().GetMethod("GetParameter",Flags,null,new[]{typeof(int),typeof(string)},null);
   var fallbackField=__args[0].GetType().GetField("Default",Flags);
   string fallback=fallbackField==null?null:fallbackField.GetValue(__args[0]) as string;
   if(method!=null)__state=(string)method.Invoke(__args[0],new object[]{0,fallback});
   else __state=fallback;
  } catch(Exception e) { if(!CaptureError){CaptureError=true;UnityEngine.Debug.Log("[QudCnRuntimeVerbs] capture failed: "+e.GetType().Name);} }
 }
 public static void Render(MethodBase __originalMethod,string __state,ref string __result) {
  if(QudCnSupplement.IsChinese&&!string.IsNullOrEmpty(__state))__result=TranslateRendered(__result,__state,__originalMethod.Name=="Verb");
 }
 public static string TranslateRendered(string text,string actualVerb,bool verbOnly) {
  if(!QudCnSupplement.IsChinese||string.IsNullOrEmpty(text)||string.IsNullOrEmpty(actualVerb))return text;
  string chinese;if(!Words.TryGetValue(actualVerb,out chinese)) {
   lock(ReviewedUnknown) { if(Regex.IsMatch(actualVerb,@"^[A-Za-z][A-Za-z -]*$")&&ReviewedUnknown.Count<64&&ReviewedUnknown.Add(actualVerb))UnityEngine.Debug.Log("[QudCnRuntimeVerbs] REVIEW actual verb="+actualVerb); }
   return text;
  }
  string third;
  if(actualVerb.EndsWith("y",StringComparison.OrdinalIgnoreCase)&&actualVerb.Length>1&&"aeiou".IndexOf(char.ToLowerInvariant(actualVerb[actualVerb.Length-2]))<0)third=actualVerb.Substring(0,actualVerb.Length-1)+"ies";
  else if(Regex.IsMatch(actualVerb,@"(?:s|sh|ch|x|z|o)$",RegexOptions.IgnoreCase))third=actualVerb+"es";
  else third=actualVerb+"s";
  if(actualVerb=="fly")third="flies";
  if(actualVerb=="break down")third="breaks down";
  // Match only the actual operation's complete trailing verb, with original
  // markup terminators preserved; a proper name earlier in the result is untouched.
  string pattern=(verbOnly?@"^":@"(?<=\s)")+"(?:"+Regex.Escape(actualVerb)+"|"+Regex.Escape(third)+@")(?<end>(?:\}\}|&[A-Za-z])*)$";
  return Regex.Replace(text,pattern,delegate(Match m){return chinese+m.Groups["end"].Value;},RegexOptions.IgnoreCase);
 }
}
