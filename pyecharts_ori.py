import sys
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.faker import Faker


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

        # 创建Pyecharts柱形图
        chart1 = self.create_bar_chart()
        chart2 = self.create_bar_chart()
        chart3 = self.create_bar_chart()
        chart4 = self.create_bar_chart()

        # 将每个格子的HTML代码放入QWebEngineView
        web_view1 = QtWebEngineWidgets.QWebEngineView()
        web_view1.setHtml(chart1)
        web_view2 = QtWebEngineWidgets.QWebEngineView()
        web_view2.setHtml(chart2)
        web_view3 = QtWebEngineWidgets.QWebEngineView()
        web_view3.setHtml(chart3)
        web_view4 = QtWebEngineWidgets.QWebEngineView()
        web_view4.setHtml(chart4)

        # 设置每个格子的位置
        row2_layout.addWidget(web_view1, 0, 0)
        # row2_layout.addWidget(web_view2, 0, 1)
        # row2_layout.addWidget(web_view3, 1, 0)
        # row2_layout.addWidget(web_view4, 1, 1)

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
            .add_yaxis("Series 1", Faker.values(), category_gap="50%", bar_width=20)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="Bar Chart"),
                # toolbox_opts=opts.ToolboxOpts(),
                tooltip_opts=opts.TooltipOpts(
                    is_show=True, trigger="axis", axis_pointer_type="shadow"
                ),
                yaxis_opts=opts.AxisOpts(
                    interval=50,
                    max_interval=100,
                    max_=100
                )
                # graphic_opts=[opts.GraphicGroup(
                #     graphic_item=opts.GraphicItem(
                #         left="10%", top="10%", z=100, bounding="raw", is_ignore=False
                #     ),
                #     children=[
                #         opts.GraphicRect(
                #             graphic_item=opts.GraphicItem(left="center", top="center"),
                #             graphic_shape_opts=opts.GraphicShapeOpts(width=600, height=400),
                #         )
                #     ],
                # )],
            )
            .render_embed()
        )

        return bar


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
