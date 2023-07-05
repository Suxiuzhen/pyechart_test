# This is a sample Python script.

from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QPushButton, QGridLayout
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QGuiApplication
import cv2
import sys
import shutil
import os
import random
import time


class MyLabel(QLabel):
    def __init__(self, parent=None):
        super(MyLabel, self).__init__(parent)
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.rect_list = []

    # 鼠标移动事件
    def mouseMoveEvent(self, event):
        # barHeight = self.bar.height()
        # if self.flag:
        self.x1 = event.pos().x()
        self.y1 = event.pos().y()
        self.update()

    # 鼠标释放事件
    def mouseReleaseEvent(self, event):
        print(self.x0, self.y0, self.x1, self.y1)
        self.rect_list.append([self.x0, self.y0, self.x1, self.y1])
        self.x0, self.y0, self.x1, self.y1 = (0, 0, 0, 0)
        print(self.x0, self.y0, self.x1, self.y1)

    # 绘制事件
    def paintEvent(self, event):
        super().paintEvent(event)
        # if self.flag and self.move:
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        painter.drawRect(QRect(self.x0, self.y0, abs(self.x1 - self.x0), abs(self.y1 - self.y0)))

        for rect in self.rect_list:
            rect = QRect(rect[0], rect[1], abs(rect[2] - rect[0]), abs(rect[3] - rect[1]))
            painter.drawRect(rect)
        # painter.end()
        # print(self.x0, self.y0, self.x1, self.y1)

    # 单击鼠标触发事件
    def mousePressEvent(self, event):
        # barHeight = self.bar.height()
        self.x0 = event.pos().x()
        self.y0 = event.pos().y()


# 测试类
class Test(QWidget):
    def __init__(self):
        super(Test, self).__init__()
        self.image_path = {
            0: 'images/10000.jpg',
            1: 'images/10001.jpg',
            2: 'images/10002.jpg',
        }
        self.image_id = 0
        self.initUI()


    def save_draw_image(self):
        # image = self.label.pixmap()
        # # print(image)
        # image.save('./aa.jpg')
        current_file_path = self.image_path[self.image_id]
        file_name = os.path.basename(current_file_path)
        base_name, mime = file_name.rsplit('.', 1)
        out_file_path = os.path.join('outer_images', f'{base_name}_{time.time()}.{mime}')
        shutil.copy(self.image_path[self.image_id], out_file_path)
        # cv2.imwrite('./outer_image/10000.jpg', image)
        image_byte_stream = cv2.imread(out_file_path)

        for rect_info in self.label.rect_list:
            x1 = rect_info[0]
            y1 = rect_info[1]
            x2 = rect_info[2]
            y2 = rect_info[3]
            image_byte_stream = cv2.rectangle(image_byte_stream, (x1, y1), (x2, y2), (0, 0, 255), 1)
        cv2.imwrite(out_file_path, image_byte_stream)

    def image_switch_up(self):
        self.label.rect_list = []
        self.image_id -= 1
        if self.image_id < 0:
            self.image_id = 2
        self.load_iamge(self.image_id)


    def image_switch_down(self):
        self.label.rect_list = []
        self.image_id += 1
        if self.image_id > 2:
            self.image_id = 0
        self.load_iamge(self.image_id)

    def load_iamge(self, image_id):
        img = cv2.imread(self.image_path[image_id])
        height, width, bytesPerComponent = img.shape
        bytesPerLine = 3 * width
        cv2.cvtColor(img, cv2.COLOR_BGR2RGB, img)
        QImg = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(QImg)
        self.label.setPixmap(pixmap)

    def initUI(self):
        self.resize(960, 540)
        self.setWindowTitle("图像切换和绘制矩形")
        # self.bar = QToolBar()
        # self.addToolBar(self.bar)
        grid = QGridLayout()
        # grid.setSpacing(15)


        self.label = MyLabel(self)  # 重定义的label
        self.load_iamge(0)

        self.label.setCursor(Qt.CrossCursor)
        self.button = QPushButton(self)
        self.button.setText('保存')
        # self.button.show()
        grid.addWidget(self.button, 0, 0)
        self.button1 = QPushButton(self)
        self.button1.setText('上一张')
        # self.button1.show()
        grid.addWidget(self.button1, 0, 1)
        self.button2 = QPushButton(self)
        self.button2.setText('下一张')
        # self.button2.show()
        grid.addWidget(self.button2, 0, 2)
        grid.addWidget(self.label, 1, 0, 1, 3)
        self.button.clicked.connect(self.save_draw_image)
        self.button1.clicked.connect(self.image_switch_up)
        self.button2.clicked.connect(self.image_switch_down)
        self.setLayout(grid)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = Test()
    test.show()
    sys.exit(app.exec())
