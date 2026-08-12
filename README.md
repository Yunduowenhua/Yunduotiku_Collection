# PDF 题库自动提取工具

基于 PySide6 + RapidOCR + PyMuPDF 的 Windows 桌面应用，用于 PDF 题库的自动解构、识别与人工审校。

## 核心特性
- **双模解析**：自动按页识别原生文本页与扫描件，路由至 RapidOCR / PyMuPDF。
- **暗黑 3-Pane 工作站 UI**：基于 Stitch 设计系统的 Cyanide Terminal 界面，左侧导航、中间双视窗比对、右侧极速审校。
- **拉框重划修正 (Ctrl+E)**：对切图或表格进行实时拖拽框选与重新识别。
- **数据持久化保护**：打上 `manual_edited=True` 标记，防止重新导入覆盖人工成果。

## 运行方式
```bash
python -m src.main
```
