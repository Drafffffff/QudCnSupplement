#!/usr/bin/env python3
"""Build a field-level CN supplement against the supplied 2.0.212.31 example corpus.
Requires: pip install opencc-python-reimplemented. No network calls.
"""
import argparse, collections, copy, hashlib, json, re
from pathlib import Path
import xml.etree.ElementTree as ET
from opencc import OpenCC
ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'sources'
DISPLAY_NAMES = {'prefix','postfix','infix','zone','value','template','step','relictypemapping','quest','pregen','location'}
KEYS = ('Name','ID','Context','Key','Class','Level','x','y','Type')

def fields(root):
    out = {}; nodes = {}
    def walk(e,path):
        counts=collections.Counter()
        for child in e:
            attrs=tuple((k,child.get(k)) for k in KEYS if child.get(k) is not None and not (k=='Name' and (child.tag in DISPLAY_NAMES or child.get('ID') is not None)))
            token=(child.tag,attrs); counts[token]+=1
            p=path+((child.tag,attrs,counts[token]),); nodes[p]=child
            for k,v in child.attrib.items(): out[(p,k)]=v
            if child.text and child.text.strip(): out[(p,'#text')]=child.text
            walk(child,p)
    walk(root,()); return out,nodes

def plain(s):return s.replace('▶','')
def latin(s):
    s=re.sub(r'=(?=[A-Za-z])[A-Za-z][^=]*=', '',s)
    s=re.sub(r'{{[^|{}]+\|','',s)
    return bool(re.search(r'[A-Za-z]{2}',s))
def tokens(s):return collections.Counter(re.findall(r'=(?=[A-Za-z])[A-Za-z][^=]*=',s))
def translate_visible_glossary(file,source,target,glossary):
    if (file=='Naming.example.xml' and target.startswith('spice.')) or target in {'xe/xem/xyr','qe/qem/qyr','1-FF','0lam','vqvtl 3'} or '::' in target or re.search(r',(friend|hate|dislike),',target):return target
    if 'MIT License' in target or 'Brian Bucklew' in target:return target
    pattern=re.compile(r'(?<![A-Za-z])('+'|'.join(re.escape(k) for k in sorted(glossary,key=len,reverse=True))+r')(?![A-Za-z])')
    protected=re.compile(r'(=(?=[A-Za-z@])[A-Za-z@][^=]*=|\*[^*]+\*|@[^@]+@|\{\{[^|{}]+\||https?://[^\s)）]+|\b[^\s]+\.(?:xml|cs|csproj|txt|log)\b|~[A-Za-z][A-Za-z0-9_:/ .+-]*)')
    def rewrite(text):
        return ''.join(part if i%2 else pattern.sub(lambda m:glossary[m.group()],part) for i,part in enumerate(protected.split(text)))
    if file=='Options.example.xml' and re.search(r'^[-A-Za-z0-9.% ]+\|',target):
        return ','.join(a.split('|',1)[0]+'|'+rewrite(a.split('|',1)[1]) if '|' in a else a for a in target.split(','))
    result=rewrite(target)
    return result

def literal_unit_operations(target,units):
    changes=[]
    def replace(m):
        base,operation,word=m.groups()
        unit=units.get(word)
        if unit is None and re.search(r'[\u3400-\u9fff]',word):unit=word
        if unit is None:return m.group()
        replacement=unit if operation=='pluralize' else '='+base+'= '+unit
        changes.append({'removed_token':m.group(),'replacement':replacement,'operation':operation,'variable_base':base,'quantity_token_added':None if operation=='pluralize' else '='+base+'=','literal_unit':unit})
        return replacement
    result=re.sub(r'=([A-Za-z][^=\n:]*?)\.(pluralize|things):([^=:\n|]+)=',replace,target)
    return result,changes

def token_shape(token):
    # Selector arguments are display text; variable/operator heads are structural.
    body=token[1:-1]
    head=re.split(r'[:|]',body,maxsplit=1)[0].replace("'s",'')
    return head

def classify_tokens(source,target):
    a=collections.Counter(token_shape(t) for t in tokens(source).elements())
    b=collections.Counter(token_shape(t) for t in tokens(target).elements())
    if a==b:return 'same_variable_heads_translated_parameters_or_filters'
    return 'grammar_omission_or_structure_difference_needs_context_review'

