# Academic PPT

面向学术演示文稿设计、制作与修订的Codex技能。以研究问题、方法、证据与结论组织内容，结合原生PowerPoint母版、可编辑元素和逐页中文讲稿，适用于论文汇报、研究组会、开题报告与学位答辩。

默认16:9，支持4:3。中文采用微软雅黑，英文与数字采用Arial；页面大标题36磅，底部总结28磅，正文一级24磅、二级22磅、三级20磅，图例与辅助标注可按需减小。模板文字行距统一为1.2倍。八色色板中的灰色 `#7F7F7F` 用于图形边框及辅助轮廓，浅蓝保留为底色。

## 使用

将仓库内容保存到个人Codex技能目录的 `academic_ppt` 文件夹，确保该目录直接包含 `SKILL.md`。技能名称为 `academic_ppt`，展示名为 **Academic PPT**。调用 `$academic_ppt`，提供本次材料、汇报时长和页面比例。

每次调用先检查元素库末尾的补充入口及本机登记的编辑副本。有新增内容时，先脱敏、归类并更新索引，再使用主体库制作。

## 参考资源

| 文件 | 用途 |
| --- | --- |
| [assets/reference.pptx](assets/reference.pptx) | 默认16:9原生母版与7页基础参考 |
| [assets/reference-4x3.pptx](assets/reference-4x3.pptx) | 对应4:3原生母版与7页基础参考 |
| [assets/element-reference.pptx](assets/element-reference.pptx) | 95种排版组合与13类独立部件 |
| [references/element-catalog.md](references/element-catalog.md) | 唯一分类索引，包含稳定编号、页码及适用场景 |
| [references/design-guide.md](references/design-guide.md) | 字体层级、原生版式、占位符与比例适配 |
| [references/composition-guide.md](references/composition-guide.md) | 八色色板、边框、图文、列表及表格 |
| [references/library-workflow.md](references/library-workflow.md) | 补充区整理、隐藏创新对照与反馈记录 |
| [references/privacy-guide.md](references/privacy-guide.md) | 格式参考脱敏与共享边界 |
| [assets/previews/template-overview-16x9.png](assets/previews/template-overview-16x9.png) | 16:9基础页总览 |
| [assets/previews/template-overview-4x3.png](assets/previews/template-overview-4x3.png) | 4:3基础页总览 |
| [scripts/inspect_reference_state.py](scripts/inspect_reference_state.py) | 只读检查补充内容及编辑副本变化 |

两种比例的母版文件各保留7页：封面、目录、三种正文版式、字体与色板、自由版式。图文、流程、比较和表格等组合统一在元素库中维护。版式2使用底部蓝色矩形条与白色居中的一行总结。总结能舒展地放一行时优先一行，确有需要再用两行，两种情况均为28磅。母版右侧保留同序的八色色卡。

元素库分A—K共11类，共114页：封面、四页可点击索引、108项独立参考和末页空白补充入口。每项含用途与编辑备注；已有编号保持稳定，后续可继续扩展。K类提供容器、标签、括号、分隔及六类箭头，使用时根据内容调整比例与留白。每条完整关系优先由一个原生对象表达，按关系需要选择普通连接线或箭头。

## 制作与经验维护

目录随材料变化并在章节开始时回访，表格文本双向居中。优先使用材料原图，缺少合适示意时先使用PPT原生形状。页面直接切换，正文默认静态，仅在分步讲解确有需要时使用动画。

每个新制作或重新制作的PPT文件只制作1页创新对照。选1页正文保留正常版本，再以相同内容制作这1页创新版，默认隐藏，备注说明设计思路。明确正向反馈后，将脱敏样式归入主体库，并在本机Memory独立一页保存创新页、思路和反馈；明确负向反馈后，仅在Memory记录创新页、思路、反馈及反思；没有反馈时不修改Memory和模板库。

Memory使用可编辑的 `.local/Memory.pptx`。Memory、待评信息、个人偏好及编辑副本登记均仅留本机。共享资源使用通用占位文字，原始研究内容、数据、讲稿、个人信息及未处理补充材料不进入分享包。
