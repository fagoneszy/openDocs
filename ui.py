from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QToolTip,
)
from PySide6.QtCore import (
    Qt,
    QMimeData,
    QSize,
    QEvent,
    QPropertyAnimation,
    QPoint,
    QRect,
)
from PySide6.QtGui import (
    QFont,
    QColor,
    QPalette,
    QDragEnterEvent,
    QDropEvent,
    QCursor,
)


# ── Colors (grafite/frio — OpenCode/Linear aesthetic) ──────────────────────

BG_COLOR = "#090B10"
SURFACE_COLOR = "#10131A"
SURFACE_ELEVATED = "#151922"
BORDER_COLOR = "#252A35"
PRIMARY_TEXT = "#F4F7FB"
SECONDARY_TEXT = "#8B95A7"
ACCENT = "#6E8CFF"
ACCENT_GLOW = "#90A8FF"
WHITE = "#FFFFFF"


def apply_palette(widget):
    """Apply the OpenDocs dark theme to a widget."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_COLOR))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(PRIMARY_TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(SURFACE_COLOR))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(SURFACE_ELEVATED))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(BG_COLOR))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(PRIMARY_TEXT))
    palette.setColor(QPalette.ColorRole.Text, QColor(PRIMARY_TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(SURFACE_ELEVATED))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(PRIMARY_TEXT))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(WHITE))
    palette.setColor(QPalette.ColorRole.Link, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BG_COLOR))
    widget.setPalette(palette)
    widget.setAutoFillBackground(True)


# ── Style helper: generate stylesheets without f-string triple-quote issues ──

def style_str(*parts):
    """Concatenate style parts into a single string."""
    return "".join(parts)


class DropArea(QLabel):
    """Large drop zone that accepts file drops."""

    dropped = object()  # sentinel to avoid duplicate signals

    def __init__(self, text="Drop a file here"):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(120)
        self.setStyleSheet(
            style_str(
                "QLabel {",
                "color: " + SECONDARY_TEXT + ";",
                "background: " + SURFACE_ELEVATED + ";",
                "border: 2px dashed " + BORDER_COLOR + ";",
                "border-radius: 8px;",
                "font-size: 14px;",
                "font-weight: 500;",
                "}",
                "QLabel:hover {",
                "border-color: " + ACCENT + ";",
                "background: rgba(110, 140, 255, 0.08);",
                "}",
            )
        )
        apply_palette(self)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setWordWrap(True)

    def enterEvent(self, event):
        self.setStyleSheet(
            style_str(
                "QLabel {",
                "color: " + ACCENT + ";",
                "background: rgba(110, 140, 255, 0.08);",
                "border: 2px dashed " + ACCENT + ";",
                "border-radius: 8px;",
                "font-size: 14px;",
                "font-weight: 500;",
                "}",
            )
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(
            style_str(
                "QLabel {",
                "color: " + SECONDARY_TEXT + ";",
                "background: " + SURFACE_ELEVATED + ";",
                "border: 2px dashed " + BORDER_COLOR + ";",
                "border-radius: 8px;",
                "font-size: 14px;",
                "font-weight: 500;",
                "}",
            )
        )
        super().leaveEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_paths = [
                url.toLocalFile() for url in urls if url.isLocalFile()
            ]
            self.setProperty("dropped_paths", file_paths)
            self.style().polish(self)


class DocumentPreview(QFrame):
    """Shows a summary of the opened document."""

    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            style_str(
                "QFrame {",
                "background: " + SURFACE_COLOR + ";",
                "border: 1px solid " + BORDER_COLOR + ";",
                "border-radius: 6px;",
                "margin: 4px;",
                "}",
            )
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.kind_label = QLabel("Arquivo não aberto")
        self.kind_label.setStyleSheet(
            "color: " + SECONDARY_TEXT + "; font-size: 12px;"
        )
        layout.addWidget(self.kind_label)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(
            "color: " + SECONDARY_TEXT + "; font-size: 11px;"
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.content_label = QLabel("")
        self.content_label.setStyleSheet(
            "color: " + PRIMARY_TEXT + "; font-size: 10px;"
        )
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.content_label)

    def update_view(self, result):
        """result can be DocumentResult or a dict-like."""

        if not hasattr(result, "kind"):
            # dict-like
            kind = getattr(result, "kind", "unknown")
            renderer = getattr(result, "renderer", "unknown")
            support = getattr(result, "support", "L?")
            content = getattr(result, "content", None)
            metadata = getattr(result, "metadata", {})
            warnings = getattr(result, "warnings", [])
        else:
            kind = result.kind
            renderer = result.renderer
            support = result.support
            content = result.content
            metadata = result.metadata
            warnings = result.warnings

        # Kind badge
        kind_labels = {
            "text": "Texto",
            "pdf": "PDF",
            "docx": "DOCX",
            "xlsx": "XLSX",
            "archive": "Arquivo",
            "unknown": "Desconhecido",
        }
        kind_name = kind_labels.get(kind, kind.upper() if kind else "—")

        self.kind_label.setText(
            kind_name + " • " + renderer + " • Nível " + support
        )

        # Info (size, strings, etc.)
        if kind == "unknown":
            entropy = (
                metadata.get("entropy", "?") if metadata else "?"
            )
            strings_count = (
                metadata.get("string_count", 0) if metadata else 0
            )
            self.info_label.setText(
                "Entropia: " + str(entropy) + " | Strings encontradas: " + str(strings_count)
            )
        elif kind == "archive":
            entry_count = (
                metadata.get("entry_count", 0) if metadata else 0
            )
            self.info_label.setText(
                "Arquivo compactado: " + str(entry_count) + " entradas"
            )
        else:
            self.info_label.setText("")

        # Content preview
        if content is not None:
            c = str(content)
            if len(c) > 600:
                c = c[:600] + "..."
            self.content_label.setText(c)
        else:
            self.content_label.setText("(nenhum conteúdo disponível)")


class MainWindow(QMainWindow):
    """Main OpenDocs window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenDocs")
        self.resize(1000, 720)
        self.setMinimumSize(800, 600)

        # Theme
        apply_palette(self)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────────────────
        top_bar = QFrame()
        top_bar.setFixedHeight(36)
        top_bar.setStyleSheet(
            style_str(
                "QFrame {",
                "background: " + SURFACE_ELEVATED + ";",
                "border-bottom: 1px solid " + BORDER_COLOR + ";",
                "}"
            )
        )
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(12, 4, 12, 4)

        # App name / logo area
        self.logo_label = QLabel("◇ OpenDocs")
        self.logo_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.logo_label.setStyleSheet("color: " + PRIMARY_TEXT + ";")
        top_bar_layout.addWidget(self.logo_label)

        # Window controls (minimize, maximize, close)
        for btn_text, btn_role in [("—", "minimize"), ("□", "maximize"), ("×", "close")]:
            btn = QPushButton(btn_text)
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(
                style_str(
                    "QPushButton {",
                    "color: " + SECONDARY_TEXT + ";",
                    "background: transparent;",
                    "border: none;",
                    "font-size: 14px;",
                    "font-weight: bold;",
                    "}",
                    "QPushButton:hover {",
                    "color: " + PRIMARY_TEXT + ";",
                    "background: " + SURFACE_COLOR + ";",
                    "border-radius: 4px;",
                    "}",
                    'QPushButton[role="close"]:hover {',
                    "color: #ff5f57;",
                    "}",
                )
            )
            btn.setProperty("role", btn_role)
            if btn_role == "close":
                btn.clicked.connect(self.close)
            elif btn_role == "maximize":
                btn.clicked.connect(
                    self.showMaximized
                    if not self.isMaximized()
                    else self.showNormal
                )
            elif btn_role == "minimize":
                btn.clicked.connect(self.showMinimized)
            top_bar_layout.addWidget(btn)

        top_bar_layout.addStretch()
        root_layout.addWidget(top_bar)

        # ── Main content area ───────────────────────────────────────────
        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background: " + BG_COLOR + ";")
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ── Drop area ──────────────────────────────────────────────────
        self.drop_area = DropArea(
            "Arrastre um arquivo aqui\nou use o menu Arquivo → Abrir"
        )
        self.drop_area.setProperty("dropped_paths", [])
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setMinimumHeight(200)
        self.drop_area.setStyleSheet(
            style_str(
                "QLabel {",
                "color: " + SECONDARY_TEXT + ";",
                "background: " + SURFACE_ELEVATED + ";",
                "border: 2px dashed " + BORDER_COLOR + ";",
                "border-radius: 8px;",
                "font-size: 13px;",
                "font-weight: 500;",
                "}",
                "QLabel:hover {",
                "border-color: " + ACCENT + ";",
                "background: rgba(110, 140, 255, 0.08);",
                "}",
            )
        )
        apply_palette(self.drop_area)
        self.drop_area.setAcceptDrops(True)
        self.drop_area.setMouseTracking(True)

        content_layout.addWidget(self.drop_area)

        # ── Document area ───────────────────────────────────────────────
        self.preview = DocumentPreview()
        content_layout.addWidget(self.preview, 1)

        root_layout.addWidget(content_wrapper, 1)

        # ── Status bar ──────────────────────────────────────────────────
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(
            "background: " + SURFACE_ELEVATED + "; color: " + SECONDARY_TEXT + ";"
        )
        self.status_bar.showMessage("Pronto — solte um arquivo para abrir")

        # Internal state
        self.current_result = None

    # ── Drag & drop handling ────────────────────────────────────────────
    def _on_files_dropped(self):
        # Read the dropped paths from the drop area's property
        paths = self.drop_area.property("dropped_paths")
        if paths:
            self.open_file(paths[0])

    def open_file(self, path):
        """Open a file and display its preview."""
        from readers import open_document, support_level_name

        result = open_document(path)
        self.current_result = result

        # Update UI
        self.preview.update_view(result)

        # Status
        import os
        fname = os.path.basename(path)
        support_name = support_level_name(
            getattr(result, "support", "L?")
        )
        self.status_bar.showMessage("Aberto: " + fname + " — " + support_name)

        # Set window title
        kind_labels = {
            "pdf": "PDF",
            "docx": "DOCX",
            "xlsx": "XLSX",
            "unknown": "OpenDocs",
            "text": "Texto",
        }
        kind_name = kind_labels.get(
            result.kind if hasattr(result, "kind") else "unknown", "OpenDocs"
        )
        self.setWindowTitle("OpenDocs — " + kind_name + " • " + fname)

    def closeEvent(self, event):
        # Ensure clean exit
        self.current_result = None
        super().closeEvent(event)


# ── Allow running as `python -m opendocs.ui` ───────────────────────────────

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())