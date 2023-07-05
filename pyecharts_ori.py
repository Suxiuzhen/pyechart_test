import sys
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt5.QtCore import QSize, QObject, QTimer
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.faker import Faker


class ChartObject(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart = None

    def setChart(self, chart):
        self.chart = chart


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("PyQt5 Layout Example")
        self.setGeometry(100, 100, 800, 600)

        # 创建布局容器
        layout = QtWidgets.QVBoxLayout()

        # 第一行布局
        row1_layout = QtWidgets.QHBoxLayout()
        combo1 = QtWidgets.QComboBox()
        combo1.addItem("Option 1")
        combo1.addItem("Option 2")
        combo2 = QtWidgets.QComboBox()
        combo2.addItem("Option A")
        combo2.addItem("Option B")
        time_picker = QtWidgets.QDateTimeEdit()
        time_picker.setDateTime(QtCore.QDateTime.currentDateTime())

        row1_layout.addWidget(combo1)
        row1_layout.addWidget(combo2)
        row1_layout.addWidget(time_picker)

        # 第二行布局
        self.row2_layout = QtWidgets.QGridLayout()
        # self.create_rectangle(self.row2_layout)

        # 将第一行和第二行布局添加到主布局容器中
        layout.addLayout(row1_layout)
        layout.addLayout(self.row2_layout)

        # 创建一个 QWidget 作为主窗口的中心部件
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.create_rectangle(self.row2_layout)

    def get_window_size(self):
        # 窗口尺寸变化时，获取当前窗口的宽度和高度
        width = self.width()
        height = self.height()
        print(f"Width: {width}, Height: {height}")

        return width/2.3, height/2.35

    def create_rectangle(self, gridLayout):
        # 创建四个格子，每个格子使用 QWebEngineView 显示 PyEcharts 生成的柱形图
        width, height = self.get_window_size()
        for i in range(2):
            for j in range(2):
                webview = QWebEngineView()
                gridLayout.addWidget(webview, i, j)

                # 使用 QWebChannel 进行通信
                channel = QWebChannel()
                webview.page().setWebChannel(channel)

                # 创建 PyEcharts 的柱形图实例

                chart = self.create_bar_chart(width, height)

                webview.setHtml(chart)

    def create_bar_chart(self, cell_width=600, cell_height=400):
        bar = (
            Bar()
            .add_xaxis(Faker.choose())
            .add_yaxis("Series 1", Faker.values(), category_gap="50%", bar_width=20)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="Bar Chart"),
                # toolbox_opts=opts.ToolboxOpts(),
                tooltip_opts=opts.TooltipOpts(
                    is_show=True, trigger="axis", axis_pointer_type="shadow"
                ),
            )
            .render_embed()
        )
        bar = bar.replace(
            'style="width:900px; height:500px; "',
            f'style="width:{cell_width}px; height:{cell_height}px; "'
        )
        return bar


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
