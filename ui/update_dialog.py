from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
)
import webbrowser
import re


def clean_md(md: str) -> str:
    # bỏ ###, **bold**, ...
    text = re.sub(r"#+\s*", "", md)  # remove headings
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # bold
    return text.strip()


class UpdateDialog(QDialog):
    def __init__(self, current_version: str, updates: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cập nhật ứng dụng")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        lbl = QLabel(f"Phiên bản hiện tại: {current_version}")
        layout.addWidget(lbl)

        self.text = QTextEdit()
        self.text.setReadOnly(True)

        text_content = ""
        for v in updates:
            text_content += f"=== {v['version']} ===\n"
            text_content += f"{clean_md(v.get('changelog', '(không có log)'))}\n\n"
        self.text.setText(text_content.strip())
        layout.addWidget(self.text)

        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Đóng")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)

        self.btn_dl = QPushButton("Tải bản mới nhất")
        self.btn_dl.clicked.connect(lambda: self.download(updates[0]))
        btn_layout.addWidget(self.btn_dl)

        layout.addLayout(btn_layout)

    def download(self, latest: dict):
        url = latest.get("url")
        if url:
            webbrowser.open(url)
        self.accept()