def retained_type(row):
    s=row['translation'];f=row['file']
    if f=='Naming.example.xml':return 'procedural_naming_or_identifier'
    if re.search(r'^[-A-Za-z0-9.% ]+\|',s):return 'serialized_option_keys_not_visible_labels'
    if '::' in s or re.search(r',(friend|hate|dislike),',s):return 'serialized_faction_and_relationship_keys'
    if 'MIT License' in s or 'Brian Bucklew' in s:return 'credit_names_or_original_license_notice'
    if re.search(r'\b[Mm]k?\s+[IVX]+|\b(?:II|III|XVII-XXIV)\b',s):return 'model_designation_or_roman_number'
    if re.search(r'\.(?:xml|cs|csproj|txt|log)\b|https?://|\b(?:XML|CPU|LED|ASCII|ID|CP|MP|pt|ms)\b',s):return 'technical_name_path_unit_or_abbreviation'
    if re.search(r'\b(?:Alt|Shift|Enter|Space|Escape|ESC|PgUp|PgDown)\b|~Cmd|~UI|{{hotkey\|',s):return 'command_token_or_key_label'
    if '=@' in s or '@their@' in s or '*material*' in s:return 'runtime_placeholder_other_syntax'
    if f=='Books.example.xml':return 'calendar_notation_roman_number_or_machine_name'
    if f=='Naming.example.xml':return 'procedural_naming_or_identifier'
    if f in {'Creatures.example.xml','HiddenObjects.example.xml','Worlds.example.xml'} and s in {'xe/xem/xyr','qe/qem/qyr','1-FF','0lam','vqvtl 3'}:return 'pronoun_set_key_or_machine_identifier'
    if '~' in s or '{{W|[' in s or 'Tab' in s or "l'ook" in s:return 'command_token_or_key_label'
    if s.startswith('=') and not s.endswith('='):return 'partial_runtime_template_from_source'
    if 'support@' in s:return 'original_contact_address'
    if f=='Manual.example.xml':return 'command_token_or_key_label'
    if f=='Options.example.xml':return 'technical_name_path_unit_or_abbreviation'
    return 'proper_name_coinage_or_literal_needs_context_review'

