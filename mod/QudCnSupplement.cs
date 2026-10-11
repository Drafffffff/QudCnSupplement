using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using HarmonyLib;
using XRL;

// Display-only translation. No object mutation, save serialization or global word replacement.
[HasModSensitiveStaticCache]
public static class QudCnSupplement
{
    private const string HarmonyId = "local.qud.cn.supplement.v1";
    private static bool initialized;
    private static readonly object Gate = new object();
    private static readonly HashSet<string> Seen = new HashSet<string>(StringComparer.Ordinal);
    private const int MaxDiagnosticEntries = 256;
    private static readonly Regex English = new Regex(@"[A-Za-z]{3,}");
    private static readonly Regex Article = new Regex(@"\b(?:the|a|an)\s+(?=(?:\{\{[^{}|]+\|)*[\u3400-\u9fff])", RegexOptions.IgnoreCase);
    private static readonly Regex Pronoun = new Regex(@"\b(his|her|its|their|your)\s+(?=(?:\{\{[^{}|]+\|)*[\u3400-\u9fff])", RegexOptions.IgnoreCase);
    private static readonly Regex OuterWithSuffix = new Regex(@"^\{\{([^{}|]+)\|(.*)\}\}(\s*\[[^\]]*\])$", RegexOptions.Singleline);
    private static readonly Regex Outer = new Regex(@"^\{\{([^{}|]+)\|(.*)\}\}$", RegexOptions.Singleline);

    // Evaluate on every invocation: changing language takes effect without restarting.
    public static bool IsChinese { get { return XRL.UI.Options.Language == "CN"; } }

    [ModSensitiveCacheInit]
    public static void Init()
    {
        if (initialized) return;
        initialized = true;
        var harmony = new Harmony(HarmonyId);
        SelfTest();
        int count = 0;
        count += Patch(harmony, "XRL.Messages.MessageQueue", delegate(MethodInfo m) {
            var p = m.GetParameters();
            return (m.Name == "Add" || m.Name == "AddPlayerMessage") && p.Length > 0 && p[0].ParameterType == typeof(string);
        }, "MessagePrefix", null);
        count += Patch(harmony, "XRL.World.Text.TextBuilder", delegate(MethodInfo m) {
            return m.Name == "ToString" && m.ReturnType == typeof(string);
        }, null, "GeneratedPostfix");
        count += Patch(harmony, "XRL.Language.Strings", delegate(MethodInfo m) {
            return m.Name == "_S" && m.ReturnType == typeof(string);
        }, null, "StringPostfix");
        count += Patch(harmony, "XRL.UI.Popup", delegate(MethodInfo m) {
            return m.Name == "Show" || m.Name == "ShowYesNoCancel" || m.Name == "PickOption" || m.Name == "ShowOptionList";
        }, "PopupPrefix", null);
        count += Patch(harmony, "ConsoleLib.Console.ScreenBuffer", delegate(MethodInfo m) {
            var p = m.GetParameters();
            return m.Name == "Write" && p.Length > 0 && (p[0].ParameterType == typeof(string) || p[0].ParameterType == typeof(StringBuilder));
        }, "DisplayPrefix", null);
        count += Patch(harmony, "TMPro.TMP_Text", delegate(MethodInfo m) {
            return m.Name == "set_text";
        }, "DisplayPrefix", null);
        // These delegates generate pronouns for rendered templates, not object names or saved data.
        count += Patch(harmony, "XRL.World.Text.Delegates.GameObjectReplacers", delegate(MethodInfo m) {
            return m.ReturnType == typeof(string) && (m.Name == "Subjective" || m.Name == "Objective" ||
                m.Name == "Possessive" || m.Name == "SubstantivePossessive" || m.Name == "Reflexive");
        }, null, "TemplatePronounPostfix");
        // Effect labels are translated at their semantic source. Character and place names
        // never pass through this hook, unlike global display-name word substitutions.
        foreach (var type in typeof(XRL.World.Effect).Assembly.GetTypes())
        {
            if (type.ContainsGenericParameters || !type.IsSubclassOf(typeof(XRL.World.Effect))) continue;
            foreach (var method in AccessTools.GetDeclaredMethods(type))
            {
                if (method.IsAbstract || method.ContainsGenericParameters || method.Name != "GetDescription" || method.ReturnType != typeof(string) || method.GetParameters().Length != 0) continue;
                try { harmony.Patch(method, postfix: new HarmonyMethod(typeof(QudCnSupplement), "EffectPostfix")); count++; }
                catch (Exception e) { Diagnostic("HOOK_ERROR", method.ToString() + " " + e.Message); }
            }
        }
        UnityEngine.Debug.Log("[QudCnSupplement] initialized; hooks=" + count + "; exact UI=" + QudCnSupplementData.Ui.Count + "; patterns=" + QudCnSupplementData.Patterns.Length + "; language=" + XRL.UI.Options.Language);
    }

