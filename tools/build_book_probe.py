#!/usr/bin/env python3
"""Generate procedural-book checks for the isolated QA mod, never the live save.
The final test temporarily creates an unsaved XRLGame only when no world exists,
runs the actual lore generator and postprocessor, and restores the core field.
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = ROOT/'analysis/private/qa-mod/BookProbe.cs'
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(r'''
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using XRL;
using XRL.World.Parts;

[HasModSensitiveStaticCache]
public static class QudCnBookProbe {
 static int passed, failed;
 static readonly Regex Latin = new Regex(@"[A-Za-z]");
 static readonly Regex Cjk = new Regex(@"[\u3400-\u9fff]");
 static void Check(string name, bool good, string detail="") {
  if(good)passed++;else failed++;
  UnityEngine.Debug.Log("[CN-BOOK-QA] "+name+"="+(good?"PASS":"FAIL")+"; "+detail);
 }
 [ModSensitiveCacheInit] public static void Init() {
  string before = XRL.UI.Options.Language;
  try {
   QudCnSupplement.Init();
   XRL.UI.Options.Language="en";
   var original=MarkovChainData.LoadFromFile(QudCnBooks.DefaultCorpus);
   string originalHash=Fingerprint(original);
   XRL.Rules.Stat.ReseedFrom(77113);
   string baseline=MarkovChain.GenerateTitle(original);
   XRL.UI.Options.Language="CN";
   int titles=0, sentences=0, paragraphs=0, minTitle=9999, maxTitle=0, minBody=9999, maxBody=0;
   for(int i=0;i<100;i++) {
    XRL.Rules.Stat.ReseedFrom(29000+i);
    string title=MarkovChain.GenerateTitle(original);
    string sentence=MarkovChain.GenerateSentence(original,null);
    string paragraph=MarkovChain.GenerateParagraph(original);
    if(IsChinese(title) && title.Length>=2 && title.Length<=100)titles++;
    if(IsChinese(sentence) && sentence.Length>=4 && sentence.Length<=600)sentences++;
    if(IsChinese(paragraph) && paragraph.Length>=4 && paragraph.Length<=6000)paragraphs++;
    minTitle=Math.Min(minTitle,title.Length);maxTitle=Math.Max(maxTitle,title.Length);
    minBody=Math.Min(minBody,paragraph.Length);maxBody=Math.Max(maxBody,paragraph.Length);
    if(i<3)UnityEngine.Debug.Log("[CN-BOOK-QA] sample="+title+" | "+paragraph);
   }
   Check("CN titles",titles==100,titles+"/100; length="+minTitle+".."+maxTitle);
   Check("CN sentences",sentences==100,sentences+"/100");
   Check("CN paragraphs",paragraphs==100,paragraphs+"/100; length="+minBody+".."+maxBody);
   XRL.UI.Options.Language="en";
   XRL.Rules.Stat.ReseedFrom(77113);
   string english=MarkovChain.GenerateTitle(original);
   Check("EN chain unchanged",english==baseline && Latin.IsMatch(english),english);
   Check("original graph unchanged",Fingerprint(original)==originalHash);
   XRL.UI.Options.Language="CN";
   var other=new MarkovChainData();other.order=2;
   other.OpeningWords.Add("custom English");
   other.Chain.Add("custom English",new List<string>{"text."});
   var candidate=other;bool changed;
   QudCnBooks.GeneratePrefix(ref candidate,out changed);
   string otherText=MarkovChain.GenerateSentence(other,null);
   Check("other corpus unchanged",!changed && Object.ReferenceEquals(candidate,other) && Latin.IsMatch(otherText),otherText);
   var book=XRL.World.GameObject.Create("MarkovBook");
   var part=book.GetPart<MarkovBook>();
   Check("MarkovBook blueprint",part!=null);
   if(part!=null) {
    part.Title="The Orator Domineers the West";book.Render.DisplayName=part.Title;
    string display=book.DisplayName;
    Check("observed title CN context",display.Contains("演说家统御西方") && part.Title=="The Orator Domineers the West",display);
    XRL.UI.Options.Language="en";
    Check("observed title EN context",book.DisplayName.Contains("The Orator Domineers the West"),book.DisplayName);
    XRL.UI.Options.Language="CN";
    var nonBook=XRL.World.GameObject.Create("Book");nonBook.Render.DisplayName="The Orator Domineers the West";
    Check("non Markov title untouched",nonBook.DisplayName.Contains("The Orator Domineers the West"),nonBook.DisplayName);
    int valid=0;
    for(int i=0;i<100;i++) {
     part.SetContents(39000+i,QudCnBooks.DefaultCorpus);
     if(part.BookCorpus==QudCnBooks.DefaultCorpus && part.BookSeed==39000+i && Cjk.IsMatch(part.Title) && !part.Title.Contains("Unabridged") && book.Render.DisplayName==part.Title)valid++;
    }
    Check("SetContents saved metadata",valid==100,valid+"/100");
   }
   int protectedNames=0;
   foreach(var name in new string[]{"Hope-in-Motion","Red Rock","Site 3.2"}) {
    string clue="of the {Ruin of House Isner, said to be stored somewhere 3 parasangs east of "+name+".}";
    string display=QudCnBooks.FormatChinese(QudCnBooks.TranslateIsnerSecret(clue));
    if(display.Contains(name) && display.Contains("以东3帕拉桑"))protectedNames++;
   }
   Check("landmarks preserved",protectedNames==3,protectedNames+"/3");
   string unknown="of the {unknown future lore, Red Rock.}";
   Check("unknown lore not guessed",QudCnBooks.TranslateIsnerSecret(unknown)==unknown);
   TestIsner(original,originalHash);
  } catch(Exception e) {Check("exception",false,e.ToString());}
  finally {XRL.UI.Options.Language=before;}
  UnityEngine.Debug.Log("[CN-BOOK-QA] total="+passed+" PASS / "+failed+" FAIL");
 }
 static bool IsChinese(string s) { return !String.IsNullOrEmpty(s) && Cjk.IsMatch(s) && !Latin.IsMatch(s) && !s.Contains(" ") && !s.Contains("."); }
 static string Fingerprint(MarkovChainData data) {
  var keys=new List<string>(data.Chain.Keys);keys.Sort(StringComparer.Ordinal);
  var b=new StringBuilder();b.Append(data.order).Append('\0');
  foreach(var s in data.OpeningWords)b.Append(s).Append('\0');
  foreach(var k in keys){b.Append(k).Append('\0');foreach(var s in data.Chain[k])b.Append(s).Append('\u0001');b.Append('\0');}
  using(var sha=SHA256.Create())return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(b.ToString())));
 }
 static void TestIsner(MarkovChainData original,string originalHash) {
  var core=XRL.The.Core;
  var coreField=typeof(XRL.Core.XRLCore).GetField("Core",BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static);
  var gameField=typeof(XRL.Core.XRLCore).GetField("Game",BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance);
  if(gameField==null || coreField==null){Check("Isner core fields",false);return;}
  object beforeCore=coreField.GetValue(null);
  bool fakeCore=core==null;
  if(fakeCore) {core=new XRL.Core.XRLCore();coreField.SetValue(null,core);}
  object before=gameField.GetValue(core);bool fake=false;
  try {
   if(before==null) {
    var game=new XRL.XRLGame();
    game.IntGameState["RuinofHouseIsner_xCoordinate"]=20;
    game.IntGameState["RuinofHouseIsner_yCoordinate"]=20;
    gameField.SetValue(core,game);fake=true;
   }
   var active=XRL.The.Game;
   int x,y;
   if(!active.IntGameState.TryGetValue("RuinofHouseIsner_xCoordinate",out x)||!active.IntGameState.TryGetValue("RuinofHouseIsner_yCoordinate",out y)) {Check("Isner coordinates",false,"No unsaved world coordinates");return;}
   int translated=0;
   for(int i=0;i<200;i++) {
    string lore=XRL.LoreGenerator.RuinOfHouseIsnerLore(x,y);
    string cn=QudCnBooks.TranslateIsnerSecret(lore);
    if(cn!=lore && cn.Contains("帕拉桑") && cn.EndsWith(".}") && cn.Contains("以"))translated++;
    if(i<3)UnityEngine.Debug.Log("[CN-BOOK-QA] Isner actual="+lore+" => "+cn);
   }
   Check("actual Isner lore translation",translated==200,translated+"/200; dynamic landmark retained");
   // GetChineseChain calls the original PostprocessLoadedCorpus now that the
   // actual runtime sees coordinate keys. The installed AppendSecret prefix
   // translates only this separate CN chain, leaving the EN graph unchanged.
   var cnChain=QudCnBooks.GetChineseChain();int clues=0;
   foreach(var pair in cnChain.Chain)foreach(var word in pair.Value)if(word.Contains("伊斯纳家族之毁")||word.Contains("失落的大师手枪"))clues++;
   Check("Isner clues injected",clues>=46,"protected clue transitions="+clues);
   List<string> clueChoices;int reachableClues=0;
   if(cnChain.Chain.TryGetValue("传说 中",out clueChoices))foreach(var word in clueChoices)if(word.Contains("伊斯纳家族之毁")||word.Contains("失落的大师手枪"))reachableClues++;
   Check("Isner clues reachable",reachableClues>=46 && cnChain.OpeningWords.Contains("传说 中"),"reachable clue successors="+reachableClues);
   Check("EN graph after Isner unchanged",Fingerprint(original)==originalHash);
  } finally {
   if(fake) {
    gameField.SetValue(core,before);
    // This is isolated QA only: discard the temporary unsaved world's CN chain.
    var flags=BindingFlags.Static|BindingFlags.NonPublic;
    typeof(QudCnBooks).GetField("chinese",flags).SetValue(null,null);
    typeof(QudCnBooks).GetField("chineseGame",flags).SetValue(null,null);
    typeof(QudCnBooks).GetField("secretsAdded",flags).SetValue(null,false);
   }
   if(fakeCore)coreField.SetValue(null,beforeCore);
  }
 }
}
''', encoding='utf-8')
print(p)
