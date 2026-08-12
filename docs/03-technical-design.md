# 03. Technical Design

## 1. 技术栈
- 语言：Python 3.11+
- UI 框架：PySide6
- PDF 引擎：PyMuPDF (fitz)
- OCR 引擎：RapidOCR (ONNX Runtime, AVX2 加速)
- 图像处理：OpenCV, Pillow
- 数据库：SQLite 3 (WAL 模式)
- 打包：PyInstaller

## 2. 核心架构设计 (三层架构)
```text
[ Presentation Layer (PySide6 UI) ]
             |
[ Application & Service Layer (Pipelines, Workers) ]
             |
[ Domain Layer (Entities, BBox Geometry, Anchor Extractor) ]
             |
[ Infrastructure & Adapters (PyMuPDF, RapidOCR, SQLite) ]
```

## 3. 数据模型 (Domain Models)
- `TextBlock`: 代表页面上的文本框 (text, bbox, confidence)。
- `Anchor`: 识别出的题号/选项 Anchor。
- `QuestionRegion`: 题目合并后的包围盒与切图。
- `QuestionState`: 持久化题目实体 (id, raw_text, options, answer, image_path, manual_edited, status)。

## 4. 线程与异步处理
- 主界面运行在 Qt 事件循环 (Main Thread)。
- PDF 解析与 OCR 识别封装在 `ParseWorker` (QThread) 中异步执行，通过 Qt Signal 实时推送进度与识别结果至 UI。
- 重划框选识别封装在 `CropWorker` (QThread) 中，避免界面卡顿。
