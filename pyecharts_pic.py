import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.faker import Faker
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot as driver


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
        row2_layout = QtWidgets.QGridLayout()

        # 创建四个柱形图
        chart1 = self.create_bar_chart()
        chart2 = self.create_bar_chart()
        chart3 = self.create_bar_chart()
        chart4 = self.create_bar_chart()

        # 创建图表容器，将图表渲染为图片
        chart_widget1 = self.create_chart_widget(chart1)
        chart_widget2 = self.create_chart_widget(chart2)
        chart_widget3 = self.create_chart_widget(chart3)
        chart_widget4 = self.create_chart_widget(chart4)

        # 设置每个格子的位置
        row2_layout.addWidget(chart_widget1, 0, 0)
        row2_layout.addWidget(chart_widget2, 0, 1)
        row2_layout.addWidget(chart_widget3, 1, 0)
        row2_layout.addWidget(chart_widget4, 1, 1)

        # 将第一行和第二行布局添加到主布局容器中
        layout.addLayout(row1_layout)
        layout.addLayout(row2_layout)

        # 创建一个 QWidget 作为主窗口的中心部件
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def create_bar_chart(self):
        bar = (
            Bar()
            .add_xaxis(Faker.choose())
            .add_yaxis("Series 1", Faker.values())
            .set_global_opts(
                title_opts=opts.TitleOpts(title="Bar Chart"),
                toolbox_opts=opts.ToolboxOpts(),
                tooltip_opts=opts.TooltipOpts(
                    is_show=True, trigger="axis", axis_pointer_type="shadow"
                ),
            )
        )

        return bar

    def create_chart_widget(self, chart):
        # 渲染图表为图片
        snapshot_path = "chart_snapshot.png"
        make_snapshot(driver, chart.render(), snapshot_path)

        # 创建 QLabel 并设置图片
        chart_widget = QtWidgets.QLabel()
        chart_widget.setPixmap(QtGui.QPixmap(snapshot_path).scaled(600, 400))

        return chart_widget


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
