# Unity HUD 与悬停渲染修复

目标版本为 2.0.212.31。真实场景里 `ModelShark.TooltipTrigger.parameterizedTextFields[].value` 保存了英文按钮说明；这些文字不经过 `Strings._S`。`UITextSkin.text` 也可由预制体直接赋值。仅拦截消息、字符串表和 TMP setter，无法覆盖这些路径。

`QudCnHud` 在提示框填充前临时翻译参数值，在完成或异常退出时恢复源值。参数名、占位符及控制键保持不变。`UITextSkin.Apply` 翻译已知完整标签，并在切换英文后恢复其源文。增加 legacy Unity Text、UITextSkin.SetText 和 Apply 钩子，现有 TMP 与 ScreenBuffer 显示入口使用同一标签处理。映射采用完整标签匹配，保留外部空格和颜色包装。

真实隔离引擎中逐个执行 11 个按钮的 Initialize → Deactivate → WarmUp → SetTextAndSize，读取渲染后的 TMP 文本，并检查参数源值恢复；另验证英文 Autoexplore 与 Nearby objects 标题切回英文。14/14 通过。额外完整标签渲染检查见最新 `analysis/hover-runtime.log`。

`SetTextAndSize` 对当前文字执行占位符替换；`Tooltip.Deactivate` 才将缓存包装器中的 OriginalText 还原。测试若省略 Deactivate 会把上一条已填充文字错误当成下一条输入，产生假失败。因此探针模拟完整关闭/重开流程。

原始 UI 库存 `ui-inventory-before.json` 记录的是已加载组件，包含不可见的 prefab 示例、占位符、测试串与动态内容样本，不能把它当作真实玩家画面的漏译清单。纯模板键如 `%BodyText%` 必须保留；示例人名和程序名不能全局逐词替换。本次覆盖不证明所有菜单和所有物品动态提示已遍历。
