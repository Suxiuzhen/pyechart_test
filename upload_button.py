import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QPushButton, QScrollArea


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scrollable Layout")
        self.setGeometry(100, 100, 400, 300)

        self.num_images = 0

        # 创建主要布局管理器
        layout = QGridLayout()
        self.setLayout(layout)

        # 创建滚动区域
        scroll_area = QScrollArea(self)
        layout.addWidget(scroll_area, 0, 0)

        # 创建内容部件
        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)

        # 将内容部件设置为滚动区域的子部件
        scroll_area.setWidget(self.content_widget)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.create_labels()

        # 创建按钮并添加点击事件
        button = QPushButton("Update Labels")
        button.clicked.connect(self.update_labels)
        layout.addWidget(button, 1, 0)

    def create_labels(self):
        # 清空内容布局
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            self.content_layout.removeWidget(widget)
            widget.setParent(None)

        # 创建标签并添加到内容布局
        for i in range(self.num_images):
            label = QLabel(f"Image {i + 1}")
            self.content_layout.addWidget(label, i // 4, i % 4)

        # 重新设置内容部件的最小大小
        self.content_widget.setMinimumSize(self.content_layout.sizeHint())

    def update_labels(self):
        self.num_images += 1
        self.create_labels()
        self.content_widget.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
