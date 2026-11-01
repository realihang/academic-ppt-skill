# 科研汇报 Academic PPT

科研汇报的通用格式Skill，默认16:9，支持4:3。中文微软雅黑，英文和数字Arial，正文标题36磅，正文、表格与底部28磅。

## 使用

将仓库保存到个人Codex技能目录中的 `artifact-template-academic-ppt` 文件夹，调用 `$artifact-template-academic-ppt`，提供本次材料、时长和页面比例。

每次调用先检查元素库的补充入口及本机登记的编辑副本。有新增内容时，先脱敏、归类和更新索引，再使用主体库制作。

## 参考资源

| 文件 | 用途 |
| --- | --- |
| [assets/reference.pptx](assets/reference.pptx) | 默认16:9母版，版式2为白底蓝字居中的一行总结 |
| [assets/reference-4x3.pptx](assets/reference-4x3.pptx) | 对应4:3母版 |
| [assets/element-reference.pptx](assets/element-reference.pptx) | 10类80种可编辑组合，当前为审阅稿 |
| [references/element-catalog.md](references/element-catalog.md) | 类别、编号、页码与适用场景 |
| [references/catalog-manifest.json](references/catalog-manifest.json) | 结构化检索清单 |
| [references/library-workflow.md](references/library-workflow.md) | 补充区处理、隐藏创新页和反馈记录规则 |
| [references/design-guide.md](references/design-guide.md) | 字体、字号、母版与占位符 |
| [references/composition-guide.md](references/composition-guide.md) | 七色色板、图文组织与元素取舍 |
| scripts/inspect_reference_state.py | 只读检查补充内容和编辑副本变化 |

元素参考共85页：封面、三页可点击索引、80页独立组合、末页空白补充入口。主体可整体复制或取消组合编辑。后续新增组合不受80种限制，已有编号保持稳定。

每次制作汇报，先完成一页正常样式，再以相同内容完成至少一页新样式，创新页默认隐藏，备注说明创新思路。明确正向反馈后，脱敏样式入库，并在本机Memory独立一页保存创新页、思路和反馈；明确负向反馈后，只在Memory记录创新页、思路、反馈及反思；没有反馈时不修改Memory和模板库。

Memory使用现代可编辑的PPTX格式，位于 `.local/Memory.pptx`。首次使用时建立初始化封面，零条经验记录。本机Memory、待评定位信息、个人偏好及编辑副本登记均不上传。

目录随材料变化，表格双向居中。页面直接切换，正文默认静态，只有辅助讲解时使用动画。共享参考仅含通用占位格式，原始研究内容、数据、讲稿和个人信息不进入分享包。
