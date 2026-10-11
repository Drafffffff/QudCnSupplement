# 程序书籍标题调查与修复（2.0.212.31）

`The Orator Domineers the West` 不是官方导出的静态书名字段。它可由独立的英文 Markov 语料生成：将原始家具描述翻译成中文，并不会改变已经编译在 `LibraryCorpus.json` 里的英文链。已新增独立中文链 `mod/LibraryCorpus.CN.json`；运行时须在 CN 语言下选择这个文件，不能无条件覆盖原版 `LibraryCorpus.json`。

## 可核查证据

复用 REA 保存证据 `analysis/private/rea-evidence.json` 的 `records[0].normalized_result`，证据 ID：`ev_0345e15d31fbc53b3d628bbea1cd4ae418c8277b5ababf7cabe01d3bc5096c3b`。目标 `Assembly-CSharp.dll` SHA-256：`a348819a26f57beaaebbeca17957a0393026e69859c07f38036dc4fbab6491d8`，MVID：`668db015-786e-4762-9f3d-15df5ef2856d`。下列 token 仅适用于这个构建。

- `sources/ExampleLanguage/Furniture.example.xml:1340`，`statue of wizard / Description.Short`，含原句 `Dagon the orator domineers the west apse with his brazen pose.`。现有 CN 翻译已是“演说家达贡以傲慢姿态统御西侧半圆室。他的金冠在火光中灿烂闪耀。”，并非此 XML 字段漏译。
- 对 Bazzite 运行目录进行了只读 SSH 查询，没有退出游戏或写入存档。原版 `CoQ_Data/StreamingAssets/Base/LibraryCorpus.json.raw.txt` 第 604925 字符附近含同一句。`LibraryCorpus.json` SHA-256：`b710154e74d1c234a70e86ecad602b603e2222537539cab4956f1f55ca375a4d`；`order=2`，5658 起句，84006 键和值。
- 原链的实际转移：`the orator → domineers`，`orator domineers → the`，`domineers the → west`，`the west → that / was / apse`。书名与语料片段吻合；没有从存档提取这件书的种子，因此没有声称重现了该对象的同一次随机生成。
- `XRL.World.Parts.MarkovBook.SetContents`，`0x06009460`：IL 2/9 写入 `BookSeed`/`BookCorpus`；IL 15 调用 `EnsureCorpusLoaded`；IL 55 调用 `MarkovChain.GenerateTitle`；IL 60 写入 `Title`；IL 324–340 把 `Title` 写入 `ParentObject.Render.DisplayName`。标题主体没有静态字符串翻译调用。仅卷号、无删节版、版次的包装调用 `_T`。
- `MarkovChain.GenerateTitle`，`0x060035ba`：随机选链状态，调用 `GenerateFragment`，去除不合适首尾词，再执行英文式标题大小写。`GenerateFragment`，`0x060035bb`，用 ASCII 空格推进两词状态、用 ASCII `.` 检查结束。
- `MarkovBook.EnsureCorpusLoaded`，`0x0600945e`：按文件名查询静态 `CorpusData` 字典，未缓存时通过 `DataManager.FilePathFromBasePreferModFile` 加载文件，再 `PostprocessLoadedCorpus`。
- `MarkovChainData.LoadFromFile`，`0x060035b2`：mod 优先路径 → `ReadAllText` → JSON 反序列化 → `OnAfterDeserialize`。后者 `0x060035ad` 校验键值数量相等，将各 `values` 按 U+0001 拆成后继词列表。
- `ObjectBlueprints/Items.xml` 的 `MarkovBook.BookCorpus` 和 `StandaloneMarkovBook.Chain` 都指向 `LibraryCorpus.json`；`PopulationTables.xml` 也把它作为书架种群选项。仅改 `StandaloneMarkovBook` 无法覆盖所有生成入口。
- 另发现 `SetContents` 无删节版分支 IL 212–227 在本地化包装后额外拼接硬编码 `: Unabridged`。这是 C# 路径问题，中文语料文件不能自行消除它。

## 新增中文语料