    private static int Patch(Harmony harmony, string typeName, Predicate<MethodInfo> select, string prefix, string postfix)
    {
        var type = AccessTools.TypeByName(typeName);
        if (type == null) { Diagnostic("HOOK_MISSING", typeName); return 0; }
        int count = 0;
        foreach (var method in AccessTools.GetDeclaredMethods(type))
        {
            if (!select(method)) continue;
            try
            {
                harmony.Patch(method,
                    prefix: prefix == null ? null : new HarmonyMethod(typeof(QudCnSupplement), prefix),
                    postfix: postfix == null ? null : new HarmonyMethod(typeof(QudCnSupplement), postfix));
                count++;
            }
            catch (Exception e) { Diagnostic("HOOK_ERROR", method.ToString() + " " + e.Message); }
        }
        if (count == 0) Diagnostic("HOOK_MISSING", typeName + " (no matching methods)");
        return count;
    }

    public static void TemplatePronounPostfix(MethodBase __originalMethod, ref string __result)
    {
        if (!IsChinese || string.IsNullOrEmpty(__result)) return;
        __result = TranslateTemplatePronoun(__originalMethod.Name, __result);
    }
    public static string TranslateTemplatePronoun(string operation, string value)
    {
        if (value == null) return value;
        bool possessive = operation == "Possessive" || operation == "SubstantivePossessive";
        string result;
        switch (value.ToLowerInvariant())
        {
            case "she": case "her": case "hers": result = "她"; break;
            case "he": case "him": case "his": result = "他"; break;
            case "it": case "its": result = "它"; break;
            case "they": case "them": case "their": case "theirs": result = "他们"; break;
            case "you": case "your": case "yours": result = "你"; break;
            case "i": case "me": case "my": case "mine": result = "我"; break;
            case "we": case "us": case "our": case "ours": result = "我们"; break;
            case "herself": return "她自己";
            case "himself": return "他自己";
            case "itself": return "它自己";
            case "themselves": case "themself": return "他们自己";
            case "yourself": return "你自己";
            case "yourselves": return "你们自己";
            case "myself": return "我自己";
            case "ourselves": return "我们自己";
            default: return value; // Preserve custom pronouns, names and unrecognized forms.
        }
        return possessive ? result + "的" : result;
    }

    public static void EffectPostfix(ref string __result)
    {
        if (!IsChinese || string.IsNullOrEmpty(__result)) return;
        string value;
        if (QudCnSupplementData.Effects.TryGetValue(__result, out value)) { __result = value; return; }
        var outer = Outer.Match(__result);
        if (outer.Success && QudCnSupplementData.Effects.TryGetValue(outer.Groups[2].Value, out value))
            __result = "{{" + outer.Groups[1].Value + "|" + value + "}}";
    }

