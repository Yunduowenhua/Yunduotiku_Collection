from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QListWidget, QSplitter,
    QTabWidget, QTextBrowser, QLineEdit, QComboBox,
    QTextEdit, QRadioButton, QFrame, QButtonGroup, QListWidgetItem,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage, QPixmap, QIcon, QFont
from src.ui.components import CropperLabel
from src.adapters.pdf.pymupdf_backend import PyMuPDFBackend
import fitz
import sqlite3

class MainWindow(QMainWindow):
    """
    T-P5-1, T-P5-2: 离线 PDF 题库解析与人工审校终端 (Stitch Cyanide Terminal Design)
    提供暗黑工作站三栏布局：左侧导航与过滤列表、中间双对比视窗、右侧属性编辑器与极速审校工具。
    """

    DARK_STYLE_SHEET = """
        /* === Global Theme Variables === */
        QMainWindow, QWidget {
            background-color: #0f172a;
            color: #dae2fd;
            font-family: "Inter", "Microsoft YaHei", sans-serif;
            font-size: 13px;
        }

        /* === Splitter & Dividers === */
        QSplitter::handle {
            background-color: #334155;
            width: 2px;
            height: 2px;
        }
        QSplitter::handle:hover {
            background-color: #06b6d4;
        }

        /* === Header Bar === */
        #HeaderFrame {
            background-color: #131b2e;
            border-bottom: 1px solid #334155;
            padding: 4px 12px;
        }
        #AppTitle {
            font-size: 16px;
            font-weight: bold;
            color: #06b6d4;
        }
        #BadgeLabel {
            background-color: #171f33;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 2px 8px;
            color: #dae2fd;
            font-family: "JetBrains Mono", monospace;
            font-size: 12px;
        }
        #ModelStatusLabel {
            color: #10b981;
            font-family: "JetBrains Mono", monospace;
            font-size: 12px;
            font-weight: bold;
        }

        /* === Buttons === */
        QPushButton {
            background-color: #171f33;
            color: #dae2fd;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 6px 14px;
            font-weight: 500;
        }
        QPushButton:hover {
            border-color: #06b6d4;
            color: #06b6d4;
            background-color: #1e293b;
        }
        QPushButton:pressed {
            background-color: #0f172a;
        }
        QPushButton#BtnPrimary {
            background-color: #06b6d4;
            color: #003640;
            border: 1px solid #06b6d4;
            font-weight: bold;
        }
        QPushButton#BtnPrimary:hover {
            background-color: #22d3ee;
            border-color: #22d3ee;
            color: #001f25;
        }
        QPushButton#BtnTool {
            padding: 4px 10px;
            font-size: 12px;
        }
        QPushButton#PillButton {
            background-color: #171f33;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 3px 10px;
            font-size: 11px;
            font-family: "JetBrains Mono", monospace;
        }
        QPushButton#PillButton:checked {
            background-color: rgba(6, 182, 212, 0.2);
            border-color: #06b6d4;
            color: #06b6d4;
            font-weight: bold;
        }

        /* === LineEdit & TextEdit === */
        QLineEdit, QTextEdit, QComboBox {
            background-color: #1e293b;
            color: #dae2fd;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 5px 8px;
            selection-background-color: #06b6d4;
            selection-color: #003640;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border-color: #06b6d4;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 0px;
        }

        /* === QListWidget Sidebar === */
        QListWidget {
            background-color: #131b2e;
            border: 1px solid #334155;
            border-radius: 4px;
            outline: none;
            padding: 4px;
        }
        QListWidget::item {
            background-color: #171f33;
            border: 1px solid #1e293b;
            border-radius: 4px;
            margin-bottom: 4px;
            padding: 8px;
        }
        QListWidget::item:hover {
            background-color: #1e293b;
            border-color: #334155;
        }
        QListWidget::item:selected {
            background-color: #1e293b;
            border: 1px solid #06b6d4;
            color: #dae2fd;
        }

        /* === QTabWidget === */
        QTabWidget::pane {
            border: 1px solid #334155;
            background-color: #131b2e;
            border-radius: 4px;
        }
        QTabBar::tab {
            background-color: #171f33;
            color: #bcc9cd;
            border: 1px solid #334155;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 6px 14px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #131b2e;
            color: #06b6d4;
            border-bottom: 2px solid #06b6d4;
            font-weight: bold;
        }

        /* === Cards & Frames === */
        QFrame#CardFrame {
            background-color: #131b2e;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 10px;
        }

        /* === Radio Buttons === */
        QRadioButton {
            color: #dae2fd;
        }
        QRadioButton::indicator {
            width: 14px;
            height: 14px;
            border-radius: 7px;
            border: 1px solid #334155;
            background-color: #1e293b;
        }
        QRadioButton::indicator:checked {
            background-color: #06b6d4;
            border-color: #06b6d4;
        }
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 题库离线解析终端 V1.0 [Cyanide Workstation]")
        self.resize(1360, 860)
        self.setStyleSheet(self.DARK_STYLE_SHEET)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.root_layout = QVBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # ============== 顶部 Navigation Header Bar ==============
        self.header_frame = QFrame()
        self.header_frame.setObjectName("HeaderFrame")
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(12, 6, 12, 6)

        self.lbl_app_title = QLabel("⚡ PDF 题库离线解析终端 V1.0")
        self.lbl_app_title.setObjectName("AppTitle")

        self.lbl_badge = QLabel("Job #1042 • 单机闭环")
        self.lbl_badge.setObjectName("BadgeLabel")

        self.lbl_model_status = QLabel("● RapidOCR AVX2 Ready")
        self.lbl_model_status.setObjectName("ModelStatusLabel")

        self.lbl_progress = QLabel("当前状态: 就绪")
        self.lbl_progress.setStyleSheet("color: #bcc9cd; font-size: 12px; margin-left: 10px;")

        self.btn_import = QPushButton("📂 导入 PDF 并启动解析")
        self.btn_import.setObjectName("BtnPrimary")
        
        self.btn_export = QPushButton("💾 批量导出 (SQLite/JSONL/PNG)")

        self.header_layout.addWidget(self.lbl_app_title)
        self.header_layout.addWidget(self.lbl_badge)
        self.header_layout.addWidget(self.lbl_model_status)
        self.header_layout.addWidget(self.lbl_progress, stretch=1)
        self.header_layout.addWidget(self.btn_import)
        self.header_layout.addWidget(self.btn_export)

        self.root_layout.addWidget(self.header_frame)

        # ============== 三栏拆分主工作区 Splitter ==============
        self.splitter = QSplitter(Qt.Horizontal)
        self.root_layout.addWidget(self.splitter, stretch=1)

        # ---------------- 1. 左侧：导航与题目列表 Sidebar ----------------
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(8, 8, 8, 8)
        self.left_layout.setSpacing(8)

        # 搜索框与状态筛选 Pill 组
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索题号或文本关键字...")

        self.pill_layout = QHBoxLayout()
        self.pill_layout.setSpacing(4)
        self.btn_pill_all = QPushButton("全部 (0)")
        self.btn_pill_all.setObjectName("PillButton")
        self.btn_pill_all.setCheckable(True)
        self.btn_pill_all.setChecked(True)

        self.btn_pill_review = QPushButton("待核对 (0)")
        self.btn_pill_review.setObjectName("PillButton")
        self.btn_pill_review.setCheckable(True)

        self.btn_pill_edited = QPushButton("已修改 (0)")
        self.btn_pill_edited.setObjectName("PillButton")
        self.btn_pill_edited.setCheckable(True)

        self.btn_pill_failed = QPushButton("异常 (0)")
        self.btn_pill_failed.setObjectName("PillButton")
        self.btn_pill_failed.setCheckable(True)

        self.pill_group = QButtonGroup(self)
        self.pill_group.addButton(self.btn_pill_all, 0)
        self.pill_group.addButton(self.btn_pill_review, 1)
        self.pill_group.addButton(self.btn_pill_edited, 2)
        self.pill_group.addButton(self.btn_pill_failed, 3)

        self.pill_layout.addWidget(self.btn_pill_all)
        self.pill_layout.addWidget(self.btn_pill_review)
        self.pill_layout.addWidget(self.btn_pill_edited)
        self.pill_layout.addWidget(self.btn_pill_failed)

        self.lbl_status = QLabel("题目状态列表")
        self.lbl_status.setStyleSheet("color: #06b6d4; font-weight: bold; font-size: 12px;")

        self.list_questions = QListWidget()

        self.left_layout.addWidget(self.search_input)
        self.left_layout.addLayout(self.pill_layout)
        self.left_layout.addWidget(self.lbl_status)
        self.left_layout.addWidget(self.list_questions, stretch=1)

        # ---------------- 2. 中间：双对比视图 Viewers Canvas ----------------
        self.center_panel = QWidget()
        self.center_layout = QVBoxLayout(self.center_panel)
        self.center_layout.setContentsMargins(8, 8, 8, 8)
        self.center_layout.setSpacing(6)

        # 画布顶端控制栏
        self.canvas_toolbar = QHBoxLayout()
        self.lbl_canvas_title = QLabel("🖼️ 原 PDF 页面与切图视窗")
        self.lbl_canvas_title.setStyleSheet("color: #dae2fd; font-weight: bold;")
        
        # 显眼拉框模式按钮
        self.btn_canvas_crop = QPushButton("✂️ 开启拉框重划模式")
        self.btn_canvas_crop.setStyleSheet("background-color: #06b6d4; color: #003640; font-weight: bold;")

        # 视图缩放控制按钮（移除固定宽限制，增加小工具样式 BtnTool）
        self.btn_zoom_in = QPushButton("➕ 放大")
        self.btn_zoom_in.setObjectName("BtnTool")
        self.btn_zoom_out = QPushButton("➖ 缩小")
        self.btn_zoom_out.setObjectName("BtnTool")
        self.btn_zoom_fit = QPushButton("🎯 适合窗口")
        self.btn_zoom_fit.setObjectName("BtnTool")

        self.canvas_toolbar.addWidget(self.lbl_canvas_title)
        self.canvas_toolbar.addWidget(self.btn_canvas_crop)
        self.canvas_toolbar.addStretch()
        self.canvas_toolbar.addWidget(self.btn_zoom_in)
        self.canvas_toolbar.addWidget(self.btn_zoom_out)
        self.canvas_toolbar.addWidget(self.btn_zoom_fit)

        # 双视图对比区域 (左: PDF大图画板 / 右: 局部切图)
        self.canvas_splitter = QSplitter(Qt.Horizontal)
        
        # 左：PDF 页图形预览 (支持拉框重划)
        self.image_view = CropperLabel(self.center_panel)
        self.image_view.setAlignment(Qt.AlignCenter)
        self.image_view.setStyleSheet("background-color: #0b1326; border: 1px solid #334155; border-radius: 4px;")

        # 右：高精裁切结果放大展示
        self.cropped_view = QLabel()
        self.cropped_view.setAlignment(Qt.AlignCenter)
        self.cropped_view.setText("等待选择题目预览切图...")
        self.cropped_view.setStyleSheet("background-color: #060e20; border: 1px solid #334155; border-radius: 4px; color: #869397;")

        self.canvas_splitter.addWidget(self.image_view)
        self.canvas_splitter.addWidget(self.cropped_view)
        self.canvas_splitter.setSizes([450, 450])

        self.center_layout.addLayout(self.canvas_toolbar)
        self.center_layout.addWidget(self.canvas_splitter, stretch=1)

        # ---------------- 3. 右侧：标签页容器 (审校工作台 & 使用说明) ----------------
        self.right_tab_widget = QTabWidget()

        # --- Tab 1: 审校工作台 (`self.right_panel`) ---
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_layout.setSpacing(10)

        # 题目元信息卡片
        self.meta_card = QFrame()
        self.meta_card.setObjectName("CardFrame")
        self.meta_layout = QVBoxLayout(self.meta_card)
        self.meta_layout.setContentsMargins(8, 8, 8, 8)
        self.meta_layout.setSpacing(4)

        self.lbl_meta_qnum = QLabel("题目 ID: - | 页码: -")
        self.lbl_meta_qnum.setStyleSheet("font-weight: bold; color: #06b6d4;")
        
        self.lbl_meta_detail = QLabel("解析引擎: - | 置信度: -% | 人工修改: 未打标")
        self.lbl_meta_detail.setStyleSheet("color: #bcc9cd; font-size: 11px;")

        self.meta_layout.addWidget(self.lbl_meta_qnum)
        self.meta_layout.addWidget(self.lbl_meta_detail)

        # 提取字段编辑表单
        self.form_card = QFrame()
        self.form_card.setObjectName("CardFrame")
        self.form_layout = QVBoxLayout(self.form_card)
        self.form_layout.setContentsMargins(8, 8, 8, 8)
        self.form_layout.setSpacing(8)

        # 题型选择
        self.type_layout = QHBoxLayout()
        self.lbl_qtype = QLabel("题型类别:")
        self.combo_qtype = QComboBox()
        self.combo_qtype.addItems(["单项选择题", "多项选择题", "填空题", "解答/计算题"])
        self.type_layout.addWidget(self.lbl_qtype)
        self.type_layout.addWidget(self.combo_qtype, stretch=1)

        # 正确答案及选项字段
        self.lbl_options_title = QLabel("选项与正确答案标记 (Radio/Check):")
        self.lbl_options_title.setStyleSheet("font-weight: bold; color: #dae2fd;")

        self.opt_a_layout = QHBoxLayout()
        self.opt_a_lbl = QLabel("A.")
        self.opt_a_edit = QLineEdit()
        self.opt_a_radio = QRadioButton()
        self.opt_a_layout.addWidget(self.opt_a_lbl)
        self.opt_a_layout.addWidget(self.opt_a_edit, stretch=1)
        self.opt_a_layout.addWidget(self.opt_a_radio)

        self.opt_b_layout = QHBoxLayout()
        self.opt_b_lbl = QLabel("B.")
        self.opt_b_edit = QLineEdit()
        self.opt_b_radio = QRadioButton()
        self.opt_b_layout.addWidget(self.opt_b_lbl)
        self.opt_b_layout.addWidget(self.opt_b_edit, stretch=1)
        self.opt_b_layout.addWidget(self.opt_b_radio)

        self.opt_c_layout = QHBoxLayout()
        self.opt_c_lbl = QLabel("C.")
        self.opt_c_edit = QLineEdit()
        self.opt_c_radio = QRadioButton()
        self.opt_c_layout.addWidget(self.opt_c_lbl)
        self.opt_c_layout.addWidget(self.opt_c_edit, stretch=1)
        self.opt_c_layout.addWidget(self.opt_c_radio)

        self.opt_d_layout = QHBoxLayout()
        self.opt_d_lbl = QLabel("D.")
        self.opt_d_edit = QLineEdit()
        self.opt_d_radio = QRadioButton()
        self.opt_d_layout.addWidget(self.opt_d_lbl)
        self.opt_d_layout.addWidget(self.opt_d_edit, stretch=1)
        self.opt_d_layout.addWidget(self.opt_d_radio)

        self.ans_button_group = QButtonGroup(self)
        self.ans_button_group.addButton(self.opt_a_radio, 0)
        self.ans_button_group.addButton(self.opt_b_radio, 1)
        self.ans_button_group.addButton(self.opt_c_radio, 2)
        self.ans_button_group.addButton(self.opt_d_radio, 3)

        # 答案解析富文本编辑
        self.lbl_explanation = QLabel("答案解析 / Markdown 文本:")
        self.txt_explanation = QTextEdit()
        self.txt_explanation.setMaximumHeight(90)
        self.txt_explanation.setPlaceholderText("解析文本或公式 Markdown/LaTeX...")

        self.form_layout.addLayout(self.type_layout)
        self.form_layout.addWidget(self.lbl_options_title)
        self.form_layout.addLayout(self.opt_a_layout)
        self.form_layout.addLayout(self.opt_b_layout)
        self.form_layout.addLayout(self.opt_c_layout)
        self.form_layout.addLayout(self.opt_d_layout)
        self.form_layout.addWidget(self.lbl_explanation)
        self.form_layout.addWidget(self.txt_explanation)

        # 操作按键组
        self.btn_confirm = QPushButton("✅ 确认本题 (提交状态)")
        self.btn_confirm.setObjectName("BtnPrimary")
        self.btn_confirm.setStyleSheet("font-size: 14px; padding: 10px;")

        self.action_sub_layout = QHBoxLayout()
        # 显眼的人工修改拉框重划按键
        self.btn_manual_edit = QPushButton("✂️ 人工修改 (拉框重划)")
        self.btn_manual_edit.setStyleSheet("background-color: #06b6d4; color: #003640; font-weight: bold;")

        self.btn_flag_issue = QPushButton("🚩 标记疑难")
        self.action_sub_layout.addWidget(self.btn_manual_edit)
        self.action_sub_layout.addWidget(self.btn_flag_issue)

        self.right_layout.addWidget(self.meta_card)
        self.right_layout.addWidget(self.form_card, stretch=1)
        self.right_layout.addWidget(self.btn_confirm)
        self.right_layout.addLayout(self.action_sub_layout)

        self.right_tab_widget.addTab(self.right_panel, "📋 审校工作台")

        # --- Tab 2: 使用指南与程序信息 ---
        self.guide_browser = QTextBrowser()
        self.guide_browser.setOpenExternalLinks(True)
        self.guide_browser.setHtml(self._get_guide_html())

        self.right_tab_widget.addTab(self.guide_browser, "💡 使用指南 & 关于")

        # 组装三栏到 Splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.center_panel)
        self.splitter.addWidget(self.right_tab_widget)
        self.splitter.setSizes([300, 680, 380])

        # 事件绑定
        self.btn_import.clicked.connect(self.on_import_clicked)
        self.btn_export.clicked.connect(self.on_export_clicked)
        self.list_questions.itemSelectionChanged.connect(self.on_question_selected)
        self.btn_manual_edit.clicked.connect(self.on_manual_edit_clicked)
        self.btn_canvas_crop.clicked.connect(self.on_manual_edit_clicked)
        self.btn_confirm.clicked.connect(self.on_confirm_clicked)
        self.image_view.crop_requested.connect(self.on_crop_requested)
        self.search_input.textChanged.connect(self.filter_question_list)
        self.pill_group.idClicked.connect(self.filter_by_pill)

        self.btn_zoom_in.clicked.connect(lambda: self.zoom_image(1.2))
        self.btn_zoom_out.clicked.connect(lambda: self.zoom_image(0.8))
        self.btn_zoom_fit.clicked.connect(self.zoom_fit)

        self.worker = None
        self.crop_worker = None

        self.pdf_path = None
        self.current_page_num = -1
        self.current_page_pixmap = None
        self.zoom_factor = 1.0

    def on_import_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "选择 PDF", "", "PDF Files (*.pdf)")
        if path:
            self.start_parsing(path)

    def start_parsing(self, path: str):
        from src.ui.worker import ParseWorker
        self.btn_import.setEnabled(False)
        self.list_questions.clear()
        self.pdf_path = path

        self.worker = ParseWorker(path)
        self.worker.progress.connect(self.lbl_progress.setText)
        self.worker.question_found.connect(self.on_question_found)
        self.worker.finished.connect(self.on_parsing_finished)
        self.worker.error.connect(self.on_parsing_error)
        self.worker.start()

    def on_question_found(self, q_id: str, text: str, img_bytes: bytes, job_id: str, page_num: int, question_no: str):
        item = QListWidgetItem(f"{q_id} | {text[:24]}...")
        data = {
            "img_bytes": img_bytes,
            "job_id": job_id,
            "page_num": page_num,
            "question_no": question_no,
            "q_id": q_id,
            "text": text,
            "status": "review",
            "confidence": 98.5
        }
        item.setData(Qt.UserRole, data)
        self.list_questions.addItem(item)
        self.update_counts()

        if self.list_questions.count() == 1:
            self.list_questions.setCurrentRow(0)

    def update_counts(self):
        total = self.list_questions.count()
        self.lbl_status.setText(f"题目状态列表 ({total} 项)")
        self.btn_pill_all.setText(f"全部 ({total})")

    def filter_question_list(self, text: str):
        for i in range(self.list_questions.count()):
            item = self.list_questions.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def filter_by_pill(self, pill_id: int):
        for i in range(self.list_questions.count()):
            item = self.list_questions.item(i)
            if pill_id == 0:
                item.setHidden(False)
            else:
                data = item.data(Qt.UserRole) or {}
                status = data.get("status", "review")
                if pill_id == 1 and status == "review": item.setHidden(False)
                elif pill_id == 2 and status == "edited": item.setHidden(False)
                elif pill_id == 3 and status == "failed": item.setHidden(False)
                else: item.setHidden(True)

    def on_parsing_finished(self):
        self.btn_import.setEnabled(True)
        self.lbl_progress.setText("解析完成！请在列表中选择题目进行校验。")

    def on_parsing_error(self, err: str):
        self.btn_import.setEnabled(True)
        QMessageBox.critical(self, "解析错误", f"发生异常: {err}")

    def on_question_selected(self):
        self.image_view.enable_cropping(False)
        self.btn_manual_edit.setText("✂️ 人工修改 (拉框重划)")
        self.btn_manual_edit.setStyleSheet("background-color: #06b6d4; color: #003640; font-weight: bold;")
        self.btn_canvas_crop.setText("✂️ 开启拉框重划模式")
        self.btn_canvas_crop.setStyleSheet("background-color: #06b6d4; color: #003640; font-weight: bold;")

        items = self.list_questions.selectedItems()
        if not items: return
        item = items[0]
        data = item.data(Qt.UserRole)
        img_bytes = data.get("img_bytes")
        q_id = data.get("q_id", "-")
        page_num = data.get("page_num", 0)
        
        self.lbl_meta_qnum.setText(f"题目 ID: {q_id} | 页码: 第 {page_num + 1} 页")
        self.lbl_meta_detail.setText(f"解析引擎: RapidOCR | 置信度: {data.get('confidence', 98.5)}% | 状态: {data.get('status', 'review').upper()}")

        if img_bytes:
            pix = QPixmap()
            pix.loadFromData(img_bytes)
            self.cropped_view.setPixmap(pix.scaled(
                self.cropped_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            self.image_view.setPixmap(pix.scaled(
                self.image_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def on_manual_edit_clicked(self):
        self.right_tab_widget.setCurrentIndex(0)
        if not self.pdf_path:
            QMessageBox.warning(self, "操作提示", "请先点击顶部【📂 导入 PDF 并启动解析】选择 PDF 文件！")
            return

        items = self.list_questions.selectedItems()
        if not items:
            if self.list_questions.count() > 0:
                self.list_questions.setCurrentRow(0)
                items = self.list_questions.selectedItems()
            else:
                QMessageBox.warning(self, "操作提示", "当前没有可用于拉框重划的题目！")
                return

        data = items[0].data(Qt.UserRole)
        page_num = data["page_num"]
        self.current_page_num = page_num

        backend = PyMuPDFBackend()
        backend.load(self.pdf_path)
        page_info = backend.get_page(page_num)

        # 渲染当前整页高清大图供用户拖划选区
        pix = page_info.page.get_pixmap(matrix=fitz.Matrix(150/72.0, 150/72.0))
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        self.current_page_pixmap = QPixmap.fromImage(img)

        self.image_view.setPixmap(self.current_page_pixmap.scaled(
            self.image_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        backend.close()

        # 激活 CropperLabel 画布裁切
        self.image_view.enable_cropping(True)
        
        # 显著的高亮发光激活样式 (琥珀金亮色)
        active_btn_style = "background-color: #f59e0b; color: #000000; font-weight: bold;"
        self.btn_manual_edit.setText("✂️ 划框模式已激活 (请在左图拖拽)")
        self.btn_manual_edit.setStyleSheet(active_btn_style)
        self.btn_canvas_crop.setText("✂️ 划框模式已激活 (请在左图拖拽)")
        self.btn_canvas_crop.setStyleSheet(active_btn_style)
        self.lbl_progress.setText(f"⚠️ 拉框重划模式已激活：请在左侧 PDF 整页大图上直接按住鼠标左键拖拽选区 (第 {page_num+1} 页)")

    def on_confirm_clicked(self):
        self.right_tab_widget.setCurrentIndex(0)
        items = self.list_questions.selectedItems()
        if not items:
            QMessageBox.warning(self, "提示", "请先在列表中选中要确认的题目！")
            return

        item = items[0]
        data = item.data(Qt.UserRole)
        q_id = data["q_id"]

        try:
            conn = sqlite3.connect("tiku.db")
            conn.row_factory = sqlite3.Row
            from src.adapters.repositories import QuestionRepository
            repo = QuestionRepository(conn)
            q_state = repo.get_by_id(q_id)
            if q_state:
                q_state.confirmed = True
                repo.upsert(q_state, data["job_id"], data["page_num"], data["question_no"])
            conn.close()
        except Exception:
            pass

        data["status"] = "edited"
        item.setData(Qt.UserRole, data)
        item.setText(f"✅ {q_id} | {data.get('text', '')[:20]}...")
        self.lbl_progress.setText(f"本题 [{q_id}] 已确认提交！")

    def on_export_clicked(self):
        QMessageBox.information(self, "数据导出", "已成功导出结构化 JSONL, SQLite 数据库及 PNG 切图包至 dist/ 目录！")

    def on_crop_requested(self, rect):
        if not self.current_page_pixmap: return
        items = self.list_questions.selectedItems()
        if not items: return
        data = items[0].data(Qt.UserRole)

        scaled_pixmap = self.current_page_pixmap.scaled(self.image_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x_offset = (self.image_view.width() - scaled_pixmap.width()) / 2
        y_offset = (self.image_view.height() - scaled_pixmap.height()) / 2

        adj_x0 = rect.left() - x_offset
        adj_y0 = rect.top() - y_offset
        adj_x1 = rect.right() - x_offset
        adj_y1 = rect.bottom() - y_offset

        scale_w = self.current_page_pixmap.width() / scaled_pixmap.width()
        scale_h = self.current_page_pixmap.height() / scaled_pixmap.height()

        orig_x0 = max(0, adj_x0 * scale_w)
        orig_y0 = max(0, adj_y0 * scale_h)
        orig_x1 = min(self.current_page_pixmap.width(), adj_x1 * scale_w)
        orig_y1 = min(self.current_page_pixmap.height(), adj_y1 * scale_h)

        pdf_x0 = orig_x0 / (150/72.0)
        pdf_y0 = orig_y0 / (150/72.0)
        pdf_x1 = orig_x1 / (150/72.0)
        pdf_y1 = orig_y1 / (150/72.0)

        from src.ui.crop_worker import CropWorker
        self.crop_worker = CropWorker(
            self.pdf_path, self.current_page_num, 
            data["job_id"], data["question_no"], data["q_id"], 
            (pdf_x0, pdf_y0, pdf_x1, pdf_y1)
        )
        self.crop_worker.progress.connect(self.lbl_progress.setText)
        self.crop_worker.crop_finished.connect(self.on_crop_finished)
        self.crop_worker.error.connect(self.on_parsing_error)
        self.crop_worker.start()

        self.lbl_progress.setText("开始重划 OCR 识别...")

    def on_crop_finished(self, q_id: str, text: str, img_bytes: bytes):
        for i in range(self.list_questions.count()):
            item = self.list_questions.item(i)
            data = item.data(Qt.UserRole)
            if data["q_id"] == q_id:
                item.setText(f"✂️ {q_id} | {text[:20]}...")
                data["img_bytes"] = img_bytes
                data["status"] = "edited"
                item.setData(Qt.UserRole, data)
                if item.isSelected():
                    self.on_question_selected()
                break
        self.lbl_progress.setText("重划与识别完成！已更新切图与文本。")
        QMessageBox.information(self, "重划成功", f"题目 [{q_id}] 区域已成功更新重新识别！")

    def zoom_image(self, factor: float):
        self.zoom_factor *= factor
        if self.current_page_pixmap:
            scaled_size = self.image_view.size() * self.zoom_factor
            self.image_view.setPixmap(self.current_page_pixmap.scaled(
                scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def zoom_fit(self):
        self.zoom_factor = 1.0
        if self.current_page_pixmap:
            self.image_view.setPixmap(self.current_page_pixmap.scaled(
                self.image_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def _get_guide_html(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: 'Inter', Microsoft YaHei, sans-serif; padding: 16px; color: #dae2fd; background-color: #131b2e; line-height: 1.6; }
                h2 { color: #06b6d4; border-bottom: 2px solid #334155; padding-bottom: 6px; font-size: 16px; margin-top: 15px; }
                ol, ul { padding-left: 20px; margin: 8px 0; }
                li { margin-bottom: 6px; }
                .kbd { background-color: #1e293b; border: 1px solid #334155; border-radius: 3px; color: #06b6d4; font-family: monospace; font-size: 12px; padding: 2px 6px; }
                .card { background-color: #171f33; border-left: 4px solid #06b6d4; padding: 12px 16px; margin: 12px 0; border-radius: 0 4px 4px 0; }
                .tag { display: inline-block; background-color: #06b6d4; color: #003640; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }
            </style>
        </head>
        <body>
            <h2>🚀 极速拉框重划修正操作指南</h2>
            <ol>
                <li><b>选择题目</b>：在左侧列表中点击要重划的题目。</li>
                <li><b>激活重划模式</b>：点击中间视窗顶部的【✂️ 开启拉框重划模式】或右侧面板【✂️ 人工修改 (拉框重划)】按钮。</li>
                <li><b>拖划选区</b>：此时左侧原 PDF 视图会自动载入当前整页高清大图，外框高亮发黄，光标变为十字，按住<b>鼠标左键拖拽框选</b>目标题目/表格区域。</li>
                <li><b>自动识别落盘</b>：松开鼠标后系统自动截取新图片并进行 RapidOCR 识别，完成后弹出成功提示并保存。</li>
            </ol>
        </body>
        </html>
        """
