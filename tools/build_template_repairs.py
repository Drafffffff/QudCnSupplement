#!/usr/bin/env python3
"""Emit exact-field repairs for reviewed Chinese grammar templates; no global replacement.
Run before build_corpus, after its literal-unit baseline has been audited.
"""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'=[^=\n]+=')
OP = re.compile(r'\.(Doesly|itDoes|Does|does|verb|is|a|A|the|The|andList|orList|ifPlural|ordinalName|pluralize|things)(?=[:.#|=])')
VERB = re.compile(r'^=(?P<ref>[^=:#|]+)\.(?P<op>Does|does|verb):(?P<verb>[^=:#|]+)(?P<args>(?::[^=|]+)?)(?P<filter>(?:\|[^=]+)?)=$')
# Reviewed lexical verbs only. Polysemous / heavily mistranslated contexts remain explicit review.
WORDS = {
 'gain':'获得','lose':'失去','reflect':'反射','begin':'开始','stop':'停止','start':'开始',
 'emit':'发出','release':'释放','explode':'爆炸','disappear':'消失','appear':'出现',
 'teleport':'传送','jump':'跳跃','drink':'喝下','eat':'吃下','use':'使用','deal':'造成',
 'resist':'抵抗','heal':'治疗','need':'需要','activate':'激活','intercept':'拦截',
 'clean':'清洁','lop':'砍下','chop':'砍断','identify':'鉴定','perform':'进行',
 'exit':'退出','wake':'醒来','intimidate':'威吓','cause':'使','grow':'生长',
 'shoot':'射出','loosen':'松开','push':'推动','refuse':'拒绝','yell':'大喊',
 'collapse':'崩塌','detonate':'引爆','impale':'刺穿','swim':'游泳','seal':'封住',
 'destabilize':'扰乱','stand':'站立','remove':'移除','add':'增加','penetrate':'穿透',
 'invoke':'唤起','dig':'挖掘','discharge':'放电','touch':'触碰','fling':'掷出',
 'spot':'发现','sense':'感应','detach':'脱落','disarm':'缴械','enter':'进入','press':'按下',
 'snore':'打鼾','ogle':'凝视','emerge':'钻出','stiffen':'变得僵硬','suffer':'承受',
 'beguile':'魅惑','stare':'凝视','wince':'畏缩','spark':'冒火花','buzz':'嗡鸣',
 'shift':'变换','waver':'摇曳','rebuke':'斥责','regenerate':'再生','ignore':'忽略',
 'give':'给予','burn':'烧毁','vomit':'呕吐','grant':'赋予','receive':'获得','unlock':'解锁',
 'desecrate':'亵渎','implode':'内爆','equip':'装备','unequip':'卸下','raise':'举起',
 'break':'打破','toss':'抛出','shout':'喊叫','flinch':'退缩','hum':'嗡鸣',
 'leak':'泄漏','dissipate':'消散','cease':'停止','disintegrate':'解体',
 'dematerialize':'消失','shimmer':'闪烁','hiss':'嘶鸣','extrude':'挤出',
 'swap':'交换','click':'咔哒作响','wade':'涉水','collect':'收集','unseal':'解封',
 'bandage':'包扎','staunch':'止住','crumble':'碎裂','shatter':'粉碎','require':'需要',
 'erupt':'喷发','peer':'凝视','conjure':'召唤','sunder':'撕裂','attempt':'尝试',
 'blur':'模糊','multiply':'增殖','focus':'聚焦','tighten':'收紧','evade':'躲避',
 'recharge':'充能','revert':'恢复','absorb':'吸收','spit':'吐出','strike':'击打',
 'collide':'碰撞','flicker':'闪烁','vanish':'消失','continue':'继续','cleave':'劈开',
 'hook':'钩住','teach':'教会','extinguish':'扑灭','smash':'砸碎','howl':'嚎叫',
 'launch':'发射','cannot':'无法','see':'看见','amputate':'截断','grab':'抓住',
 'climb':'攀爬','throw':'投掷','try':'尝试', 'have':'拥有',"don't":'不',"aren't":'不是',"won't":'不会',
}
# English auxiliary be is already expressed by the existing Chinese predicate.
BE = {'are','is','am','were','was','be'}
BRANCH = {
 '=verb:claim:afterpronoun=':'声称拥有',
 '=subject.pluralize.word:companion=':'同伴',
 '=subject.pluralize.word:生物=':'生物',
 '=subject.Doesly:gently:shake=':'=subject.The.name=轻轻摇动',
 '=subject.Doesly:merely:click=':'=subject.The.name=只是咔哒作响',
 '=subject.Doesly:suddenly:start=':'=subject.The.name=',
 '=subject.Doesly:accidentally:destroy=':'=subject.The.name=意外摧毁',
 '=subject.Doesly:permanently:drain=':'=subject.The.name=',
 '=object.Doesly:already:have=':'=object.The.name=',
 '=subject.itDoes:starve=':'=subject.it=饥饿不堪',
 '=number.ifPlural:points:point=':'点',
 '=number.ifPlural:点:点=':'点',
 '=skills.pluralize:已:已=':'已',
 '=duration.things:回合:回合=':'=duration= 回合',
 '=left.things:more round:more rounds=':'再等 =left= 回合',
 '=books.pluralize:book was:books were=':'本书',
 '=bookshelves.pluralize:bookshelf was:bookshelves were=':'个书架',
 '=crops.pluralize:crop was:crops were=':'株作物',
 '=gadgets.pluralize:gadget was:gadgets were=':'件装置',
 '=furniture.pluralize:was:were=':'',
 '=numClones.ifPlural:reflections:a reflection=':'倒影',
 '=numClones.ifPlural:are:is=':'',
 # Existing Chinese already says 凭空现身; the English appear is redundant.
 '=numClones.ifPlural:appear:appears=':'',
 '=part.ifPlural:they aren\'t:it isn\'t=':'=part.ifPlural:它们不是:它不是=',
 '=part.ifPlural:they don\'t:it doesn\'t=':'=part.ifPlural:它们不:它不=',
}