    public static void MessagePrefix(ref string __0)
    {
        if (!IsChinese || string.IsNullOrEmpty(__0)) return;
        try
        {
            __0 = TranslateMessage(__0);
            if (NeedsReview(__0)) Diagnostic("MESSAGE_REVIEW", __0);
        }
        catch (Exception e) { Diagnostic("ERROR", "Message " + e.Message); }
    }
    public static void GeneratedPostfix(ref string __result)
    {
        if (!IsChinese || string.IsNullOrEmpty(__result)) return;
        try { __result = TranslateMessage(__result); }
        catch (Exception e) { Diagnostic("ERROR", "Generated " + e.Message); }
    }
    public static void StringPostfix(object[] __args, ref string __result)
    {
        if (!IsChinese || string.IsNullOrEmpty(__result)) return;
        try
        {
            __result = TranslateExact(__result);
            if (NeedsReview(__result)) Diagnostic("STRING_REVIEW", string.Join(" | ", __args) + " => " + __result);
        }
        catch (Exception e) { Diagnostic("ERROR", "String " + e.Message); }
    }
    public static void DisplayPrefix(object[] __args)
    {
        if (!IsChinese || __args.Length == 0) return;
        var text = __args[0] as string;
        if (text != null) { __args[0] = TranslateExact(text); return; }
        var buffer = __args[0] as StringBuilder;
        if (buffer != null)
        {
            string before = buffer.ToString();
            string after = TranslateExact(before);
            // Do not mutate shared StringBuilder arguments used by game code.
            if (after != before) __args[0] = new StringBuilder(after);
        }
    }
    public static void PopupPrefix(object[] __args)
    {
        if (!IsChinese) return;
        for (int i = 0; i < __args.Length; i++)
        {
            var text = __args[i] as string;
            if (text != null) { __args[i] = TranslateMessage(text); continue; }
            var list = __args[i] as IReadOnlyList<string>;
            if (list != null)
            {
                var translated = new string[list.Count];
                for (int n = 0; n < list.Count; n++) translated[n] = TranslateExact(list[n]);
                // Arrays implement both IList and IReadOnlyList; preserve List-specific signatures.
                __args[i] = __args[i] is List<string> ? (object)new List<string>(translated) : translated;
            }
        }
    }

    public static string TranslateExact(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;
        string value;
        if (QudCnSupplementData.Ui.TryGetValue(text, out value)) return value;
        var outer = Outer.Match(text);
        if (outer.Success && QudCnSupplementData.Ui.TryGetValue(outer.Groups[2].Value, out value))
            return "{{" + outer.Groups[1].Value + "|" + value + "}}";
        return text;
    }

    public static string TranslateMessage(string text)
    {
        return TranslateMessage(text, 0);
    }
    private static string TranslateMessage(string text, int depth)
    {
        if (string.IsNullOrEmpty(text) || text.Length > 16384 || depth > 16) return text;
        // Do not operate on unresolved templates. The engine must resolve them first.
        if (text.IndexOf('=') >= 0 && Regex.IsMatch(text, @"=[A-Za-z][^=\r\n]*=")) return text;
        string exact = TranslateExact(text);
        if (exact != text) return exact;
        // A lone a/an in a localized sentence is meaningful even without a long Latin word.
        if (!English.IsMatch(text) && !Article.IsMatch(text)) return text;
        // Combat wraps the sentence in a color span and appends dice outside the span.
        var frame = OuterWithSuffix.Match(text);
        if (frame.Success)
        {
            string inner = TranslateMessage(frame.Groups[2].Value, depth + 1);
            if (inner != frame.Groups[2].Value)
                return "{{" + frame.Groups[1].Value + "|" + inner + "}}" + frame.Groups[3].Value;
        }
        var outer = Outer.Match(text);
        string body = outer.Success ? outer.Groups[2].Value : text;
        if (outer.Success && body.StartsWith("{{", StringComparison.Ordinal))
        {
            string nested = TranslateMessage(body, depth + 1);
            if (nested != body) return "{{" + outer.Groups[1].Value + "|" + nested + "}}";
        }
        foreach (var pair in QudCnSupplementData.Patterns)
        {
            if (!pair.Item1.IsMatch(body)) continue;
            // Capture groups are left untouched: generated names and color markup survive.
            string result = pair.Item1.Replace(body, pair.Item2);
            result = Article.Replace(result, "");
            result = Pronoun.Replace(result, delegate(Match m) {
                switch (m.Groups[1].Value.ToLowerInvariant()) {
                    case "his": return "他的"; case "her": return "她的";
                    case "their": return "他们的"; case "your": return "你的";
                    default: return "它的";
                }
            });
            return outer.Success ? "{{" + outer.Groups[1].Value + "|" + result + "}}" : result;
        }
        return text;
    }

