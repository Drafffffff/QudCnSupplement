using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using HarmonyLib;

// Unity UI and tooltip rendering only. No game-object names, save data, or parameter keys.
public static class QudCnHud
{
    static readonly Regex Color = new Regex(@"^<color=([^>]+)>(.*)</color>$", RegexOptions.Singleline);
    static readonly Regex Markup = new Regex(@"^\{\{([^{}|]+)\|(.*)\}\}$", RegexOptions.Singleline);
    class State { public string Original, Translated; }
    static readonly ConditionalWeakTable<object,State> States = new ConditionalWeakTable<object,State>();
    public sealed class FieldChange { public object Target; public FieldInfo Field; public string Original; }
    public static int Install(Harmony harmony)
    {
        int n=0;
        n+=Patch(harmony,"UnityEngine.UI.Text",m=>m.Name=="set_text","UiArgsPrefix",null);
        n+=Patch(harmony,"XRL.UI.UITextSkin",m=>m.Name=="SetText","UiArgsPrefix",null);
        n+=Patch(harmony,"XRL.UI.UITextSkin",m=>m.Name=="Apply","SkinPrefix",null);
        n+=Patch(harmony,"ModelShark.TooltipManager",m=>m.Name=="SetTextAndSize","TooltipPrefix","TooltipPostfix");
        return n;
    }
    static int Patch(Harmony h,string name,Predicate<MethodInfo> match,string pre,string post)
    {
        var t=AccessTools.TypeByName(name);int n=0;
        if(t==null){UnityEngine.Debug.Log("[QudCnSupplement] UI_HOOK_MISSING: "+name);return 0;}
        foreach(var m in AccessTools.GetDeclaredMethods(t)) if(match(m))
        {
            try { h.Patch(m,prefix:pre==null?null:new HarmonyMethod(typeof(QudCnHud),pre),postfix:post==null?null:new HarmonyMethod(typeof(QudCnHud),post),finalizer:post=="TooltipPostfix"?new HarmonyMethod(typeof(QudCnHud),"TooltipFinalizer"):null);n++; }
            catch(Exception e){UnityEngine.Debug.Log("[QudCnSupplement] UI_HOOK_ERROR: "+name+" "+e.Message);}
        }
        return n;
    }
    public static string Translate(string text)
    {
        if(string.IsNullOrEmpty(text))return text;
        string translated;
        string trimmed=text.Trim();
        if(QudCnHudData.Labels.TryGetValue(trimmed,out translated))
        {
            int first=text.IndexOf(trimmed,StringComparison.Ordinal);
            return text.Substring(0,first)+translated+text.Substring(first+trimmed.Length);
        }
        var outer=Markup.Match(text);
        if(outer.Success){var value=Translate(outer.Groups[2].Value);if(value!=outer.Groups[2].Value)return "{{"+outer.Groups[1].Value+"|"+value+"}}";}
        var color=Color.Match(text);
        if(color.Success){var value=Translate(color.Groups[2].Value);if(value!=color.Groups[2].Value)return "<color="+color.Groups[1].Value+">"+value+"</color>";}
        return QudCnSupplement.TranslateMessage(text);
    }
    public static void UiArgsPrefix(object[] __args)
    {
        if(!QudCnSupplement.IsChinese)return;
        // Only text arguments; numeric SetText parameters, field names and templates are not rewritten.
        if(__args.Length>0 && __args[0] is string)__args[0]=Translate((string)__args[0]);
    }
    public static void SkinPrefix(object __instance)
    {
        var f=AccessTools.Field(__instance.GetType(),"text");if(f==null)return;
        string current=f.GetValue(__instance) as string;if(current==null)return;
        State state=States.GetValue(__instance, key=>new State());
        if(!QudCnSupplement.IsChinese)
        {
            if(state.Translated!=null && current==state.Translated)f.SetValue(__instance,state.Original);
            return;
        }
        if(state.Translated!=null && current==state.Translated)return;
        string value=Translate(current);
        if(value!=current){state.Original=current;state.Translated=value;f.SetValue(__instance,value);}
    }
    public static void TooltipPrefix(object[] __args,out List<FieldChange> __state)
    {
        __state=new List<FieldChange>();if(!QudCnSupplement.IsChinese || __args.Length==0 || __args[0]==null)return;
        var trigger=__args[0];var f=AccessTools.Field(trigger.GetType(),"parameterizedTextFields");
        var entries=f==null?null:f.GetValue(trigger) as IEnumerable;if(entries==null)return;
        foreach(var entry in entries)
        {
            if(entry==null)continue;var value=AccessTools.Field(entry.GetType(),"value");if(value==null)continue;
            var before=value.GetValue(entry) as string;var after=Translate(before);
            if(before!=after){__state.Add(new FieldChange{Target=entry,Field=value,Original=before});value.SetValue(entry,after);}
        }
    }
    public static Exception TooltipFinalizer(Exception __exception,List<FieldChange> __state)
    { TooltipPostfix(__state);return __exception; }
    public static void TooltipPostfix(List<FieldChange> __state)
    {
        if(__state==null)return;
        // Restore serialized source values after rendering so language switches remain reversible.
        foreach(var change in __state)change.Field.SetValue(change.Target,change.Original);
    }
}