def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--upstream',type=Path,default=DEFAULT); args=ap.parse_args()
    base=args.upstream/'ExampleLanguage'; cn=args.upstream/'333640/3746335636/languages/lang-CN'; tw=args.upstream/'333640/3777400827/zh-tw'
    convert=OpenCC('t2s').convert; manual=json.loads((ROOT/'data/manual-translations.json').read_text())
    overrides={(x['file'],x['path']):x for x in json.loads((ROOT/'data/manual-overrides.json').read_text())}
    glossary=json.loads((ROOT/'data/glossary-visible.json').read_text())
    units=json.loads((ROOT/'data/literal-units.json').read_text())
    repairs={(x['file'],x['path']):x for x in json.loads((ROOT/'data/template-repairs.json').read_text())}
    applied_repairs=set()
    unit_audit=[]
    documents=[]; bytext={}; cnid={}; twid={}; snapshots={}
    for path in sorted(base.glob('*.xml')):
        root=ET.parse(path).getroot(); sf,sn=fields(root)
        cp=cn/path.name.replace('example','CN'); tp=tw/path.name.replace('example','zh-tw')
        cf=fields(ET.parse(cp).getroot())[0] if cp.exists() else {}; tf=fields(ET.parse(tp).getroot())[0] if tp.exists() else {}
        documents.append((path,root,sf,sn,cf,tf))
        for p in (path,cp,tp):
            if p.exists(): snapshots[str(p.relative_to(args.upstream))]=hashlib.sha256(p.read_bytes()).hexdigest()
        for k,v in sf.items():
            if '▶' in v and k in cf and cf[k]!=plain(v):bytext.setdefault(plain(v).strip(),cf[k])
        for p,mp in ((cp,cnid),(tp,twid)):
            if p.exists():
                for e in ET.parse(p).iter('string'):mp.setdefault(e.get('ID'),e.get('Value',e.text or ''))
    audit=[]; unresolved=[]; mixed=[]; token_warnings=[]; counts=collections.Counter(); outdir=ROOT/'mod/languages/lang-CN'; outdir.mkdir(parents=True,exist_ok=True)
    for old in outdir.glob('*.xml'):old.unlink()
    for path,root,sf,sn,cf,tf in documents:
        chosen={}
        for k,source in sf.items():
            if '▶' not in source or not plain(source).strip():continue
            source=plain(source); short=source.strip(); current=cf.get(k)
            status='existing_cn'; translated=current
            # Retain existing translations except exact English fallback; mixed existing text is reported separately.
            if current is None or current==source or current.strip()==short:
                if short in manual:translated=manual[short];status='manual'
                elif source in cnid and cnid[source]!=source:translated=cnid[source];status='cn_id_fallback'
                elif short in bytext:translated=bytext[short];status='cn_text_reuse'
                elif k in tf and tf[k]!=source:translated=convert(tf[k]);status='tw_converted'
                elif source in twid and twid[source]!=source:translated=convert(twid[source]);status='tw_id_fallback'
                elif not latin(source):translated=source;status='template_or_symbol'
                elif short in {'xe/xem/xyr','qe/qem/qyr','1-FF','0lam','vqvtl 3','{{W|Alt}}','{{W|[Esc]}} {{y|=text=}}'} or short.startswith('=location.text|') or short in {'=newName|title','name|title'}:translated=current or source;status='identifier_or_key_label'
                elif path.name=='Naming.example.xml':translated=current or source;status='procedural_name_syllable'
                elif len(short)==1:translated=source;status='shortcut'
                else:translated=current or source;status='unresolved';unresolved.append({'file':path.name,'path':repr(k),'source':source})
            override=overrides.get((path.name,repr(k)))
            if override:
                if override['source']!=source or override['previous']!=translated:raise ValueError('Override baseline changed: '+path.name+' '+repr(k))
                translated=override['translation'];status='reviewed_override'
            expanded=translate_visible_glossary(path.name,source,translated,glossary)
            if expanded!=translated:
                translated=expanded
                if status=='existing_cn':status='reviewed_glossary'
            unit_baseline=translated
            translated,unit_changes=literal_unit_operations(translated,units)
            if unit_changes:
                unit_audit.append({'file':path.name,'path':repr(k),'source':source,'baseline_translation':unit_baseline,'translation':translated,'changes':unit_changes,'baseline_tokens':dict(tokens(unit_baseline)),'final_tokens':dict(tokens(translated))})
                if status=='existing_cn':status='reviewed_unit_literal'
            repair=repairs.get((path.name,repr(k)))
            if repair:
                if repair['source']!=source or translated not in {repair['before'],repair['after']}:raise ValueError('Template repair baseline changed: '+path.name+' '+repr(k))
                translated=repair['after'];status='reviewed_template_grammar';applied_repairs.add((path.name,repr(k)))
            if current is None or translated!=current:chosen[k]=translated
            if latin(translated):mixed.append({'file':path.name,'path':repr(k),'source':source,'translation':translated})
            if translated!=source and tokens(source)!=tokens(translated):token_warnings.append({'file':path.name,'status':status,'path':repr(k),'source':source,'translation':translated})
            counts[status]+=1;audit.append({'file':path.name,'path':repr(k),'status':status,'source':source,'translation':translated,'emitted':k in chosen})
        # A Replace collection must retain every current element, even unchanged siblings.
        replacement_roots=[p for p,e in sn.items() if e.get('Load')=='Replace' and any(key[0][:len(p)]==p for key in chosen)]
        for k,v in sf.items():
            if '▶' in v and plain(v).strip() and any(k[0][:len(p)]==p for p in replacement_roots):
                chosen.setdefault(k,cf.get(k,plain(v)))
        chosen_labels={repr(k) for k in chosen}
        for row in audit:
            if row["file"]==path.name and row["path"] in chosen_labels:row["emitted"]=True
        if not chosen:continue
        result=copy.deepcopy(root);rf,rn=fields(result)
        for k,v in sf.items():
            if '▶' not in v:continue
            node=rn[k[0]]
            if k in chosen:
                if k[1]=='#text':node.text=chosen[k]
                else:node.set(k[1],chosen[k])
            elif k[1]=='#text':node.text=None
            else:node.attrib.pop(k[1],None)
        emitted_nodes={id(rn[k[0]]) for k in chosen}
        def prune(e):
            for child in list(e):
                if not prune(child):e.remove(child)
            if e.text and ('▶' in e.text or not e.text.strip()):e.text=None
            e.tail=None
            return id(e) in emitted_nodes or bool(len(e))
        prune(result);result.set('Lang','CN');result.set('Encoding','utf-8')
        ET.indent(result,space='  ');ET.ElementTree(result).write(outdir/path.name.replace('.example.xml','.supplement.CN.xml'),encoding='utf-8',xml_declaration=True)
    if applied_repairs!=set(repairs):raise ValueError('Template repair field missing from export')
    data=ROOT/'data';dump(data/'audit-fields.json',audit);dump(data/'unresolved.json',unresolved);dump(data/'existing-mixed-latin.json',mixed);dump(data/'token-warnings.json',token_warnings);dump(data/'snapshot-sha256.json',snapshots)
    unit_lookup={(x['file'],x['path']):x for x in unit_audit}
    for row in token_warnings:
        unit_row=unit_lookup.get((row['file'],row['path']))
        if (row['file'],row['path']) in repairs:row['classification']='reviewed_exact_template_grammar'
        elif unit_row:row['classification']='reviewed_literal_unit_operation' if tokens(row['source'])==tokens(unit_row['baseline_translation']) else 'inherited_difference_plus_reviewed_literal_unit_operation'
        else:row['classification']=classify_tokens(row['source'],row['translation'])
    for row in mixed:row['retained_type']=retained_type(row)
    dump(data/'token-warnings.json',token_warnings);dump(data/'existing-mixed-latin.json',mixed)
    dump(data/'review-classification.json',{'token_differences':dict(collections.Counter(x['classification'] for x in token_warnings)),'retained_latin':dict(collections.Counter(x['retained_type'] for x in mixed)),'note':'Classifier documents a review queue; it does not certify semantic correctness or prove every remaining Latin fragment is required.'})
    dump(data/'unit-operation-audit.json',{'runtime_evidence':'Actual game Grammar.Pluralize("打兰") returns "打兰s". Single noun pluralize operations are rendered as literal Chinese units; things retains its numeric variable.','entries':unit_audit})
    unit_index={(x['file'],x['path']):x for x in unit_audit}
    new_differences=[];checked_new=0
    for row in audit:
        if row['status'] not in {'manual','tw_converted','cn_text_reuse','cn_id_fallback','template_or_symbol','identifier_or_key_label','procedural_name_syllable'}:continue
        checked_new+=1;a=tokens(row['source']);b=tokens(row['translation'])
        if a==b:continue
        change=unit_index.get((row['file'],row['path']))
        baseline=tokens(change['baseline_translation']) if change else b
        new_differences.append({'file':row['file'],'path':row['path'],'status':row['status'],'exact_source_tokens':dict(a),'exact_translation_tokens':dict(b),'approved_exact_unit_operation_only':a==baseline,'runtime_confirmation_required':False})
    dump(data/'new-translation-token-audit.json',{'checked_fields':checked_new,'difference_fields':len(new_differences),'unapproved_difference_fields':sum(not x['approved_exact_unit_operation_only'] for x in new_differences),'differences':new_differences})
    dump(data/'selector-parameter-allowlist.json',{'scope':'Retired: engine appends s to Chinese single-argument noun pluralization. No selector substitutions are allowed by this file; see unit-operation-audit.json for exact literal-operation replacements.','entries':[]})
    summary={'scope':'Nonempty ▶-marked fields in official ExampleLanguage XML 2.0.212.31; excludes runtime C#, historyspice JSON, procedural syllable semantics, translations already wrong/mixed and strings absent from the official export. Coverage is field availability, not full-game translation quality.','mode':'Incremental XML with Lang=CN; requires original CN pack and later load order.','total_source_fields':len(audit),'statuses':dict(counts),'emitted_fields':sum(x['emitted'] for x in audit),'unresolved_fields':len(unresolved),'existing_mixed_latin_fields':len(mixed),'residual_latin_fields_all_final_values':len(mixed),'residual_latin_scope':'Includes all final existing, reused, converted and manual values; residual does not mean untranslated prose.','placeholder_warning_fields':len(token_warnings),'xml_files':len(list(outdir.glob('*.xml'))),'template_grammar_repaired_fields':len(applied_repairs),'literal_unit_operation_fields':len(unit_audit),'collection_policy':'Load=Replace collections include unchanged existing CN siblings to preserve the entire collection.'}
    dump(data/'coverage-summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