    private static void SelfTest()
    {
        int pronounsPassed = 0;
        string[][] pronouns = {
            new string[] { "Subjective", "she", "她" },
            new string[] { "Objective", "her", "她" },
            new string[] { "Possessive", "her", "她的" },
            new string[] { "SubstantivePossessive", "hers", "她的" },
            new string[] { "Reflexive", "herself", "她自己" },
            new string[] { "Subjective", "She", "她" },
            new string[] { "Subjective", "Will", "Will" },
            new string[] { "Subjective", "xe", "xe" }
        };
        foreach (var item in pronouns) if (TranslateTemplatePronoun(item[0], item[1]) == item[2]) pronounsPassed++;
        UnityEngine.Debug.Log("[QudCnSupplement] pronouns=" + pronounsPassed + "/" + pronouns.Length);
        string[][] cases = new string[][] {
            new string[] { "你 take the 皮甲。", "你拿取了皮甲。" },
            new string[] { "{{r|你 miss 使用 你的 {{w|青铜}}匕首 未命中！}} [2 对 5]", "{{r|你用你的 {{w|青铜}}匕首攻击，但未命中！}} [2 对 5]" },
            new string[] { "你经过了 a 铁门。", "你经过了铁门。" },
            new string[] { "道路被 a 熟铁栅栏 挡住了。", "道路被熟铁栅栏挡住了。" },
            new string[] { "你经过了 {{W|a 铁门}}。", "你经过了{{W|铁门}}。" },
            new string[] { "道路被 an {{W|铁门}} 挡住了。", "道路被{{W|铁门}}挡住了。" },
            new string[] { "a 铁门", "a 铁门" },
            new string[] { "你 equip the 火把", "你装备了火把。" },
            new string[] { "You hit (x2) for 3 damage with 你的 青铜匕首! [7]", "你用 你的 青铜匕首 击中(x2)，造成 3 伤害[7]" },
            new string[] { "The 熊 misses 使用 his 撕咬 未命中你! [2 对 7]", "熊用撕咬攻击你，但未命中！[2 对 7]" },
            new string[] { "你将 the 古怪小饰物 识别为 a 化学电池", "你将古怪小饰物识别为化学电池。" },
            new string[] { "No Equipment Set", "无装备套装" },
            new string[] { "{{R|No Equipment Set}}", "{{R|无装备套装}}" },
            new string[] { "You take 4 damage from freezing!", "你因冰冻受到4伤害。" },
            new string[] { "You take 8 damage from fire! [9]", "你因火焰受到8伤害[9]。" },
            new string[] { "The 熊 dies!", "熊 死亡。" },
            new string[] { "You were killed by Hope-in-Motion!", "你被 Hope-in-Motion 击杀。" },
            new string[] { "You emit a freezing ray from your hands!", "你从双手射出一道冰冻射线。" },
            new string[] { "The 熊 emits a flaming ray from its hands!", "熊从双手射出一道火焰射线。" },
            new string[] { "You toggle 力场 on.", "你将力场开启。" },
            new string[] { "You toggle 力场 off.", "你将力场关闭。" },
            new string[] { "{{R|{{W|No Equipment Set}}}}", "{{R|{{W|无装备套装}}}}" },
            new string[] { "{{R|{{W|You equip the 火把.}}}}", "{{R|{{W|你装备了 火把。}}}}" },
            new string[] { "Hope-in-Motion", "Hope-in-Motion" },
            new string[] { "Will", "Will" },
            new string[] { "=subject.Does:hit= the 熊", "=subject.Does:hit= the 熊" },
            new string[] { "You equip the {{W|火把}}.", "你装备了 {{W|火把}}。" }
        };
        int passed = 0;
        foreach (var item in cases)
        {
            string actual = TranslateMessage(item[0]);
            if (actual == item[1] && TranslateMessage(actual) == actual) passed++;
            else Diagnostic("SELFTEST_FAIL", item[0] + " => " + actual + " (expected " + item[1] + ")");
        }
        string[] codeOnly = new string[] {
            "=subject.Does:hit= =object.the.name=", "{{R|=subject.name=}}",
            "<color=#ff0000>=subject.name=</color>", "AV DV HP XP CPU",
            "Textures/UI/item.png", "C:/Game/HistorySpice.json", "[x2] [7]"
        };
        int diagnosticPassed = 0;
        foreach (string sample in codeOnly) { if (!NeedsReview(sample)) diagnosticPassed++; else Diagnostic("SELFTEST_DIAGNOSTIC_FAIL", sample); }
        if (NeedsReview("你 equip the 火把")) diagnosticPassed++;
        UnityEngine.Debug.Log("[QudCnSupplement] diagnostics=" + diagnosticPassed + "/" + (codeOnly.Length + 1));
        int combinations = 0;
        int combinationFailures = 0;
        foreach (string target in new string[] { "Hope-in-Motion", "Will", "熊", "{{R|熊}}" })
        foreach (string weapon in new string[] { "May", "青铜匕首", "{{W|青铜匕首}}" })
        foreach (string damage in new string[] { "1", "9", "300" })
        {
            string input = "You hit " + target + " for " + damage + " damage with " + weapon + "! [7]";
            string expected = "你用 " + weapon + " 击中 " + target + "，造成 " + damage + " 伤害[7]";
            string actual = TranslateMessage(input);
            combinations++;
            if (actual != expected || TranslateMessage(actual) != actual) { combinationFailures++; Diagnostic("SELFTEST_FAIL", input + " => " + actual); }
        }
        UnityEngine.Debug.Log("[QudCnSupplement] matrix=" + (combinations - combinationFailures) + "/" + combinations);
        UnityEngine.Debug.Log("[QudCnSupplement] selftest=" + passed + "/" + cases.Length);
    }