def subject(ref, op, args, filt):
    # it/It was an explicit pronoun request: preserve the same referent and casing.
    if ref.endswith(('.it','.It')):
        if args:
            return None
        return '=' + ref + filt + '='
    # Only native name options whose counterparts exist on name are retained.
    if args and not all(x in {'single','long','withTitles','includeAdjunctNoun','asIfKnown','notAsPossessed'} for x in args[1:].split(':')):
        return None
    return '=' + ref + ('.The.name' if op == 'Does' else '.the.name') + args + filt + '='

def translation(verb, left, right, op):
    tail = right.lstrip()
    # Context-reviewed idioms and predicates already translated elsewhere in this same clause.
    if verb in {'容纳','拥有','含有','劈裂','挖掘'}: return verb
    if verb=='是' and tail.startswith(('价值','比平常','两倍')): return ''
    if verb=='turn': return '转动'
    if verb=='burst': return '迸裂'
    if verb=='pony': return '拿出'
    if verb=='seem': return '似乎'
    if verb=='fall':
        if tail.startswith(('到地上','穿过')): return '掉落'
        if tail.startswith(('睡着','从上方落下')): return ''
        if tail.startswith('=object.tag:FallPreposition:'): return '落'
    if verb=='pour':
        if tail.startswith('水倒在'): return '把'
        if tail.startswith(('淡水淋遍','来自')): return '把'
        if tail.startswith('出'): return '倒'
    if verb=='beat': return '用'
    if verb=='burrow': return '钻入' if op!='verb' else '钻出'
    if verb=='assume': return '摆出' if tail.startswith('柔韧') else '变成'
    if verb=='shank': return '刺击'
    if verb=='flush': return '顿生'
    if verb=='thirst': return '口渴'
    if verb=='freeze': return '冻结' if not tail.startswith('用冷冻') else ''
    if verb=='toast': return '' if tail.startswith('用火焰') else '灼烧'
    if verb=='drop': return '下降' if tail.startswith('到') else '放下'
    if verb=='expel': return '' if tail.startswith('会根据') else '喷出'
    if verb=='go' and tail.startswith('俯卧'): return ''
    if verb=='clasp': return '紧握'
    if verb=='fail': return '未能'
    if verb=='dismiss': return '遣散'
    if verb=='wander': return ''
    if verb=='dust': return '扫去'
    if verb=='blink': return '闪现'
    if verb=='lapse': return '重'
    if verb=='bear': return '带有'
    if verb=='voice': return ''
    if verb=='discorporate': return '形体消散'
    if verb=='blow': return '吹'
    if verb=='plop': return '扑通落下'
    if verb=='make': return '' if tail.startswith('没有声音') else '扎'
    if verb=='light': return '点燃'
    if verb=='tinker': return '制造'
    if verb=='flip': return '反转'
    if verb=='decide': return '决定'
    if verb=='vibrate': return ''
    if verb=='pass': return '' if tail.startswith('穿过') else '穿过'
    if verb=='slip' and tail.startswith('躲开'): return ''
    if verb=='attune': return '调谐'
    if verb=='incense': return '激怒'
    if verb=='latch': return ''
    if verb=='transfer': return '转移'
    if verb=='match': return '调整'
    if verb=='bump': return ''
    if verb=='impel': return '促使'
    if verb=='bask': return '沐浴'
    if verb=='pop' or verb=='slot': return ''
    if verb=='shake' or verb=='draw': return ''
    if verb=='flinch' and tail.startswith('闪身躲开'): return ''
    if verb=='chop' and tail.startswith('下'): return '砍'
    if verb=='come' and tail.startswith('与'): return ''
    if verb=='take':
        if tail.startswith(('电击伤害','下一次伤害','接下来','=damage=')): return '承受'
        if tail.startswith('=object.the.name='): return '拿起'
        if tail.startswith('了一口'): return '吸'
        if not tail and '受到可避免的伤害' in left:return ''
    if verb=='do' and tail.startswith(('电量不足','现在似乎','似乎没有')): return ''
    if verb=='swim': return ''
    if verb=='wade': return ''
    if verb=='grow' and tail.startswith('满身'): return '长'
    if verb in {'staunch','toss','strike','hook','smash','amputate','throw'} and tail.startswith(('用','将')): return ''
    if verb in {'extrude','shoot','spit','dig'} and tail.startswith('出'): return {'extrude':'挤','shoot':'射','spit':'吐','dig':'挖'}[verb]
    if verb=='resist' and tail.startswith('抵住'): return ''
    if verb=='recharge' and tail.startswith('从伤害中恢复'): return ''
    if verb=='cleave' and tail.startswith('劈开'): return ''
    if verb=='spot' and tail.startswith('发现'): return ''
    if verb=='grab' and tail.startswith('抓住'): return ''
    if verb=='launch' and tail.startswith('发起'): return ''
    if verb=='stand' and tail.startswith('稳'): return '站'
    if verb=='invoke' and tail.startswith('在'): return ''
    if verb=='invoke' and tail.startswith('出'): return '激发'
    if verb=='peer' and tail.startswith('望入'): return ''
    if verb=="aren't" and tail.startswith('没有'): return ''
    if verb in BE:
        return ''
    if verb == 'do':
        if tail.startswith(('无法','不能','不会','没有','不','可','能')): return ''
        return None
    if verb == 'become':
        if tail.startswith(('陷入','免疫','不受','更','相位','失去','获得','恐惧')): return ''
        return '变得'
    if verb == 'take':
        if tail.startswith(('受到','利用','控制','从')) or left.rstrip().endswith('受到'):return ''
        if tail.startswith('一口'):return '喝下'
        if tail.startswith(('伤害','的坠落','来自','可避免')):return '承受'
        return None
    if verb == 'fall':
        if tail.startswith(('爱上','倒下')):return ''
        if tail.startswith('{{C|睡眠'):return '陷入'
        return None
    if verb == 'miss' and ('未命中' in right): return ''
    if verb == 'miss':return '未命中'
    if verb == 'slip' and '滑倒' in right:return ''
    if verb == 'have' and (tail.startswith(('没有','没什么','提升了','倒下','达到','被')) or ('反射护盾停用了' in right)):return ''
    if verb == "don't":
        if tail.startswith(('没有','似乎无法','不能','无法')):return ''
        if tail.startswith('有'):return '没'
        if tail.startswith('在接下来'):return '不会'
    if verb == 'get':
        if tail.startswith(('被','皮肤瘙痒','疾病')):return ''
        if tail.startswith(('可用来','可饮用','+','=bonus')):return '获得'
        return None
    if verb == 'phase' and tail.startswith(('入相','出相','重新入相')):return ''
    if verb == 'freeze' and tail.startswith('用冷冻念力冻结'):return ''
    if verb == 'feel' and tail.startswith(('内心','自己')):return ''
    if verb == 'feel':return '感觉'
    if verb == 'manage' and tail.startswith('还是设法'):return ''
    if verb == 'shower' and ('火花' in right):return ''
    if verb == 'cool' and tail.startswith('冷却'):return ''
    if verb == 'emit' and tail.startswith(('从','发出','在等级','每层')):return ''
    if verb == 'emit' and tail.startswith('出'):return '发'
    if verb == 'release' and left.rstrip().endswith(('产生','会')):return None
    if verb == 'release' and tail.startswith('在等级'):return ''
    if verb == 'stop' and tail.startswith('流血'):return '停止'
    word=WORDS.get(verb)
    if word and tail.startswith(word):return ''
    return word

