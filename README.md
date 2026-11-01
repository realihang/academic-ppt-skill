# Academic PPT

面向学术演示文稿设计、制作与修订的Codex技能。使用原生PowerPoint母版与可编辑元素，围绕研究问题、方法、证据和结论组织内容，配套逐页中文讲稿。适用于论文汇报、研究组会、开题报告和学位答辩。

默认16:9，支持4:3。中文采用微软雅黑，英文与数字采用Arial；正文页标题36磅，正文、表格与底部总结28磅。装饰按信息关系选用，保持简洁、清晰和学术表达。

## 使用

将仓库内容保存到个人Codex技能目录的 `academic_ppt` 文件夹，确保该目录下直接包含 `SKILL.md`。技能名称为 `academic_ppt`，展示名为 **Academic PPT**。调用 `$academic_ppt`，并提供本次材料、汇报时长和页面比例。

每次调用先检查元素库末尾的补充入口及本机登记的编辑副本。有新增内容时，先脱敏、归类并更新索引，再使用主体库制作。

## 参考资源

| 文件 | 用途 |
| --- | --- |
| [assets/reference.pptx](assets/reference.pptx) | 默认16:9母版，版式2使用底部蓝色矩形条与白色居中文字 |
| [assets/reference-4x3.pptx](assets/reference-4x3.pptx) | 对应4:3母版，保留相同字体与版式规则 |
| [assets/element-reference.pptx](assets/element-reference.pptx) | 11类参考：95种排版组合与13类独立部件 |
| [references/element-catalog.md](references/element-catalog.md) | 类别、稳定编号、页码及适用场景 |
| [references/catalog-manifest.json](references/catalog-manifest.json) | 结构化检索清单 |
| [references/library-workflow.md](references/library-workflow.md) | 补充区整理、隐藏创新对照与反馈记录 |
| [references/design-guide.md](references/design-guide.md) | 字体、字号、原生母版与占位符 |
| [references/composition-guide.md](references/composition-guide.md) | 配色、图文组织、元素与箭头选取 |
| [scripts/inspect_reference_state.py](scripts/inspect_reference_state.py) | 只读检查补充内容与编辑副本变化 |

元素库共114页：封面、四页可点击索引、108项独立参考及末页空白补充入口。每项单独成页，含用途与编辑备注。已有编号保持稳定，后续可继续扩展。K类包含容器、标签、括号、分隔及六类箭头；使用时按实际内容协调比例与留白。

## 制作与经验维护

目录根据本次材料生成，表格文本双向居中。优先使用材料原图，缺少合适示意时使用PPT原生形状。页面直接切换，正文默认静态，仅在分步讲解确有需要时使用动画。

每次制作汇报，先完成一页正常样式，再以相同内容制作至少一页创新样式。创新页默认隐藏，备注说明设计思路。收到明确正向反馈后，将脱敏样式归入主体库，并在本机Memory独立一页保存创新页、思路和反馈；明确负向反馈后，仅在Memory记录创新页、思路、反馈及反思；没有反馈时不修改Memory和模板库。

Memory使用可编辑的 `.local/Memory.pptx`，首次使用时建立初始化封面。Memory、待评信息、个人偏好与编辑副本登记均仅保留本机。共享资源使用通用占位文字，原始研究内容、数据、讲稿、个人信息及未处理补充材料不进入分享包。
