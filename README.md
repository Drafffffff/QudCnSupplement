# Caves of Qud 简体中文补充 Mod

当前补充包版本 **0.1.3**。针对 Bazzite 上的 **2.0.212.31 / lang-experimental**，依赖创意工坊简中补丁 **3746335636 / QudSimplifiedChinese**。本项目是独立本地 Mod，不覆盖创意工坊文件；加载顺序为原简中包 → QudCnSupplement。

## 覆盖范围与限制

目标是补齐当前版本的简体中文。官方 ExampleLanguage 导出中 25,090 个非空可本地化字段均有最终值，缺失字段为 0；这是**导出字段覆盖率 100%**，不能等同于“整个游戏任何情况下都没有英文”。游戏中的硬编码、程序生成组合、其他 Mod 和未来更新无法由这一指标证明。

补充包写出 28 个 XML、5,993 个字段；另有 HistorySpice 历史生成文本、精确界面映射、受限的动态消息模板和状态描述。保留变量、控制地址、颜色、数字和角色名称。技术标识符、按键、型号及原作者署名可保留拉丁字符。遗留译文仍可能存在语义和文风问题。

动态补丁仅在语言为 CN 时运行，不对全局文本做逐词替换。未识别的英文输出会写入有数量上限的审阅日志，以便后续增补。游戏更新后应重新生成并测试，安装脚本会拒绝不匹配的游戏或原包版本。

## 安装与卸载

已通过 SSH 在 Bazzite 安装。手动安装时把 `mod/` 内的文件放入以下独立文件夹，并保留原创意工坊简中补丁，启用脚本 Mod，重启游戏：

```text
~/.config/unity3d/Freehold Games/CavesOfQud/Mods/QudCnSupplement/
```

自动安装先保存并退出游戏，再运行：

```sh
python3 tools/install_remote.py --host bazzite
```

脚本校验目标版本及每个文件，备份 PlayerOptions.json，并启用 OptionAllowCSMods。安装记录和备份保存在游戏配置目录的 `cn-supplement-install.json`、`cn-supplement-backups/`。不修改存档。

卸载时先退出游戏：

```sh
python3 tools/install_remote.py --host bazzite --uninstall
```

卸载只删除此补充包，并恢复安装前的脚本开关；保留期间其他设置变更。发现文件被用户修改时会停止自动卸载，避免删掉新增工作。不要取消订阅原简中补丁。

## 重现构建

项目内 `sources/` 固定当前官方语言导出和上游资源，`data/` 保存逐字段审计、输入哈希、术语与人工修订。Python 3：

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/build_template_repairs.py
.venv/bin/python tools/build_corpus.py
.venv/bin/python tools/build_dynamic.py
.venv/bin/python tools/build_history.py
.venv/bin/python tools/build_hud.py
.venv/bin/python tools/build_markov.py
.venv/bin/python -m unittest discover -s tests -v
```

`tools/build_probe.py` 生成只用于隔离测试的探针，不随正式 Mod 安装。`tools/remote_test.py` 使用 Bazzite 的官方 Steam Linux Runtime，在独立存档与设置目录启动真实游戏；远端测试目录需预先放入原包与补充包。真实游戏编译和测试结果见 `analysis/` 及 `TESTING.md`。

## 来源

简中：Mao Shengzi 的 QudSimplifiedChinese。繁中与动态翻译参考：AosakiReiya（见 THIRD_PARTY_NOTICES.md）。部分译文由繁中转简体，再结合当前版本修订。原游戏资源属于 Freehold Games。本地补充不表示获得上游再许可，未上传或发布创意工坊。

## 0.1.1 动态语法修复

针对实机发现的冠词、拿取和未命中混合文本，修复短词筛选和颜色框外骰点后缀；在模板渲染专用的代词函数上区分主格、宾格、所有格及反身代词，不改游戏对象的代词数据或姓名。见 `data/DYNAMIC_GRAMMAR.md`。历史消息已存下的文本不追溯重写，新消息使用新规则。

## 0.1.2 悬停、模板与程序书籍

修正 736 个源字段的 815 处语法问题，覆盖确定的英文动词、数量分支及所有格；改动逐字段校验源文和变量。界面增加 81 个完整标签映射，并接入真实 TooltipManager 与 UITextSkin 渲染流程。模板列表使用中文连接词，身体部位与代词在类型专用显示出口处理；原始姓名、部位及代词数据不变。

程序书籍在 CN 下使用独立中文 Markov 链。原英文图、保存的语料名和种子保持原样；标题及正文为中文语料随机生成，并非原随机英语文本的逐句对译。保留 Isner 藏宝线索、真实方位／距离／地标，检查其从起句可达。已观察的旧书名“演说家统御西方”仅在该书显示上下文补译，未知旧英文书名未被伪造或批量改写。

实机测试和剩余边界见 TESTING.md，以及 `data/HUD_RENDERING.md`、`data/TEMPLATE_GRAMMAR.md`、`data/RUNTIME_GRAMMAR.md`、`data/PROCEDURAL_TITLES.md`。这些结果仍不能证明全游戏任意场景绝无漏译。

真实引擎验证：10,211 条字符串查询零差异、95 项界面/悬停、12 项语法、25 项动态动词、17 组程序书籍与线索检查；离线 37 项测试通过。正常配置安装 38 个文件哈希一致、原存档哈希不变。完整证据与未证明的覆盖边界见 [TESTING.md](TESTING.md)。

## 0.1.3 烹饪冠词与交易用语

烹饪随机语料中的 `|article` 在中文食材和形容词生成后仍调用英文 Grammar.A。补充在 PostProcessors.Article 出口识别已展开的中文开头，跳过英文冠词，保留英文词和英文模式的原生行为；不改食材 ID、储存名称或已经写入存档的历史消息。

交易显示中的数字容量“打兰／打蓝”统一为“德拉姆”，保留数值和计算；清水是交易媒介，德拉姆是水量单位，不是另一种货币。补全交易分类及电池 Full/Empty 的中文显示。标准祝语 Live and drink 从“生而饮水”改为“长存，畅饮”；有意变体和粗话维持其上下文。验证见 `data/COOKING_TRADE.md`。

同版纳入三张 Steam 截图的后续修复：称呼“人类朋友”、坐着／躺在床上状态、苏丹历史日志分类及中文日期序数。所有修改在显示/模板语义出口进行，原存档数据不改。
