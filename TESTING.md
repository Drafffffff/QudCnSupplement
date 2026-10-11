# Bazzite 实机验证记录

## 0.1.2：2026-10-11

目标是实际安装的 Caves of Qud 2.0.212.31 lang-experimental，与创意工坊 QudSimplifiedChinese 0.1.0 共同加载。补充 Mod 依赖原包并在其后加载。

隔离实例使用官方 Steam Linux Runtime 和原生游戏，独立设置、Mods、存档路径。`analysis/hover-build.log` 记录 7 个正式 C# 文件和 4 个隔离 QA 文件均编译成功，无正式包编译警告。`analysis/hover-runtime.log` 记录：

- 10,211/10,211 次实际 Strings._S 查询匹配，差异 0。
- 178 个运行时钩子初始化；自检 27/27、代词 8/8、诊断 8/8、模板组合 36/36。
- 原截图涉及的 begin、stop、your freezing effect、emit/hands、miss、take the 消息通过实际 MessageQueue 输出中文。
- 81 个 HUD 标签、11 个实际 TooltipManager 悬停提示及中英文切换，共 95/95。截图 `analysis/hover-after.png` 显示真实渲染的“自动探索”悬停提示。
- 名称冠词、代词、身体部位、列表、复数作用域与英文守卫 12/12。
- 动态 Does/Verb 参数、姓名颜色保留、未知词保留与英文守卫 25/25。最终再次发现并修复 Does 产生的 “The 门”；动词探针现同时检查冠词。
- 中文随机书名、句子、段落各 100 次；SetContents 元数据保持 100 次；英文原链、自定义链、旧书名显示、地名保护、200 次实际伊斯纳线索翻译及 46 条线索注入和可达性，共 17 组通过。
- 书籍 QA 在无世界时构造测试对象会产生原生 ApplyModification NullReference 日志；其后所有断言通过。正式配置启动没有加载这些测试对象或 QA 模组。

离线 37 项测试全部通过（`analysis/hover-tests.log`）。25,090 个官方 XML 导出字段有译值，缺失 0；本包输出 5,993 个字段，精确修复 736 字段的 815 处语法操作。历史语料保留结构、数组和权重。字段有值并不代表全部译文语义正确。

正式安装日志为 `analysis/hover-install.log`；安装后再次用正常配置启动，保留原创意工坊包。正常存档的前后哈希见 `analysis/hover-saves-before.json` 和 `analysis/hover-saves-after.json`，启动与文件校验结果见 `analysis/hover-installed-verification.json`。没有进入、推进原角色；QA 探针没有安装到正式配置。

## 尚未证明的边界

未遍历所有任务、菜单、战斗、程序生成组合和旧存档对象。未知历史随机英文书名、自定义动词、第三方 Mod 及未来版本不保证全覆盖；游戏内部标识符、按键、作者署名等保留。不能据此声称全游戏任意状态 100% 无英文或 100% 语义正确。

## 早期 0.1.0 记录


时间：2026-10-11，目标：Caves of Qud 2.0.212.31，lang-experimental。原简中包 QudSimplifiedChinese 0.1.0。

## 隔离的真实游戏引擎

使用官方 Steam Linux Runtime 启动同一份原生 Linux 游戏。测试存档、设置、Mods 路径在 `~/qud-cn-supplement-test/`，与正常配置隔离。不是只运行 Python 字符串替换模拟。

最终 `analysis/runtime-final.log`：

- 游戏编译补充包 2 个 C# 文件及测试探针成功。
- 实际加载顺序：原简中包、补充包、测试探针。
- 10,211 个真实 `Strings._S` 查询全部匹配，差异 0。
- 动态初始化自检：20/20；消息模板组合：36/36；诊断过滤：8/8。
- 103 个运行时钩子安装；最终无 HOOK_ERROR。
- 实际 `MessageQueue.Add` 输出中文击中伤害和装备消息，颜色保留。
- 切换英文后动态消息保持英文，English guard=True，再恢复 CN。
- HistorySpice 实际合并后的玻璃、骰子与控制地址 3/3 匹配。
- 用独立随机源实际展开 `=spice:elements.glass.materials.!random=`，得到“玻璃”。
- 引擎原始 `Grammar.Pluralize("打兰")` 返回“打兰s”，此行是故障对照。补充包已将 113 字段的 117 个名词单位操作改为中文固定量词；things 操作保留数量变量。

## 正式配置安装与启动

目标目录：`~/.config/unity3d/Freehold Games/CavesOfQud/Mods/QudCnSupplement/`。

安装后 32 个文件哈希全部匹配；设置仅增加 `OptionAllowCSMods: Yes`。原设置备份路径记录于 `analysis/install.json`。测试探针没有安装到正式配置。

正常配置实机再次编译成功，加载顺序为 QudSimplifiedChinese → QudCnSupplement。日志 `analysis/installed-build.log`、`analysis/installed-player.log`，自检仍全部通过，初始化语言 CN。主菜单截图 `analysis/installed-main-menu.png` 已目视检查中文渲染。

安装前后正常 Saves 目录的 3 个文件 SHA-256 完全一致，详见 `analysis/saves-before-install.json`、`analysis/saves-after-install.json`。没有加载、推进或修改原角色。游戏留在正常配置的主菜单。

## 静态与离线验证

项目 Python 测试 17 项全部通过，日志 `analysis/unit-tests.log`。官方导出字段 25,090，缺失 0；历史叶键 1,574、字符串 5,858，结构、权重、数组长度与占位符审计通过。译文单位的语法操作差异由逐字段精确审计验证，不对任意 token 差异豁免。

## 测试边界

这次完成真实编译、真实字符串加载、真实消息队列和实际历史文本展开，并检查正式启动界面；没有进行完整流程通关或遍历所有菜单、任务、战斗和程序生成组合。不能将这些测试宣称为全游戏 100% 汉化、100% 语义正确或所有场景无排版问题。保留技术标识符、按键及原作者署名。其他 Mod 与未来游戏版本不在本次验证范围。
