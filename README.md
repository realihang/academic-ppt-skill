# 科研汇报 Academic PPT

科研汇报的通用格式 Skill，默认 **16:9**，支持 **4:3**。

中文使用微软雅黑，英文与数字使用 Arial；正文标题36磅，正文与总结28磅。

## 使用

将本仓库保存到个人 Codex 技能目录下的 `artifact-template-academic-ppt` 文件夹。制作时调用 `$artifact-template-academic-ppt`，提供本次材料、汇报时长和页面比例。

例如：使用 $artifact-template-academic-ppt，将这篇论文制作成约20分钟的4:3汇报，优先使用论文原图，并把逐页中文讲稿放进备注。

## 格式参考

| 路径 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 制作规范 |
| [assets/reference.pptx](assets/reference.pptx) | 默认16:9通用参考，14页 |
| [assets/reference-4x3.pptx](assets/reference-4x3.pptx) | 可选4:3通用参考，14页 |
| assets/preview.png、assets/preview-4x3.png | 两种比例的封面预览 |
| assets/style-overview.png、assets/style-overview-4x3.png | 通用版式概览 |
| references/ | 母版索引、内容组织、配色及脱敏规则 |
| scripts/ | 保留原生母版的选页复制与点击淡入工具 |

目录随材料变化，章节开始时回访并高亮。表格双向居中，并列条目使用较大的实心正方形列表。以简洁直角元素、清楚的对比度和充足留白呈现学术内容。

参考资产只展示通用文字、空图框、示例表格与可编辑格式。本机偏好可保存在 `.local/presenter.json`，该目录不参与分享。参考材料的保管与分享规则见 [脱敏与打包检查](references/privacy-guide.md)。

选页复制工具使用 `--aspect-ratio 4:3` 选择4:3参考，省略时默认16:9。
