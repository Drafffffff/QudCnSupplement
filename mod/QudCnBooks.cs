using System;
using System.IO;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using HarmonyLib;
using XRL;
using XRL.World.Parts;

// Redirect only the default procedural book corpus while CN is selected.
// Original chains, filenames, BookSeed/BookCorpus and saved titles remain intact.
public static class QudCnBooks
{
    public const string DefaultCorpus = "LibraryCorpus.json";
    public const string ChineseCorpus = "LibraryCorpus.CN.json";
    private sealed class DefaultMarker { }
    private static readonly ConditionalWeakTable<MarkovChainData,DefaultMarker> DefaultChains = new ConditionalWeakTable<MarkovChainData,DefaultMarker>();
    private static readonly object Gate = new object();
    private static MarkovChainData chinese;
    private static bool loadFailureLogged;
    private static object chineseGame;
    private static bool secretsAdded;
    private static readonly Regex IsnerHeader = new Regex(@"^(of the|to the|with the|in the) \{(Ruin of House Isner|masterwork pistol Ruin of House Isner|chest containing the Ruin of House Isner|chest holding the Ruin of House Isner|famous revolver Ruin of House Isner|hiding place of the Ruin of House Isner|lost masterwork pistol), (.+)\.\}$");
    private static readonly Regex IsnerStored = new Regex(@"^(said to be stored somewhere|rumored to be stored somewhere|located somewhere|where I stored it somewhere) (?:(?<distance>[0-9]+) parasangs|under one parasangs?) (?<direction>east|west|north|south) of (?<landmark>.+?)(?<story>, as the story goes)?$");
    private static readonly Regex IsnerNear = new Regex(@"^located somewhere near (?<landmark>.+) (?:some (?<distance>[0-9]+) parasangs|less than one parasang) (?<direction>east|west|north|south)$");
    private static readonly Regex IsnerHidden = new Regex(@"^which I hid somewhere (?<direction>east|west|north|south) of (?<landmark>.+), (?:about (?<distance>[0-9]+) parasangs|less than one parasang)$");
    private static readonly Regex Cjk = new Regex(@"[\u3400-\u9fff]");
    private static readonly HashSet<string> Landmarks = new HashSet<string>(StringComparer.Ordinal);
    private static readonly Regex Spaces = new Regex(@"[ \t]+");
    private const string ObservedTitle = "The Orator Domineers the West";
    private const string ObservedChineseTitle = "演说家统御西方";

    public static int Install(Harmony harmony)
    {
        int count = 0;
        count += Patch(harmony, typeof(MarkovChainData), m => m.Name == "LoadFromFile" && m.IsStatic && m.ReturnType == typeof(MarkovChainData), null, "LoadedPostfix");
        count += Patch(harmony, typeof(MarkovChain), m => m.IsStatic && m.ReturnType == typeof(string) &&
            (m.Name == "GenerateTitle" || m.Name == "GenerateSentence" || m.Name == "GenerateParagraph") &&
            m.GetParameters().Length > 0 && m.GetParameters()[0].ParameterType == typeof(MarkovChainData), "GeneratePrefix", "GeneratePostfix");
        count += Patch(harmony, typeof(MarkovChain), m => m.Name == "AppendSecret", "SecretPrefix", null);
        count += Patch(harmony, typeof(MarkovBook), m => m.Name == "SetContents", null, "ContentsPostfix");
        count += Patch(harmony, typeof(XRL.World.GameObject), m => (m.Name == "GetDisplayName" || m.Name == "get_DisplayName") && m.ReturnType == typeof(string), null, "BookNamePostfix");
        return count;
    }

    private static int Patch(Harmony harmony, Type type, Predicate<MethodInfo> select, string prefix, string postfix)
    {
        int count = 0;
        foreach (var method in AccessTools.GetDeclaredMethods(type))
        {
            if (!select(method)) continue;
            try
            {
                harmony.Patch(method, prefix: prefix == null ? null : new HarmonyMethod(typeof(QudCnBooks), prefix),
                    postfix: postfix == null ? null : new HarmonyMethod(typeof(QudCnBooks), postfix));
                count++;
            }
            catch (Exception e) { UnityEngine.Debug.Log("[QudCnSupplement] BOOK_HOOK_ERROR: " + method + " " + e.Message); }
        }
        return count;
    }

