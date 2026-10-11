# 中文模板语法审计

修复 736 个完全匹配字段、815 处模板 token。所有其他 token 均按出现次数检查完整保留；修复前后颜色标记、对象与数值引用不改动。逐条原文、译文与 token 差异见 `template-repairs.json`。

## 接入

在 `build_corpus.py` 的 `literal_unit_operations` 之后、`chosen` 和 `audit.append` 之前，以 `(path.name, repr(k))` 查询修复。必须校验 `translated == repair["before"]`，再使用 `repair["after"]`；不匹配应报告或失败，切勿猜测替换。已经是 `after` 可直接跳过。执行 `tools/build_template_repairs.py` 可重建并自测；`template-grammar-baseline.json` 保存稳定修复前快照；已修复的 audit 不会导致第二次生成丢失修复。

## 原生语义

原生 `GameObject.does` (0x06005ced) 与 `Does` (0x06005cee) 都输出主语加动词，仅代词大小写有差异。修复保留显式 `.it`/`.It` 代词；常规 Does/does 使用对应 The/the.name，保留已确认的姓名选项；verb 仅替换动词，不增添主语。动态 `Does#verb`、未确认参数和多义词均保留人工审阅。原生姓名生成仍由引擎负责，玩家姓名与生成地名不会被全局替换。

## 审阅边界

剩余操作计数：`{'The': 439, 'a': 120, 'the': 441, 'andList': 132, 'pluralize': 16, 'orList': 9, 'things': 3, 'ifPlural': 6, 'A': 8, 'ordinalName': 44, 'Does': 19, 'verb': 1}`。剩余类型：`{'name_format': 1006, 'list_join': 141, 'localized_branch': 7, 'body_part_ordinal': 44, 'dynamic_noun_plural': 17, 'dynamic_verb': 20}`。完整文件/字段/token/上下文见 `template-grammar-audit.json` 的 remaining。andList/orList、ordinalName 需类型感知运行时语义钩子；a/the 可能承载名称格式选项，保留原生调用。pluralize 无文字参数常为对象名复数化，不能替换对象名称。非英语分支本身没有汉化缺口。字面静态动词、明确英文单位及两种 Doesly/itDoes 变体已按原文和上下文审阅修订；余下20处动态动词由调用处注入，需运行时词典翻译。andList/orList、名称格式、序数和动态名词需由对应引擎语义钩子完成，不能把静态审计误称为全游戏100%语义覆盖。

## 自测

6 个主语/代词/verb-only/单位/动态动词保留/嵌套颜色用例通过；736 个字段 token 不变量与幂等性检查通过。

## 运行时后续验证

上述保留操作已由类型感知 QudCnGrammar/QudCnRuntimeVerbs 接续：真实引擎语法 12/12，动态动词 25/25，覆盖实际参数 Default 回退及 Does 生成的冠词。仍保留未知第三方名称与动词，详见 RUNTIME_GRAMMAR.md、runtime-verbs.json 和 TESTING.md。
