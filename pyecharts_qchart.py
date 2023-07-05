import sys
from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QDateTimeEdit, QGridLayout
from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis
from PyQt5.QtCore import Qt, QDateTime

class BarChartWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # 创建下拉框和时间选择器
        combo1 = QComboBox()
        combo1.addItems(["Option 1", "Option 2", "Option 3"])

        combo2 = QComboBox()
        combo2.addItems(["Option A", "Option B", "Option C"])

        dateTimeEdit = QDateTimeEdit()
        dateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        dateTimeEdit.setDateTime(QDateTime.currentDateTime())

        # 创建柱形图数据集
        barset1 = QBarSet("Bar Set 1")
        barset1.append([1, 2, 3])

        barset2 = QBarSet("Bar Set 2")
        barset2.append([4, 5, 6])

        barset3 = QBarSet("Bar Set 3")
        barset3.append([7, 8, 9])

        # 创建柱形系列并添加数据集
        series = QBarSeries()
        series.append(barset1)
        series.append(barset2)
        series.append(barset3)

        # 创建柱形图
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Bar Chart")

        axis = QBarCategoryAxis()
        axis.append(["Category 1", "Category 2", "Category 3"])
        chart.createDefaultAxes()
        chart.setAxisX(axis, series)

        chartView = QChartView(chart)

        # 创建网格布局
        gridLayout = QGridLayout()

        # 添加柱形图到网格布局中的四个格子
        gridLayout.addWidget(chartView, 0, 0)
        gridLayout.addWidget(chartView, 0, 1)
        gridLayout.addWidget(chartView, 1, 0)
        gridLayout.addWidget(chartView, 1, 1)

        # 创建主布局
        mainLayout = QGridLayout()
        mainLayout.addWidget(combo1, 0, 0)
        mainLayout.addWidget(combo2, 0, 1)
        mainLayout.addWidget(dateTimeEdit, 0, 2)
        mainLayout.addLayout(gridLayout, 1, 0, 1, 3)

        self.setLayout(mainLayout)
        self.setWindowTitle("Bar Chart Widget")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = BarChartWidget()
    widget.show()
    sys.exit(app.exec_())
