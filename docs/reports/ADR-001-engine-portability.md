# ADR-001: PDF 引擎选型与可移植性设计

## 1. 状态
**已批准 (Approved)**

## 2. 背景与问题
本项目需要高精度的 PDF 解析能力，包括提取文本、图层边界和直接截图。
市场上主流的 PDF 处理库包括：
- `PyMuPDF` (fitz)：功能全面，速度极快，文本和图像处理能力强。但在 1.24+ 版本后采用严格的 AGPL-3.0 许可证。
- `pypdfium2` (基于 PDFium)：Apache 2.0 许可证，商业友好，但 API 较底层，高级封装不如 PyMuPDF 丰富。

当前项目启动总控说明中明确规定本期交付采用“路线 A”：仅供内部自用，绝不进行商业分发或提供网络服务。因此，可以使用 PyMuPDF。
**但是，为了防止未来需求变更导致架构被 AGPL 锁死，必须在架构层面实现引擎的完全隔离。**

## 3. 决策
1. **采用 PyMuPDF** 作为首版（内用版）的核心 PDF 引擎。
2. **强制物理隔离**：建立 `PDFBackend` 接口（适配层），任何依赖 `fitz` 的代码只能存在于 `src/adapters/pdf/` 目录下。
3. **数据类型防泄漏**：`PDFBackend` 必须将所有 PDF 引擎特有的数据结构（如 `fitz.Document`, `fitz.Page`, `fitz.Rect`）转换为项目中立的领域模型（如 `domain.models.Document`, `domain.models.Rect`）。
4. **验证机制**：在 CI 或测试环节加入 AST 扫描或静态分析（如 `import-linter`），断言 `fitz` 关键字没有在 `adapters/pdf` 外部出现。

## 4. 替代方案 (Plan B: pypdfium2)
如果未来需要进行软件分发，可以通过以下步骤无缝替换引擎：
1. 移除 `src/adapters/pdf/pymupdf_backend.py`。
2. 实现 `src/adapters/pdf/pypdfium2_backend.py`，实现相同的 `PDFBackend` 接口。
3. 领域层和 UI 层代码**需做到零修改**。

## 5. 影响
- **优点**：既享受了 PyMuPDF 的高性能和便利性，又通过设计模式规避了版权污染和架构锁死风险。
- **缺点**：开发时需要编写大量的转换代码（如 `fitz.Rect` 转 `CanonicalRect`），略微增加开发工作量。每次增加新的 PDF 交互方法都必须在接口层先定义。
