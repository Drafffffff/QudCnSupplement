# 0.1.1 动态英文残留调查

用户实机截图：`analysis/article-before.png`。完整句子为“你经过了 a 铁门。”及“道路被 a 熟铁栅栏 挡住了。”。

本次运行的 Player.log 还实际记录：

```text
{{r|你 miss 使用 你的 {{w|青铜}}匕首 未命中！}} [2 对 5]
你 take the 皮甲。
```

## 根因

1. 静态译文保留英文语法型占位符。`Combat Player Miss Message (with weapon)` 使用 `=subject.Does:miss=`；`Inventory take` 使用 `=subject.Does:take=` 与 `=object.the.name=`；阻挡提示使用 `=object.a.name=`，经过提示使用上游生成的 `=passed.andList=`。字段有中文值不能证明这些变量展开后完全中文。
2. 已安装 Assembly-CSharp.dll 的 CIL 显示，GameObject.Does 调用 GetVerb 拼接主语和动词，GetVerb 调用英文 Grammar.ThirdPerson；GameObjectReplacers.Subjective/Possessive 向 IPronounProvider 取代词值。不是仅靠翻译 XML 的字面正文就能覆盖的内容。证据来自 REA 对当前 DLL 的静态读取，SHA 见 build-target.json；实际探针进一步确认 female provider 原始值 she，渲染后可独立翻译。
3. 0.1.0 TranslateMessage 的提前返回只检查 `[A-Za-z]{3,}`，所以 a/an 不能进入消息规则。即使进入规则，也需要整句匹配；原规则缺少当前版本的“你 take…”和“你 miss 使用…”句式。
4. 战斗句子外层有颜色框，骰点位于框外；原 Outer 只支持整个字符串均在颜色框内，导致含嵌套物品颜色及框外骰点的整句不能被识别。

最终译文审计中 Does/does 语法操作出现504次，verb出现144次，subjective出现129次（是token出现次数，并非独立故障数）。这说明问题涉及生成层。前一版的字段覆盖统计只证明有值，动态测试没有覆盖足够的实际句式。

## 修复

- 提前筛选兼顾短冠词；只对已知完整消息框架做清理，未匹配姓名保持原样。
- 添加经过、阻挡、拿取和玩家未命中消息规则。
- 识别“颜色框 + 框外骰点”，递归处理框内句子，保留颜色和骰点。
- 仅在 CN 时，对 GameObjectReplacers 的 Subjective、Objective、Possessive、SubstantivePossessive、Reflexive 这5个模板渲染函数做精确标准代词转换。her在宾格输出她，在所有格输出她的；保留未知自定义代词。不修改 IPronounProvider，不注册全局变量覆盖，不对姓名或全部显示文本做删词。
- 诊断日志纳入短冠词，以免 a/an 不进入审阅队列。

## 验证

Python20测试全通过；实机 selftest27/27，pronouns8/8，diagnostics8/8，matrix36/36，实际字符串查询10211/10211。

真实 MessageQueue.Add 输出：经过铁门、被熟铁栅栏挡住、拿取皮甲、使用青铜匕首未命中，均为中文，颜色和骰点保留。真实模板函数调用4/4：CN主格她、CN所有格她的、原始对象provider仍she、英文语言渲染仍she。不是把 she 在任意文本里全局替换。

正式配置再次编译成功，108 hooks、211 patterns；正常存档哈希安装前后保持一致。日志见 `analysis/article-runtime.log`、`analysis/article-installed-player.log`；旧消息不会追溯写回存档。本次无法证明所有未遇到的动态英文动词都已覆盖，未知原包语法与自定义代词仍保留以供审阅。
