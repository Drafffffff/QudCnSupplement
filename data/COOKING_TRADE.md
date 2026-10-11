# 0.1.3：烹饪与交易

## 原因与修复

实际截图中，随机烹饪消息在杏子、一根草、大刺叶前保留 `a`。实际程序集 `Campfire.DescribeMeal` (0x0600ba36) 将 `RollIngredients` 结果传入 `spice:cooking.cookTemplate`；`cooking.ingredient` 的食材及形容词分支使用 `|article`。`PostProcessors.Article` 的原生 IL 读取 Context.Value，Clear 后调用 Grammar.A，因此已经中文化的随机语料重新获得英文不定冠词。

仅在中文模式且展开值以中文（支持颜色标记）开头时，跳过该英文冠词后处理。英文食材保持 an apple；英文模式不应用补充。没有全局删除字母 A，也没有改物品或存档元数据。原始 HistorySpice token/数组/权重完全保留。

## 交易

原截图确认框显示“10 打兰淡水”，交易总价显示“11.43 德拉姆”。两者均指 dram。显示层在数字容量上下文统一为德拉姆；完整单位标签也统一。保留玩家名或其他非单位名称（例“打兰花”）。物品数量、买卖价格、实际支付与舍入逻辑不改。

分类 Food / Meds / Books / Energy Cells / Resources / Melee Weapons / Water Containers 等添加完整标签映射，支持折叠符号、颜色、重量；化学电池的 (Full)/(Empty) 显示充满/空。

## 祝语

对官方原文含 Live and drink 且旧译含“生而饮水”的 413 个字段改为“长存，畅饮”，变量不变。区别于 Live and drink piss、in peace、together 等有意变体，不用统一祝语抹平上下文。原本已中文但本包未覆盖的字段现在进入补充 XML；独立中文 Markov 语料随输入重建。

## 验证与边界

隔离真实引擎检查 12 种烹饪模板，每种 25 次；截图中的三种食材和同一 cookTemplate/andList 路径再次检查。含英文守卫、颜色、单位、分类与电池状态共 318 项。HUD 109 项、原有语法 12 项、动词 25 项、书籍 17 组及 10,211 个字符串查询继续回归；离线 37 项通过。实测结果见 analysis/cooking-runtime.log 和 analysis/cooking-tests.log。

测试没有消耗用户角色的食材、水或回合，也没有替用户确认交易；已有日志不回溯改写。完整剧情/全部随机组合覆盖仍未证明。

## Steam 新截图（保存时间 2026-10-11 23:54—23:56）

三张原图保存在 analysis/steam-screenshots。确认新增漏译：human friend、[sitting]、[lying on a 床]、Sultan Histories、14th 日。

- FormalAddressTerm 模板委托完整称呼 human friend 译为“人类朋友”；克隆独立 Gender provider 实测，不写共享代词或对象属性。
- 原先效果钩子只枚举子类声明的方法，漏掉 Sitting 继承的 Effect.GetDescription；现补上基类及 GetStateDescription。Prone/Sitting 的人物名称标签还直接调用 GetDisplayNameEvent.AddTag，单独在该语义出口处理完整姿态标签，颜色与床名保留。
- 日志通知仅在“你在日志的 … 区段中记下这项资讯”的完整上下文修复 Sultan Histories → 苏丹历史；其他同名文本不替换。
- 日期显示仅去除数字后、中文“日”前的 st/nd/rd/th，不改变日数。

Steam 专项实机检查 17 项，覆盖实际 Effect 方法、实际 AddTag/DescriptionBuilder、真实 FormalAddressTerm 模板、颜色日志通知、序数日期和英文守卫。未将测试角色放入世界，Prone 无有效世界床时原生输出“俯卧”；床上标签另经真实 AddTag 路径验证。
