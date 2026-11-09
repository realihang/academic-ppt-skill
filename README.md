# Academic PPT

面向学术演示文稿设计、制作与修订的Codex技能。以研究问题、方法、证据与结论组织内容，结合原生PowerPoint母版、可编辑元素和逐页中文讲稿，适用于论文汇报、研究组会、开题报告与学位答辩。

默认16:9，支持4:3。中文采用微软雅黑，英文与数字采用Arial；页面大标题36磅，底部总结28磅，正文一级24磅、二级22磅、三级20磅，图例与辅助标注可按需减小。可编辑文字默认加粗，尤其是各级标题；表格标题行加粗，其余单元格使用常规字重。模板文字行距统一为1.2倍。每页右上角使用加粗Arial 20磅显示“当前页码/总页数”，白底主蓝字、主蓝底白字。八色色板中的灰色 `#7F7F7F` 用于图形边框及辅助轮廓，浅蓝保留为底色。

## 使用

将仓库内容保存到个人Codex技能目录的 `academic_ppt` 文件夹，确保该目录直接包含 `SKILL.md`。技能名称为 `academic_ppt`，展示名为 **Academic PPT**。调用 `$academic_ppt`，提供本次材料、汇报时长和页面比例。

每次调用先检查元素库末尾的补充入口及本机登记的编辑副本。补充区支持新模板与制作建议：用户可插入普通文本框写意见，推荐一框一条、以“建议：”开头。先读取并审阅建议，将清楚的长期制作偏好合并到对应规则，临时意见按指定范围处理；再整理新增素材和更新索引。

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
| [scripts/finalize_presentation.py](scripts/finalize_presentation.py) | 交付前统一整理页码、字重、无用正文占位框及打开视图 |

两种比例的母版文件各保留7页：封面、目录、三种正文版式、字体与色板、自由版式。图文、流程、比较和表格等组合统一在元素库中维护。逐页按内容选择：没有特别精炼的本页概括句时使用版式1；精炼概括句在28磅下能舒展地排成一行时使用版式2，确需两行时使用版式3。版式2、3均使用蓝底白字总结，不将整套正文默认套成版式2。母版右侧保留同序的八色色卡。

标题横线下的24磅默认正文框只在承载实际正文时保留，使用图片、图示或独立对象排版后删除不用的框；同步清理对应版式与母版中无人使用的默认正文框。参考PPT、元素库和交付文件均保存为普通编辑视图，打开后进入第1张幻灯片。

建议按内容生成稳定编号，同文去重，文字改变后重新审阅。处理记录保存在本机 `.local/suggestion-history.json`，记录归档后整理补充区；原文、个人设置与台账均不上传，通用规则脱敏后共享。建议在下一次调用本Skill时处理。

元素库分A—K共11类，共114页：封面、四页可点击索引、108项独立参考和末页空白补充入口。每项含用途与编辑备注；已有编号保持稳定，后续可继续扩展。K类提供容器、标签、括号、分隔及六类箭头，使用时根据内容调整比例与留白。每条完整关系优先由一个原生对象表达，按关系需要选择普通连接线或箭头。

页面增删、排序、合并及动效制作完成后，在最终渲染前运行 `python scripts/finalize_presentation.py --source draft.pptx --output final.pptx`，统一整理页码、默认字重、无用正文占位框和普通打开视图。当前页使用原生页码字段，总页数按文件实际页数写入，包含隐藏页；PowerPoint内手动增删后须再次刷新。保存前选中第1张幻灯片，可使用PowerPoint时重新打开确认；脚本设置视图类型不等于已验证应用中的选中页。

## 制作与经验维护

目录章节框使用1磅灰色边线和60%透明度。目录随材料变化并在章节开始时回访，表格文本双向居中。以信息传达效率选择表达：关系适合用图说明时优先图示，必要文字采用“小标题＋短说明”。优先使用材料原图；补充示意图可组合原生形状、图标与AI生成的独立元素，标签与连接线保持可编辑，整张AI示意图按需使用。

主动评估图中元素的分步呈现、关系高亮或点击跳转是否有助理解，有明确收益时使用原生动画或交互，并在备注写明目的和点击提示。页面直接切换，静态预览仍须能够完整读懂。AI示意图用于概念解释，真实结果与数值仍以研究材料为准。

每个新制作或重新制作的PPT文件只制作1页创新对照。选1页正文保留正常版本，再以相同内容制作这1页创新版，默认隐藏，备注说明设计思路。明确正向反馈后，将脱敏样式归入主体库，并在本机Memory独立一页保存创新页、思路和反馈；明确负向反馈后，仅在Memory记录创新页、思路、反馈及反思；没有反馈时不修改Memory和模板库。

Memory使用可编辑的 `.local/Memory.pptx`。Memory、待评信息、个人偏好及编辑副本登记均仅留本机。共享资源使用通用占位文字，原始研究内容、数据、讲稿、个人信息及未处理补充材料不进入分享包。
