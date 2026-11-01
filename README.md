# 科研汇报 Academic PPT

科研汇报的通用格式Skill，默认16:9，支持4:3。中文使用微软雅黑，英文与数字使用Arial；正文标题36磅，正文与表格28磅。

## 使用

将仓库保存到个人Codex技能目录中的 `artifact-template-academic-ppt` 文件夹，调用 `$artifact-template-academic-ppt`，并提供本次材料、时长与页面比例。

## 参考资源

| 文件 | 用途 |
| --- | --- |
| [assets/reference.pptx](assets/reference.pptx) | 默认16:9母版与基本页面结构 |
| [assets/reference-4x3.pptx](assets/reference-4x3.pptx) | 4:3母版与基本页面结构 |
| [assets/element-reference.pptx](assets/element-reference.pptx) | 10类60种可编辑组合；当前为审阅稿 |
| [references/element-catalog.md](references/element-catalog.md) | 类别、编号、页码及适用场景索引 |
| [references/design-guide.md](references/design-guide.md) | 字体、字号、母版与占位符规范 |
| [references/composition-guide.md](references/composition-guide.md) | 七色色板、图文组织和元素取舍 |
| assets/preview.png、assets/previews/ | 模板封面及辅助预览 |
| scripts/ | 原生选页复制与按需点击淡入工具 |

元素参考PPT共63页：封面、两页可点击分类索引，以及60页独立组合。主体可以整体复制，也可以取消组合分别编辑。备注包含用途、结构和编辑提示。

用户优化并回传最终版后，替换同名元素参考文件并更新索引，后续元素选取以用户最终版为准。

目录随材料变化，表格双向居中。正文默认静态，页面直接切换，仅在分步讲解确有需要时设置动画。

共享参考只包含通用占位内容与格式。原始研究文档、图表、讲稿及个人信息不进入分享包；`.local/`只保存在本机。