生成器 `tools/build_markov.py` 从 `data/audit-fields.json` 读取已最终审阅的译文，仅选择 `Books.page` 和物品、家具、生物的 `Description.Short`。不用英词逐项替换、不把整段中文塞成单个“词”，也不改变任何英文通用显示文字。

分词使用固定版本 `jieba==0.42.1`，`HMM=False`，超长未知词最长 8 字。起句和链状态保留两词结构；每个词之间用一个 ASCII 空格，末词附 `.`，与真实引擎的状态推进和结束检查一致。中文标点先规范成引擎识别的形式，运行时显示层可以仅针对这类中文生成文本恢复“。”和去掉中文词间空格；不能在链里提前删空格。

任何含动态模板或未处理拉丁字母的句子整句跳过并记录，不给其变量提供虚构的替代内容。排除句不是中文语料的“漏译”，因为此文件是从已译散文重新训练的替代生成源，并非对英文全词链一一映射。公开领域英语摘录不会被假称已逐段翻译。

当前生成量：4419 个中文起句，29384 个两词状态，51710 个词；排除动态模板 586 句、残留拉丁字母/标识符 267 句、过短 653 句、无中文散文 95 句。确切贡献字段、分词词典及输入/输出 SHA-256 见 `data/markov-audit.json`。

复现：

```sh
.venv/bin/python -m pip install -r requirements-markov.txt
.venv/bin/python tools/build_corpus.py
.venv/bin/python tools/build_markov.py
.venv/bin/python -m unittest discover -s tests -v
```

生成 JSON 仅含引擎所需四项：`order`、`OpeningWords`、`keys`、`values`。`keys` 与 `values` 严格一一对应，`values` 使用 U+0001 序列化后继词，允许重复后继词以保留训练频率。新增 `tests/test_markov.py` 检查 JSON 结构、纯中文词表、词长、终止转移、源/产物哈希和重建一致性。100 个固定种子的参考链采样均在 100 步内结束；这项检查不替代真实引擎测试。

## 旧存档及覆盖边界

`BookSeed`、`BookCorpus` 和 `Title` 是普通实例字段，`Pages`、`Sentence` 和静态 `CorpusData` 标记不序列化；`SetContents` 明确把生成标题写入对象的 `Render.DisplayName`。因此更换语料不是对已有对象显示名进行翻译的操作。截图里的对象是否在安装补充包前生成，尚未通过只读对象检查确认；不能仅凭截图断言是旧存档。

对已经固化的标题，目前提供 `data/procedural-title-overrides.json`，只包含用户实际观察到的整名 `The Orator Domineers the West → 演说家统御西方`，要求仅在 MarkovBook 的显示上下文应用。它不修改存档，不猜测其他随机英文书名，也不把名字退化成泛称“书籍”。所有未知旧书名需要上下文精确翻译或明确的迁移策略。

中文链启用后，新生成的程序书名与正文可使用中文训练词表；具体自然程度仍属于随机拼接文本质量，不能声称它们是原英语生成结果的逐句等价翻译。原先官方 25090 XML 字段完整覆盖结论只属于导出字段范围，不能推出全游戏程序名、编译语料、旧存档文本均已 100% 汉化。

真实引擎 2.0.212.31 已验证 100 个标题、100 个句子、100 个段落均无英文；100 次 SetContents 保存语料名与种子不变。英文同随机种子输出、原图指纹及其他语料保持原样。旧已知书名 CN/EN 与非 MarkovBook 上下文守卫通过，复杂地标 3/3 完整保留。

额外以隔离 QA 临时、不保存的 XRLCore/XRLGame 提供坐标，执行真实 RuinOfHouseIsnerLore 200 次及原 PostprocessLoadedCorpus；46 条线索成功翻译且从现有起句“传说 中”可达，英文图不变。全部 17 组检查通过，finally 恢复测试前 Core/Game；该探针不安装到正常配置。完整日志见 analysis/hover-runtime.log。这些采样不代表全部随机文本的自然程度已经逐句审阅。

## 运行时桥接及秘密线索保留