EXACT = {
 '在 =tier= 等级时，每次电力生成会产生 =subject.it.does:release= 次电击放电。': '=subject.it=释放一次电击放电，效果相当于 =tier= 级发电。',
 '在等级 5-6 时，每一次电力生成(发电)会 =subject.it.does:release= 一次电放电。': '=subject.it=释放一次电击放电，效果相当于 5-6 级发电。',
}

def fix(text):
    if text in EXACT:
        after=EXACT[text]
        old=collections.Counter(TOKEN.findall(text));new=collections.Counter(TOKEN.findall(after))
        old.subtract(['=subject.it.does:release=']);new.subtract(['=subject.it='])
        assert +old==+new
        return after,[{'before_token':'=subject.it.does:release=','after':'=subject.it=','reason':'source says release a discharge per Electrical Generation rank; restore predicate placement, retaining subject and rank','literal_before':text,'literal_after':after}]
    changes=[]
    def replace(m):
        tok=m.group();left=text[:m.start()];right=text[m.end():]
        replacement=None;reason=None
        pm=re.fullmatch(r"=([^=]+\.(?:name|Name|shortsingle|shortname))'s((?::[^=|]+)?(?:\|[^=]+)?)=",tok)
        if pm:
            replacement='='+pm[1]+pm[2]+'='+('' if right.lstrip().startswith('的') else '的')
            reason='terminal possessive name; retain referent/name options and emit Chinese 的 once'
        elif tok in BRANCH:
            replacement=BRANCH[tok];reason='reviewed literal branch/idiom/explicit adverb; retain quantity, pronoun, and object referents when meaningful'
        else:
            vm=VERB.fullmatch(tok)
            if vm:
                ref,op,verb,args,filt=(vm[k] for k in ('ref','op','verb','args','filter'))
                if args == ':afterPronoun' and op=='verb' and verb in BE:
                    replacement='';reason='auxiliary be after already preserved pronoun'
                elif not args or op!='verb':
                    word=translation(verb,left,right,op)
                    if word is not None:
                        subj='' if op=='verb' else subject(ref,op,args,filt)
                        # Filter on a bare verb has no remaining string target; strip is safe on literal CN.
                        if subj is not None and (not filt or filt=='|strip'):
                            replacement=subj+word
                            if verb=='cool' and ref=='subject.it' and left.endswith('=subject.Does:are= 正在 '):
                                replacement=''
                            reason=('Chinese predicate already present / auxiliary omitted' if word=='' else 'reviewed literal Chinese verb')+'; '+('subject naming/pronoun retained' if op!='verb' else 'verb-only operation; existing subject untouched')
            else:
                im=re.fullmatch(r'=([^=]+)\.([iI]t)\.is=',tok)
                if im:
                    replacement='='+im[1]+'.'+im[2]+'=';reason='preserve explicit subject pronoun; Chinese predicate supplies copula'
                elif tok=='=pool.is=' and left.rstrip().endswith('那边'):
                    replacement='有';reason='existential there is; explicit pool name remains in next token'
                elif tok=='=item.is=' and left.rstrip().endswith('=item.a.name='):
                    replacement='是什么';reason='source remember what item is; retain item name and restore what question'
                elif re.fullmatch(r'=[^.=:|]+\.is=',tok):
                    # Only drop when there is a Chinese predicate or a prior explicit name.
                    if re.match(r'\s*[\u4e00-\u9fff]',right):
                        replacement='';reason='verb-only auxiliary be; existing Chinese predicate/name retained'
        if replacement is None or replacement==tok:return tok
        changes.append({'before_token':tok,'after':replacement,'reason':reason})
        return replacement
    result=TOKEN.sub(replace,text)
    for bad,good in [('砍下 关闭','砍下'),('砍断 关闭','砍断')]:
        if bad in result:
            result=result.replace(bad,good)
            changes.append({'before_token':'关闭','after':'','reason':'source off means limb severance, not close; exact field lexical correction','kind':'literal'})
    # Every unchanged template expression must be preserved, including multiplicity.
    old=collections.Counter(TOKEN.findall(text));new=collections.Counter(TOKEN.findall(result))
    for change in changes:
        old.subtract(TOKEN.findall(change['before_token']))
        new.subtract(TOKEN.findall(change['after']))
    assert +old==+new,(text,result,old,new)
    return result,changes

