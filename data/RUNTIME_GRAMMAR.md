# 模板运行时语法

`QudCnGrammar` 只处理模板显示委托，不改变对象姓名、身体部位存储或底层英文语法工具。

- 身体部位：在 BodyPartReplacers.OrdinalName 与 GameObjectReplacers.BodyPartOrdinalName 输出端匹配完整部位及已知方位／序数；未知自定义名称保留。
- 列表：ListReplacers/对应液体列表委托进入时建立线程局部作用域，退出或异常时恢复。在此作用域内构造中文连接符，同时完整保留每个列表元素，包括名称内的 `and`；外部调用原生 Grammar 函数不受影响。string 列表 either.or 直接写入已连接的显示内容。
- 冠词：只在对象命名显示委托中移除紧邻中文名称的 a/an/the 前缀；专有名称受 HasProperName 守卫保护。
- 代词：GameObjectReplacers 与 GenderedNounReplacers 的五种模板输出按主格／宾格／所有格／反身代词翻译。底层 PronounProvider 不改动。

精确测试结果见 `analysis/hover-runtime.log`。尚未识别的第三方自定义部位、动态动词及对象名称不会被猜测替换；模板钩子存在也不等于任意组合的语义正确性已获证明。

## 0.1.2 最终补充

中文复数在 TextBuilder 的已知 Pluralize 委托作用域内保持原样，作用域外原生 Grammar.Pluralize 不变；隔离实机语法检查 12/12。动态 Does/Verb 捕获实际参数（含 Context.Default 回退），对 68 种已核对动词执行完整尾词翻译，保留主语姓名与颜色。证据见 runtime-verbs.json；未知自定义动词保留并有界记录，不能据此声称任意第三方模组也完全汉化。