`mod/QudCnBooks.cs` 的 `Install(Harmony)` 返回成功安装的钩子数量。仅通过对象身份识别默认英文链，CN 下在 `GenerateTitle`、`GenerateSentence`、`GenerateParagraph` 的参数位置换成独立中文链；英文链与 `MarkovBook.CorpusData` 不变，也不改保存用的 `BookCorpus`/`BookSeed`。`GenerateFragment` 内部不做显示整理。生成完成后才去分词空格及复原中文标点。

原 `PostprocessLoadedCorpus` 还承担游戏功能：当前世界存在 `RuinofHouseIsner_xCoordinate` 与 `_yCoordinate` 两坐标时，以 `HouseIsnerLore` 重置随机种子，46 次调用 `LoreGenerator.RuinOfHouseIsnerLore(x,y)`（`0x060035a7`），再调用 `MarkovChain.AppendSecret`（`0x060035b6`）。因此不能为获得纯中文结果而跳过原后处理。

桥接在坐标生成后延迟对独立中文链调用一次原后处理。`AppendSecret` 钩子只对这个中文链启用，用精确的原版语法匹配七种物品名、四种前置短语、六类线索句式（含不足一帕拉桑分支）。实际随机选择的方位、距离、地标名均保留；未知版本的句式原样保留并记录 `BOOK_ISNER_UNMATCHED`，不凭词替换猜测。新世界使用新的中文链，避免带入前一世界的坐标秘密。

原 `AppendSecret` 的花括号秘密分组和两词前缀协议保留；完整秘密作为受保护文本进入链。显示整理前临时保护捕获到的真实地标，整理后恢复其原字节，故 `Hope-in-Motion`、`Red Rock`、`Site 3.2` 不会失去空格、连字符或小数点。纯中文语料的测试和进入世界后的动态地标保留应分别统计；后者不能以“出现拉丁字母”为由删除游戏线索。

旧标题的精确显示补译只作用于确实有 `MarkovBook` 部件且 `Title` 与已观察整名一致的对象，CN 下修改返回的显示字符串；英文模式和非 MarkovBook 对象保持原名。新 `SetContents` 的后处理只清理中文生成标题被原版附加的硬编码 `: Unabridged`。没有针对其他未知英文旧标题进行泛化替换。

`tools/build_book_probe.py` 生成隔离 QA Mod 的 `BookProbe.cs`，检查 100 个真实引擎标题、句子、段落及长度；英文同种子结果、原链指纹、其他语料、旧标题上下文、元数据、真实 lore 生成与 46 条秘密注入。它只应装入隔离测试目录，不能作为正式补丁发给正常存档。若隔离测试尚无世界，探针临时构造不保存的世界对象供原版线索函数读取坐标，并在 finally 恢复全局对象、丢弃测试中文链。运行结果由主任务保存；此段说明不代表尚未收到的实机结果已通过。

首轮真实引擎已确认：100/100 中文标题、100/100 句子、100/100 段落通过；英文同种子、原图不变、自建其他英文链、100 次保存元数据以及三个复杂地标保留通过。首轮暴露的旧名显示属性路径已根据 REA 补齐：`GameObject.get_DisplayName`（`0x06005eb6`）直接调用 `GetDisplayNameEvent.GetFor`，不经过已有的两个 `GetDisplayName` 重载，因此单独增加相同的精确书籍上下文钩子。秘密注入探针也已补充标题界面无 Core 时的临时隔离 Core（finally 恢复）；原 Core 构造方法 69 字节，仅初始化普通字段/集合，没有保存或加载世界操作。修复后的这两项等待下一轮真实引擎结果。

中文秘密的两词连接头统一采用已有的 `传说 中`。它同时存在于训练链和起句列表，可生成“传说中伊斯纳家族之毁，……”；不使用训练链里不存在的“关于 传说中的”等孤立连接头。探针额外要求实际注入后 `传说 中` 的后继包含至少 46 条完整线索，且仍可从起句进入，避免“加入了字典，但正文无法抽到”的虚假功能保留。
