#!/usr/bin/env python3
"""Build CN-only HistorySpice. Engine verifies top-level lang before merging.
Replaces array leaves with '=' keys; keeps all code keys and redirect targets intact.
"""
import json,re,hashlib,argparse
from pathlib import Path
from collections import Counter
from opencc import OpenCC
import json5
ROOT=Path(__file__).resolve().parents[1]
cc=OpenCC('t2s')
SOURCE=ROOT/'sources/333640/3777400827/historyspice.zh-tw.json'
# Hand repairs for upstream placeholder hallucinations, omitted arguments and mistranslations.
REPAIRS={
('elements.circuitry.inspirationsVerbPhrase',0):'遇见了=spice.entity:objectPronoun=自身的电脑化版本',
('professions.scribe.actions',0):'记录了=spice.entity:possessivePronoun=生命最后一年的事件',
('professions.scribe.foundingVerbTombInscription',0):'撰写关于如何将=var=用于=activity=的编年史',
('professions.historian.foundingVerbTombInscription',0):'解读=var=与=activity=的历史',
('gossip.twoFaction',10):'=f1=在掷骰子时反复击败=f2=。',
('gossip.twoFaction',14):'=f1=冒充了=f2=的一位领袖。',
('gossip.twoFaction',16):'=f1=为=f2=烹制了一顿腐败的餐点。',
('gossip.twoFaction',19):'=f1=拒绝让=f2=进入当地的图书馆。',
('commonPhrases.fromThenOn',2):'在=spice.entity:name=余下的生命中',
('instancesOf.countered',0):'以=spice:elements.entity@elements[random].murdermethods.!random=杀死了每一个',
('instancesOf.groupMurdered_NotBy',0):'在为其烹制一顿腐败的餐点后被杀害',
('proverbs',18):'=sacredThing=栖居于=spice:commonPhrases.hearth.!random=',
('proverbsCoda',14):'=sacredThing=栖居于=spice:commonPhrases.hearth.!random=',
('tombstones.intro',3):'此处安息着的遗体属于',
('tombstones.intro',4):'此处安息着的遗骸属于',
('tombstones.cryptIntroSingular',0):'此处安息着=maybeFamilyCognomen=',
('tombstones.cryptIntroSingular',1):'此处长眠着=maybeFamilyCognomen=',
('tombstones.cryptIntroSingular',2):'其中安息着=maybeFamilyCognomen=',
('tombstones.cryptIntroSingular',3):'其中长眠着=maybeFamilyCognomen=',
('tombstones.cryptIntroSingular',4):'在格乔斯的庇护下安息着=maybeFamilyCognomen=',
('tombstones.cryptIntroPlural',0):'此处安息着=maybeFamilyCognomen=',
('tombstones.cryptIntroPlural',1):'此处长眠着=maybeFamilyCognomen=',
('tombstones.cryptIntroPlural',2):'其中安息着=maybeFamilyCognomen=',
('tombstones.cryptIntroPlural',3):'其中长眠着=maybeFamilyCognomen=',
('tombstones.cryptIntroPlural',4):'在格乔斯的庇护下安息着=maybeFamilyCognomen=',
('tombstones.cryptPlaque.royal.familyWords',1):'我们=markovSeed:are,do,see,feel,know,have,say,go,take=',
('tombstones.itemDeath2',0):'被掉落的=item.name:includeAdjunctNoun|strip=压死',
('tombstones.itemDeath2',1):'[x3]被掉落的=item.name:asIfKnown:includeAdjunctNoun|strip=压死',
('tombstones.itemDeath2',2):'在试图找回遗失的=item.name:includeAdjunctNoun|strip=时坠下悬崖',
('tombstones.itemDeath2',3):'[x3]在试图找回遗失的=item.name:asIfKnown:includeAdjunctNoun|strip=时坠下悬崖',
('villages.description',5):'=faction.the.name=及其=spice:commonPhrases.kin.!random=在=terrainFragment=举行=spice:commonPhrases.gathering.!random=',
('quests.FindaSpecificItem.sacred.lostOur',2):'=spice:instancesOf.fate.!random=使我们与我们的=item.name=分离',
('quests.FindaSpecificItem.sacred.takenTo',1):'听说=item.them==item.verb:have=被带到了=deliveryTarget=',
('history.gospels.LostItem.EarlySultanate',0):'=spice.entity:possessivePronoun=珍爱的=item=被窃贼=spice:history.gospels.EnemyHostName.EarlySultanate.!random=偷走',
('history.gospels.LostItem.LateSultanate',0):'=spice.entity:possessivePronoun=珍爱的=item=被窃贼=spice:history.gospels.EnemyHostName.LateSultanate.!random=偷走',
('history.gospels.LostItem.LateSultanate',1):'在窃贼=spice:history.gospels.CommittedWrongAgainstSultan.LateSultanate.!random=时失去了=spice.entity:possessivePronoun=珍爱的=item=',
}
REPAIRS.update({
('elements.chance.nouns',0):'=spice:numbers.!random=面骰子',
('elements.chance.nounsPlural',0):'=spice:numbers.!random=面骰子',
('professions.gambler.items',1):'=spice:numbers.!random=面骰子',
('itemTypes.ShortBlade',4):'曲刃匕首',('itemTypes.Cudgel',3):'短棍',
('commonPhrases.shortHearth',1):'小岛',
('instancesOf.countered',1):'在=spice:elements.entity@elements[random].practices.!random=中度过一天，随后继续=spice.entity:possessivePronoun=的统治，仿佛什么都没发生',
('instancesOf.forestPlaces',2):'林间山谷',('instancesOf.forestPlaces',3):'谷地',
('instancesOf.tar',0):'沥青',('instancesOf.tar',5):'沥青',('instancesOf.tar',6):'沥青',
('extradimensional.vacuous',6):'空白的',('extradimensional.vacuous',7):'空无的',
('cooking.recipeNames.foods',12):'无酵饼',
('cooking.recipeNames.ingredients.Vinewafer Sheaf.nounPlural',3):'无酵饼',
('cooking.recipeNames.ingredients.Vinewafer Sheaf.noun',3):'无酵饼',
('cooking.recipeNames.ingredients.Congealed Rubbergum.nounPlural',0):'橡胶',
('cooking.recipeNames.ingredients.Congealed Rubbergum.nounPlural',1):'胶块',
('cooking.recipeNames.ingredients.Congealed Rubbergum.noun',0):'橡胶',
('cooking.recipeNames.ingredients.Congealed Rubbergum.noun',1):'胶块',
('cooking.recipeNames.ingredients.Sliced Bop Cheek.noun',1):'博普',
('cooking.terrain.General.someEdible',13):'乌伊尔',
('cooking.terrain.General.aEdible',9):'乌伊尔种子',
('cooking.terrain.LakeHinnom.someIngredients',9):'斯瓦迪姆涎液',
('cooking.terrain.PalladiumReef.someIngredients',16):'斯瓦迪姆涎液',
('history.gospels.ObjectFoundBy.LateSultanate',0):'由垃圾海的钓矿人=spice:commonPhrases.rescued.!random=',
('history.gospels.ObjectFoundBy.LateSultanate',1):'以乌弗麻=spice:commonPhrases.wrapped.!random=',
})
for i in [4,6,7,8,9,10,12]:REPAIRS['textFilters.frog',i]='{{emote|*呱呱*}}'
REPAIRS['textFilters.waterbird',5]='{{emote|*嘎——*}}'
for i,zh in enumerate(['伊库斯','伊卡','', '乌库斯','','埃库斯','阿卡','埃卡','奥卡','乌卡','伊卡','伊库斯']):
    if zh:REPAIRS['items.suffixes',i]=zh