    public static void LoadedPostfix(string __0, MarkovChainData __result)
    {
        if (__result == null || string.IsNullOrEmpty(__0) || Path.GetFileName(__0) != DefaultCorpus) return;
        DefaultChains.GetValue(__result, key => new DefaultMarker());
    }

    public static bool IsDefaultChain(MarkovChainData data)
    {
        if (data == null) return false;
        DefaultMarker marker;
        if (DefaultChains.TryGetValue(data, out marker)) return true;
        // A chain may have been loaded before this mod's cache initialization.
        // This is only an identity check; the original shared cache is not changed.
        MarkovChainData cached;
        return MarkovBook.CorpusData != null && MarkovBook.CorpusData.TryGetValue(DefaultCorpus, out cached) && ReferenceEquals(data, cached);
    }

    public static MarkovChainData GetChineseChain()
    {
        lock (Gate)
        {
            if (chinese != null && chineseGame != null && XRL.The.Game != null && !ReferenceEquals(chineseGame, XRL.The.Game))
            {
                // Secrets contain world-specific coordinates; never carry them
                // into another game in the same process.
                chinese = null; chineseGame = null; secretsAdded = false;
            }
            if (chinese != null) { EnsureSecrets(); return chinese; }
            try
            {
                var loaded = MarkovChainData.LoadFromFile(ChineseCorpus);
                if (loaded == null || loaded.order != 2 || loaded.Chain == null || loaded.Chain.Count == 0)
                    throw new InvalidDataException("Invalid Chinese book corpus");
                chinese = loaded;
                EnsureSecrets();
                UnityEngine.Debug.Log("[QudCnSupplement] BOOK_CORPUS_LOADED: " + ChineseCorpus + " states=" + loaded.Chain.Count);
            }
            catch (Exception e)
            {
                if (!loadFailureLogged) { loadFailureLogged = true; UnityEngine.Debug.Log("[QudCnSupplement] BOOK_CORPUS_ERROR: " + e.Message); }
            }
            return chinese;
        }
    }


    private static void EnsureSecrets()
    {
        var game = XRL.The.Game;
        if (chinese == null || game == null || secretsAdded) return;
        // Wait for world creation to publish both coordinates, rather than
        // permanently considering a title-screen load to be postprocessed.
        if (!game.IntGameState.ContainsKey("RuinofHouseIsner_xCoordinate") ||
            !game.IntGameState.ContainsKey("RuinofHouseIsner_yCoordinate")) return;
        chineseGame = game;
        MarkovBook.PostprocessLoadedCorpus(chinese);
        secretsAdded = true;
        UnityEngine.Debug.Log("[QudCnSupplement] BOOK_ISNER_INJECTED: original world-specific 46 clues retained");
    }

    public static void SecretPrefix(MarkovChainData __0, ref string __1)
    {
        if (!QudCnSupplement.IsChinese || chinese == null || !ReferenceEquals(__0, chinese)) return;
        string translated = TranslateIsnerSecret(__1);
        if (translated == __1) UnityEngine.Debug.Log("[QudCnSupplement] BOOK_ISNER_UNMATCHED: " + __1);
        __1 = translated;
    }

    // Only the exact grammar emitted by 2.0.212.31 RuinOfHouseIsnerLore is
    // accepted. Direction, distance and original landmark are captured intact.
    public static string TranslateIsnerSecret(string source)
    {
        if (string.IsNullOrEmpty(source)) return source;
        var header = IsnerHeader.Match(source);
        if (!header.Success) return source;
        string body = header.Groups[3].Value;
        var location = IsnerStored.Match(body);
        string qualifier = "";
        if (location.Success)
        {
            string kind = location.Groups[1].Value;
            qualifier = kind == "rumored to be stored somewhere" ? "传闻藏在" :
                kind == "where I stored it somewhere" ? "我将它藏在" :
                kind == "located somewhere" ? "位于" : "据说藏在";
        }
        else
        {
            location = IsnerNear.Match(body);
            if (location.Success) qualifier = "位于";
            else { location = IsnerHidden.Match(body); if (location.Success) qualifier = "我将它藏在"; }
        }
        if (!location.Success) return source;
        string direction = location.Groups["direction"].Value;
        direction = direction == "east" ? "东" : direction == "west" ? "西" : direction == "north" ? "北" : "南";
        string distance = location.Groups["distance"].Success ? location.Groups["distance"].Value + "帕拉桑" : "不到一帕拉桑";
        string landmark = location.Groups["landmark"].Value;
        lock (Gate) Landmarks.Add(landmark);
        // Keep the landmark supplied by the actual world; do not guess or
        // transliterate arbitrary player/world-generated proper names.
        string noun = header.Groups[2].Value;
        noun = noun == "masterwork pistol Ruin of House Isner" ? "大师手枪伊斯纳家族之毁" :
            noun == "chest containing the Ruin of House Isner" || noun == "chest holding the Ruin of House Isner" ? "装着伊斯纳家族之毁的箱子" :
            noun == "famous revolver Ruin of House Isner" ? "著名左轮手枪伊斯纳家族之毁" :
            noun == "hiding place of the Ruin of House Isner" ? "伊斯纳家族之毁的藏匿处" :
            noun == "lost masterwork pistol" ? "失落的大师手枪" : "伊斯纳家族之毁";
        string story = location.Groups["story"].Success ? "，传说如此" : "";
        // Original AppendSecret recognizes the {...} group as one protected
        // clue and connects it through a two-word prefix. Use an existing,
        // sentence-opening CN state so these clues remain reachable from prose.
        return "传说 中 {" + noun + "，" + qualifier + landmark + "以" + direction + distance + "处" + story + ".}";
    }