def main():
    rows=json.loads((ROOT/'data/audit-fields.json').read_text())
    prior_file=ROOT/'data/template-repairs.json'
    prior=json.loads(prior_file.read_text()) if prior_file.exists() else []
    prior_by={(x['file'],x['path']):x for x in prior}
    baseline_path=ROOT/'data/template-grammar-baseline.json'
    baseline=json.loads(baseline_path.read_text()) if baseline_path.exists() else []
    baseline_by={(x['file'],x['path']):x for x in baseline}
    repairs=[];operations=collections.Counter();verbs=collections.Counter();units=collections.Counter();remaining=[]
    for row in rows:
        before=row['translation'];key=(row['file'],row['path'])
        if key in baseline_by:before=baseline_by[key]['translation']
        elif key in prior_by and before==prior_by[key]['after']:before=prior_by[key]['before']
        if key not in baseline_by and (OP.search(before) or "name's" in before or "Name's" in before):
            baseline_by[key]={'file':row['file'],'path':row['path'],'source':row['source'],'translation':before}
        for tok in TOKEN.findall(before):
            for op in OP.finditer(tok):operations[op[1]]+=1
            for vm in re.finditer(r'\.(?:Does|does|verb):([^=:#|]+)',tok):verbs[vm[1]]+=1
            for um in re.finditer(r'\.(?:ifPlural|pluralize|things):([^=|]+)',tok):units[um[1]]+=1
        after,changes=fix(before)
        if changes:
            repairs.append({'file':row['file'],'path':row['path'],'source':row['source'],'before':before,'after':after,'reason':'Reviewed finite source-template grammar repair; exact before required','changes':changes})
        for tok in TOKEN.findall(after):
            if OP.search(tok) or "name's" in tok or "Name's" in tok:
                category=('dynamic_verb' if re.search(r'\.(?:Does|verb)#',tok) else 'name_format' if re.search(r'\.(?:a|A|the|The)(?=[:.#|=])',tok) or "name's" in tok else 'localized_branch' if re.search(r'\.(?:ifPlural|pluralize):[\u4e00-\u9fff]',tok) else 'list_join' if re.search(r'\.(?:andList|orList)',tok) else 'body_part_ordinal' if '.ordinalName' in tok else 'dynamic_noun_plural')
                remaining.append({'file':row['file'],'path':row['path'],'token':tok,'translation':after,'source':row['source'],'category':category,'reason':'Keep for typed runtime semantic hook; localized branches already Chinese; dynamic values must preserve object/name identity'})
    tests=[('=subject.Does:are= 被迫回到地表。','=subject.The.name= 被迫回到地表。'),('=subject.it.does:gain= +8 敏捷','=subject.it=获得 +8 敏捷'),('=subject.thisCreature= =subject.verb:are= 被点燃','=subject.thisCreature=  被点燃'),('=number.ifPlural:points:point=','点'),('=subject.Does#verb= =object.the.name=','=subject.Does#verb= =object.the.name='),('{{G|=subject.Does:emit= 从 =subject.its= =part.ordinalName= 发出一道射线！}}','{{G|=subject.The.name= 从 =subject.its= =part.ordinalName= 发出一道射线！}}')]
    for original,expected in tests:
        assert fix(original)[0]==expected,(original,fix(original),expected)
    for r in repairs:assert fix(r['after'])[0]==r['after'],r
    audit={'schema':1,'operations_before':dict(operations.most_common()),'verb_arguments':dict(verbs.most_common()),'unit_and_plural_branch_arguments':dict(units.most_common()),'repairs':len(repairs),'changed_tokens':sum(len(x['changes']) for x in repairs),'remaining_occurrences':len(remaining),'remaining_categories':dict(collections.Counter(x['category'] for x in remaining)),'remaining':remaining,'native_evidence':{'assembly':'Assembly-CSharp.dll','GameObject.does':'0x06005ced','GameObject.Does':'0x06005cee','observed':'Both emit subject via GetDisplayName/GetPronounProvider plus GetVerb. Lower/upper variants select Subjective/CapitalizedSubjective and it/It. Replacer forwards name/pronoun options. No general global name replacement.'},'selftests':{'cases':len(tests),'field_token_preservation':len(repairs),'idempotence':len(repairs)}}
    baseline_path.write_text(json.dumps(list(baseline_by.values()),ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/template-repairs.json').write_text(json.dumps(repairs,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/template-grammar-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    unresolved=collections.Counter()
    for r in remaining:
        for m in OP.finditer(r['token']):unresolved[m[1]]+=1
    md=f'''# 中文模板语法审计\n\n修复 {len(repairs)} 个完全匹配字段、{audit['changed_tokens']} 处模板 token。所有其他 token 均按出现次数检查完整保留；修复前后颜色标记、对象与数值引用不改动。逐条原文、译文与 token 差异见 `template-repairs.json`。\n\n## 接入\n\n在 `build_corpus.py` 的 `literal_unit_operations` 之后、`chosen` 和 `audit.append` 之前，以 `(path.name, repr(k))` 查询修复。必须校验 `translated == repair["before"]`，再使用 `repair["after"]`；不匹配应报告或失败，切勿猜测替换。已经是 `after` 可直接跳过。执行 `tools/build_template_repairs.py` 可重建并自测；`template-grammar-baseline.json` 保存稳定修复前快照；已修复的 audit 不会导致第二次生成丢失修复。\n\n## 原生语义\n\n原生 `GameObject.does` (0x06005ced) 与 `Does` (0x06005cee) 都输出主语加动词，仅代词大小写有差异。修复保留显式 `.it`/`.It` 代词；常规 Does/does 使用对应 The/the.name，保留已确认的姓名选项；verb 仅替换动词，不增添主语。动态 `Does#verb`、未确认参数和多义词均保留人工审阅。原生姓名生成仍由引擎负责，玩家姓名与生成地名不会被全局替换。\n\n## 审阅边界\n\n剩余操作计数：`{dict(unresolved)}`。剩余类型：`{audit['remaining_categories']}`。完整文件/字段/token/上下文见 `template-grammar-audit.json` 的 remaining。andList/orList、ordinalName 需类型感知运行时语义钩子；a/the 可能承载名称格式选项，保留原生调用。pluralize 无文字参数常为对象名复数化，不能替换对象名称。非英语分支本身没有汉化缺口。字面静态动词、明确英文单位及两种 Doesly/itDoes 变体已按原文和上下文审阅修订；余下20处动态动词由调用处注入，需运行时词典翻译。andList/orList、名称格式、序数和动态名词需由对应引擎语义钩子完成，不能把静态审计误称为全游戏100%语义覆盖。\n\n## 自测\n\n{len(tests)} 个主语/代词/verb-only/单位/动态动词保留/嵌套颜色用例通过；{len(repairs)} 个字段 token 不变量与幂等性检查通过。\n'''
    (ROOT/'data/TEMPLATE_GRAMMAR.md').write_text(md)
    print(json.dumps({k:audit[k] for k in ('operations_before','repairs','changed_tokens','selftests')},ensure_ascii=False));print('remaining',dict(unresolved))

if __name__=='__main__':main()