    public static bool NeedsReview(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return false;
        // Template syntax is code, not untranslated prose. Strip it only for diagnostics;
        // the display value and the engine's variables are never changed here.
        string visible = Regex.Replace(text, @"=[A-Za-z][^=\r\n]*=", "");
        visible = Regex.Replace(visible, @"\{\{[^{}|]*\|", "").Replace("}}", "");
        visible = Regex.Replace(visible, @"<[^>]*>", "");
        visible = Regex.Replace(visible, @"[&^][A-Za-z]", "");
        visible = Regex.Replace(visible, @"\b[\w.\-/]+\.(?:xml|json|png|ogg|wav|dll|cs|txt)\b", "", RegexOptions.IgnoreCase);
        visible = Regex.Replace(visible, @"(?:https?://|[A-Za-z]:[\\/]|/)[^\s<>]+", "");
        visible = Regex.Replace(visible, @"\b(?:AV|DV|MA|PV|XP|HP|SP|MP|FPS|CPU|GPU|UI|ID|CN|TRUE|FALSE|NULL)\b", "");
        visible = Regex.Replace(visible, @"\b[xX]\d+\b", "");
        return English.IsMatch(visible) || Article.IsMatch(visible);
    }

    // At most 256 unique lines per process, at most 1200 characters each. Review candidates
    // include generated names and conventional abbreviations; they are not missing-translation counts.
    private static void Diagnostic(string kind, string text)
    {
        if (text == null) return;
        text = text.Replace("\r", "\\r").Replace("\n", "\\n");
        if (text.Length > 1200) text = text.Substring(0, 1200);
        string entry = kind + ": " + text;
        lock (Gate) { if (Seen.Count >= MaxDiagnosticEntries || !Seen.Add(entry)) return; }
        UnityEngine.Debug.Log("[QudCnSupplement] " + entry);
    }
}