for kind,index in [('adj1',1),('adj2',2),('nounPlural',1),('noun',1)]:
    REPAIRS['cooking.recipeNames.ingredients.Fermented Tongue.'+kind,index]='格洛特'
for prefix in ['NormalityBreatherGlandPaste','ElderNormalityBreatherGlandPaste']:
    for kind in ['adj1','adj2']:REPAIRS['cooking.recipeNames.ingredients.'+prefix+'.'+kind,0]='零相'
for kind in ['adj1','nounPlural','noun']:REPAIRS['cooking.recipeNames.ingredients.asphalt.'+kind,0]='沥青'
for kind in ['adj1','nounPlural','noun']:REPAIRS['cooking.recipeNames.ingredients.goo.'+kind,0]='黏液'

def transform(x,path=()):
    if isinstance(x,dict):return {k:transform(v,path+(k.rstrip('='),)) for k,v in x.items()}
    if isinstance(x,list):return [REPAIRS.get(('.'.join(path),i),cc.convert(v)) if isinstance(v,str) else v for i,v in enumerate(x)]
    return cc.convert(x) if isinstance(x,str) else x

def leaves(x,path=()):
    if isinstance(x,dict):
        for k,v in x.items():yield from leaves(v,path+(k.rstrip('='),))
    else:yield path,x

