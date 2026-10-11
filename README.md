# Caves of Qud 简体中文补充 Mod

当前补充包版本 **0.1.1**。针对 Bazzite 上的 **2.0.212.31 / lang-experimental**，依赖创意工坊简中补丁 **3746335636 / QudSimplifiedChinese**。本项目是独立本地 Mod，不覆盖创意工坊文件；加载顺序为原简中包 → QudCnSupplement。

## 覆盖范围与限制

目标是补齐当前版本的简体中文。官方 ExampleLanguage 导出中 25,090 个非空可本地化字段均有最终值，缺失字段为 0；这是**导出字段覆盖率 100%**，不能等同于“整个游戏任何情况下都没有英文”。游戏中的硬编码、程序生成组合、其他 Mod 和未来更新无法由这一指标证明。

补充包写出 28 个 XML、5,479 个字段；另有 HistorySpice 历史生成文本、精确界面映射、受限的动态消息模板和状态描述。保留变量、控制地址、颜色、数字和角色名称。技术标识符、按键、型号及原作者署名可保留拉丁字符。遗留译文仍可能存在语义和文风问题。

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
.venv/bin/python tools/build_corpus.py
.venv/bin/python tools/build_dynamic.py
.venv/bin/python tools/build_history.py
.venv/bin/python -m unittest discover -s tests -v
```

`tools/build_probe.py` 生成只用于隔离测试的探针，不随正式 Mod 安装。`tools/remote_test.py` 使用 Bazzite 的官方 Steam Linux Runtime，在独立存档与设置目录启动真实游戏；远端测试目录需预先放入原包与补充包。真实游戏编译和测试结果见 `analysis/` 及 `TESTING.md`。

## 来源

简中：Mao Shengzi 的 QudSimplifiedChinese。繁中与动态翻译参考：AosakiReiya（见 THIRD_PARTY_NOTICES.md）。部分译文由繁中转简体，再结合当前版本修订。原游戏资源属于 Freehold Games。本地补充不表示获得上游再许可，未上传或发布创意工坊。

## 0.1.1 动态语法修复

针对实机发现的冠词、拿取和未命中混合文本，修复短词筛选和颜色框外骰点后缀；在模板渲染专用的代词函数上区分主格、宾格、所有格及反身代词，不改游戏对象的代词数据或姓名。见 `data/DYNAMIC_GRAMMAR.md`。历史消息已存下的文本不追溯重写，新消息使用新规则。