    public static void GeneratePrefix(ref MarkovChainData __0, out bool __state)
    {
        __state = false;
        if (!QudCnSupplement.IsChinese) return;
        if (ReferenceEquals(__0, chinese) && chinese != null) { __state = true; return; }
        if (!IsDefaultChain(__0)) return;
        var translated = GetChineseChain();
        if (translated == null) return;
        __0 = translated;
        __state = true;
    }

    public static void GeneratePostfix(bool __state, ref string __result)
    {
        if (__state) __result = FormatChinese(__result);
    }

    public static string FormatChinese(string value)
    {
        if (string.IsNullOrEmpty(value)) return value;
        // Applied after public generation only, never to GenerateFragment state
        // transitions. This chain contains no English names or style markup.
        lock (Gate)
        {
            // AppendSecret embeds complete real landmark names inside a clue.
            // Protect them before lexical whitespace/punctuation is normalized;
            // e.g. Red Rock and Site 3.2 retain their original bytes.
            var names = new List<string>(Landmarks);
            names.Sort((a,b) => b.Length.CompareTo(a.Length));
            var protectedNames = new List<string>();
            foreach (var name in names)
            {
                if (string.IsNullOrEmpty(name) || !value.Contains(name)) continue;
                string marker = "\uE100" + protectedNames.Count + "\uE101";
                value = value.Replace(name, marker);
                protectedNames.Add(name);
            }
            value = Spaces.Replace(value, "").Replace(",", "，").Replace(".", "。");
            for (int i=0; i<protectedNames.Count; i++) value = value.Replace("\uE100" + i + "\uE101", protectedNames[i]);
            return value;
        }
    }

    public static void ContentsPostfix(MarkovBook __instance)
    {
        if (!QudCnSupplement.IsChinese || __instance == null || __instance.BookCorpus != DefaultCorpus ||
            string.IsNullOrEmpty(__instance.Title) || !Cjk.IsMatch(__instance.Title)) return;
        const string suffix = ": Unabridged";
        // The shipped SetContents appends this literal after its localized
        // unabridged wrapper. Only clean a newly generated CN book here.
        if (__instance.Title.EndsWith(suffix, StringComparison.Ordinal))
        {
            __instance.Title = __instance.Title.Substring(0, __instance.Title.Length - suffix.Length);
            if (__instance.ParentObject != null && __instance.ParentObject.Render != null)
                __instance.ParentObject.Render.DisplayName = __instance.Title;
        }
    }

    public static string TranslateKnownBookTitle(string title)
    {
        return title == ObservedTitle ? ObservedChineseTitle : title;
    }

    public static void BookNamePostfix(XRL.World.GameObject __instance, ref string __result)
    {
        if (!QudCnSupplement.IsChinese || __instance == null || string.IsNullOrEmpty(__result) ||
            !__instance.HasPart("MarkovBook")) return;
        // Exact known title in a known book object. Render decorations can wrap
        // it, but no global vocabulary substitutions or save mutations occur.
        var part = __instance.GetPart<MarkovBook>();
        if (part == null || part.Title != ObservedTitle) return;
        __result = __result.Replace(ObservedTitle, ObservedChineseTitle);
    }
}