def tokens(s):return Counter(re.findall(r'=[^=]*=',s))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,default=ROOT/'sources/HistorySpice.jsonc');args=ap.parse_args()
    base=json5.loads(args.base.read_text())['spice'];tw=json.loads(SOURCE.read_text())
    result={'lang':'CN','spice':transform(tw['spice'])}
    bl=dict(leaves(base));rl=dict(leaves(result['spice']))
    # Control redirects contain addresses, not natural language. Restore exact engine keys.
    repaired_redirects=[]
    def redirects(x,path=()):
        for k,v in x.items():
            p=path+(k.rstrip('='),)
            if isinstance(v,dict):redirects(v,p)
            elif k.rstrip('=').startswith('_'):
                if p in bl and v!=bl[p]:x[k]=bl[p];repaired_redirects.append('.'.join(p))
    redirects(result['spice']);rl=dict(leaves(result['spice']))
    issues=[];strings=0
    for path,b in bl.items():
        if path not in rl:issues.append({'path':'.'.join(path),'reason':'missing leaf'});continue
        r=rl[path];bs=b if isinstance(b,list) else [b];rs=r if isinstance(r,list) else [r]
        if len(bs)!=len(rs):issues.append({'path':'.'.join(path),'reason':'array length mismatch'});continue
        for i,(bv,rv) in enumerate(zip(bs,rs)):
            if not isinstance(bv,str):continue
            strings+=1
            # This token deliberately translates its literal argument, not its executable key.
            if path==('lovesick',) and i==4:continue
            if (re.match(r'^\[x\d+\]',bv) or [''])[0] != (re.match(r'^\[x\d+\]',rv) or [''])[0]:issues.append({'path':'.'.join(path),'index':i,'reason':'weight mismatch'})
            if tokens(bv)!=tokens(rv):issues.append({'path':'.'.join(path),'index':i,'reason':'placeholder mismatch','base':bv,'translated':rv})
    if issues:raise SystemExit(json.dumps(issues,ensure_ascii=False,indent=2))
    out=ROOT/'mod/historyspice.CN.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    report={'language':'CN','engine_filter':'HistoricSpice.Init compares top-level lang to LanguageLoader.ActiveLanguage before MergeModJson','array_merge':'= suffix replaces; unchanged from upstream','base_leaf_keys':len(bl),'translated_leaf_keys':len(rl),'missing_keys':len(set(bl)-set(rl)),'array_length_mismatches':0,'weight_mismatches':0,'placeholder_mismatches':0,'audited_strings':strings,'manual_repairs':len(REPAIRS),'redirect_repairs':repaired_redirects,'literal_token_argument_exceptions':['lovesick[4]: text.stutterize emote argument'], 'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'base_sha256':hashlib.sha256(args.base.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
    (ROOT/'data/history-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
