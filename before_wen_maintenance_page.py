# -*- coding:utf-8 -*-

import json
import sys
import time
from datetime import datetime
from typing import cast

import cv2
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QPixmap, QResizeEvent, QMouseEvent, QCloseEvent, QIcon, QColor, QFont, QPalette
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout, QGridLayout, QLabel, QPushButton, QSpacerItem, \
    QSizePolicy, QVBoxLayout, QTableWidget, QFrame, QAbstractItemView, QTableWidgetItem, QMessageBox, \
    QDialog, QTabWidget, QHeaderView, QStackedWidget, QLineEdit
import numpy as np

from general.commonhelper import CommonHelper

from api.config import CONSTANT
from api.maintenance.maintenance_task import MaintenanceTaskCrud, DlDefectModel, \
    ManualDefectModel, RECHECKED_STATE_MAP, MainProductListModel
from api.dict_info_manager import DictInfoCRUD
from general.message import InformationMessageBox, CriticalMessageBoxOne, WarningMessageBoxOne
from general.minio_util import MinioClient, Bucket
from general.mylog import logger

from widgets.add_repair_record import AddRepairRecordWidget
from widgets.add_scrap_record import AddScrapRecordWidget
from widgets.hover_label import OptionLabel
from widgets.plugins.canvas.shape import Shape
from widgets.maintenance.main_qtitle import QTitle
from widgets.recheck.panel_product_detail import ProductDetailPanel
from widgets.defect_info_btn import *
from widgets.series_recheck.cruds.class_info import retrive_class_color_info, ProductTypeEnum
from widgets.statistics.components.asyn_thread import AsynThread


class MaintenanceWenPageWidget(QWidget):
    def __init__(self, status_bar_widget=None, parent=None,
                 mainwindow=None):
        """
            :param status_bar_widget: 状态栏控件控件
            :param parent:  父级元素
            """
        # 设置窗口
        super().__init__(parent=parent)
        self.setFocusPolicy(Qt.ClickFocus)
        self._reverse_position = False  # new-2022-03-04 入口：反转标尺
        self.ui = UI_BeforeWenMainPageWidget(self)
        self.showMaximized()
        styleFile = 'qss/maintenance_page.qss'
        qssStyle = CommonHelper.readQss(styleFile)
        self.setStyleSheet(qssStyle)
        # 处理参数 并 定义属性
        self.mainwindow = mainwindow
        self.status_bar_widget = status_bar_widget
        self.detect_task_id = 0
        self.task_info = None
        self.current_product_spec = None  # 初始规格
        self.maintenance_list_current_index = -1  # 维修列表当前选中行
        self.cruds = MaintenanceTaskCrud()  # 查询数据库的对象
        self.thread_new_recheck_products = None  # 用于查询新维修产品列表的线程
        self.split_screen_canvas = None  # 当前 分屏的 canvas 对象名

        self.map_product_index = {}  # {product_id:row_index} 的 map
        self.main_widget_reverse = CONSTANT.get("main_widget_reverse", 0)
        self.flag_changed_defects = False  # 是否改变了产品的人工缺陷列表
        self.current_product_ids = []  # 用户点击过哪些产品
        self.GG_MAP = DictInfoCRUD.get_all_gg_enum()

        self.class_color_map = {}

        self.downsampling_ratio = CONSTANT.get("downsampling_ratio_maintenance", None)

        # 调用的控件
        self.add_repair_record_widget = AddRepairRecordWidget(0, 0)
        self.add_scrap_record_widget = AddScrapRecordWidget(0, 0)

        self._reverse_position_h = False
        self._reverse_position_v = False

        # 绑定事件
        self.bind_event()

    def bind_event(self):
        """ 初始化绑定事件方法 """
        try:
            # 父级 stackWidget 容器切换，里改改界面的事件
            self.parent().currentChanged.connect(self.slot_leave_this_page)

        except Exception as e:
            logger.error(e, exc_info=True)

    def init_data(self):
        """ 初始化数据
        将界面所有的数据置为初始状态
        """
        pass

    def load_data(self, task_info, p_status="NG-待维修"):
        """ 加载数据
        :param task_info: 检测任务信息，MaintenanceListModel
        :param p_status: 过滤的产品信息
        """
        try:
            # 查询维修任务中产品列表
            self.task_info = task_info
            self.detect_task_id = task_info.task_id
            # fixme: 清空列表数据
            self.ui.q_board.init_attr()
            self.map_product_index = {}

            self.req_main_product_list(self.detect_task_id, p_status)

        except Exception as e:
            logger.error(e)

    def req_main_product_list(self, task_id, p_status):
        """ 查询 ng 产品列表
        :param task_id: 检测任务ID
        :return: 返回维修的数据
        """
        # ToDo: 已经存在的 PRODUCT_ID 应该排除在外
        try:
            logger.info(f"检测任务<{task_id}>正在运行，定时获取最新的维修产品信息")
            if self.thread_new_recheck_products is not None:
                self.thread_new_recheck_products.terminate()
                self.thread_new_recheck_products = None
            self.thread_new_recheck_products = ReqMaintenanceProductThread(task_id, p_status, self.ui.scan_lineEdit,
                                                                           reverse_position=self._reverse_position)
            # 绑定信号
            self.thread_new_recheck_products.signal_new_recheck_products.connect(self.action_change_checked_product)
            # self.thread_new_recheck_products.signal_scanner_code_in_exist_data.connect(self.slot_scanner_code_chosed)
            self.thread_new_recheck_products.signal_new_recheck_products_error.connect(
                self.slot_new_recheck_products_error)
            self.thread_new_recheck_products.signal_scanner_code_not_in_exist_data_error.connect(
                self.slot_scanner_code_not_in_exist_data_error)
            # ToDo tips：这里运行，要在界面关闭，或者在界面被切换掉之前，关掉线程
            self.thread_new_recheck_products.start()
        except Exception as e:
            logger.error(e)

    def action_change_checked_product(self, row_data, scan_code, scan_action=False):
        """ 维修列表修改选中行事件
        :param row: 行索引, 扫码枪模式为None
        :param scan_code: 扫入组件码, 扫码枪模式为str
        :param scan_action: 是否扫码枪触发
        :return:
        """
        try:

            # TODO QT的默认样式，单机选择之后表头变黑
            row_model: MainProductListModel
            if not row_data:
                return
            if scan_action:  # 如果是扫码枪进入该页面，则选中行要变更
                scan_code = scan_code.upper()
                # 将扫码枪输入组件码的分支移到这里处理，是因为偶现组件码和图像对不上号的bug by charlie 2020/11/05
                # products_map = {d.PRODUCT_CODE.upper(): (i, d) for i, d in
                #                 enumerate(self.ui.maintenance_list.q_table_product.data)}
                row, row_model = 0, row_data[0]
                if row is None:  # 理论上这个分支应该进不来，因为在线程里面已经判断过一次组件码是否在产品列表 by charlie
                    logger.error(f"维修产品列表中无此组件码:{scan_code}")
                    return
            else:
                row_model = row_data[0]
            # self.ui.maintenance_list.tab_pannel.setCurrentIndex(1)  # 默认是选中人工检测tab页面
            # self.ui.product_code_copy_btn.update_data(data=row_model.PRODUCT_CODE)
            _len_data_ = len(row_data)

            if row_model.PRODUCT_ID not in self.current_product_ids:
                self.current_product_ids.append(row_model.PRODUCT_ID)
                if self.thread_new_recheck_products:  # 传给更新数据线程
                    self.thread_new_recheck_products.current_product_ids = self.current_product_ids

            pro_type_str = "单晶"
            if row_model.PRO_TYPE == 2:
                pro_type_str = "多晶"
            pro_spec = self.get_gg_shape(row_model.GG, to_str=True)
            self.ui.panel_product_detail.load_data(
                row_model.PRO_LINE_NAME,
                self.task_info.detect_sites,
                self.task_info.task_name,
                pro_type_str + pro_spec,
                self.task_info.d_set_name
            )

            # ToDo tips: 状态栏显示图片信息
            if self.status_bar_widget is not None:
                self.status_bar_widget = cast(QLabel, self.status_bar_widget)
                try:
                    w_code = "{} {}".format(row_model.WELDING_CODE,
                                            row_model.WELDING_NAME) if row_model.WELDING_CODE is not None else "未知"
                    self.status_bar_widget.setText(f"产品信息:产品编码({row_model.PRODUCT_CODE}); 串焊机: {w_code}")
                except Exception as error:
                    self.status_bar_widget.setText(f"产品信息:产品编码({row_model.PRODUCT_CODE}); 串焊机: 未知")

            manual_el_defects_data = []
            manual_vi_defects_data = []
            manual_vi_back_defects_data = []

            # 2023-02-22 通过产线区分复检界面的横向和纵向标尺是需要反转
            product_line_id = row_model.PRO_LINE_ID
            reverse_position_h = CONSTANT.get(f'{product_line_id}_reverse_position_h', False)
            reverse_position_v = CONSTANT.get(f'{product_line_id}_reverse_position_v', False)
            logger.info(
                f'层前维修产线:{product_line_id}:横向标尺需要反转:{reverse_position_h}:纵向标尺需要反转:{reverse_position_v}')
            self._reverse_position_h = reverse_position_h
            self._reverse_position_v = reverse_position_v

            if row_model.MANUAL_EL_DEFECTS or row_model.MANUAL_VI_DEFECTS or row_model.MANUAL_VI_BACK_DEFECTS:
                product_spec = self.get_gg_shape(row_model.GG)

                for d in row_model.MANUAL_EL_DEFECTS:
                    defect_pos = self.get_mes_defect_pos(eval(d.POSITION), product_spec, row_model.reverse_position,
                                                         reverse_position_h=reverse_position_h,
                                                         reverse_position_v=reverse_position_v)
                    model = [d.LAB_CLASS_NAME, d.LAB_CLASS_NAME, defect_pos]
                    manual_el_defects_data.append(model)

                for d in row_model.MANUAL_VI_DEFECTS:
                    defect_pos = self.get_mes_defect_pos(eval(d.POSITION), product_spec, row_model.reverse_position,
                                                         reverse_position_h=reverse_position_h,
                                                         reverse_position_v=reverse_position_v)
                    model = [d.LAB_CLASS_NAME, d.LAB_CLASS_NAME, defect_pos]

                    manual_vi_defects_data.append(model)

                # 增加VI背面 2022/11/28
                for d in row_model.MANUAL_VI_BACK_DEFECTS:
                    defect_pos = self.get_mes_defect_pos(eval(d.POSITION), product_spec, row_model.reverse_position,
                                                         reverse_position_h=reverse_position_h,
                                                         reverse_position_v=reverse_position_v)
                    model = [d.LAB_CLASS_NAME, d.LAB_CLASS_NAME, defect_pos]
                    manual_vi_back_defects_data.append(model)

            self.ui.canvas.label_el.clear()
            self.ui.canvas.label_vi.clear()
            self.ui.canvas.label_vi_back.clear()

            # 更新 lable 添加缺陷信息
            # TODO
            el_text = f'EL_缺陷:       {";    ".join(["_".join([str(qx[2]), str(qx[0])]) for qx in manual_el_defects_data])}'
            vi_text = f'VI_缺陷:       {";    ".join(["_".join([str(qx[2]), str(qx[0])]) for qx in manual_vi_defects_data])}'
            vi_back_text = f'VI_背面_缺陷:       {";    ".join(["_".join([str(qx[2]), str(qx[0])]) for qx in manual_vi_back_defects_data])}'
            self.ui.canvas.label_el.setText(el_text)
            self.ui.canvas.label_vi.setText(vi_text)
            self.ui.canvas.label_vi_back.setText(vi_back_text)

            # ToDo tips: 统计信息更新
            statistics_el_defects_num = len(manual_el_defects_data)
            statistics_vi_defects_num = len(manual_vi_defects_data)
            statistics_defects_num = statistics_el_defects_num + statistics_vi_defects_num
            detect_res = "NG-维修"
            if row_model.D_RESULT == 2:
                detect_res = "NG-报废"
            self.ui.q_board.q_label_10.setText(str(statistics_defects_num))
            self.ui.q_board.q_label_11.setText(str(statistics_el_defects_num))
            self.ui.q_board.q_label_12.setText(str(statistics_vi_defects_num))
            self.ui.q_board.q_label_13.setText(detect_res)

            # fixme 20200507: 所有的都好了，修改当前选择行

        except Exception as e:
            logger.error(e, exc_info=True)

    def get_gg_shape(self, gg_enum, to_str=False):
        try:
            if gg_enum not in self.GG_MAP.keys():
                self.GG_MAP = DictInfoCRUD.get_all_gg_enum()
            value = self.GG_MAP[gg_enum]
            return "*".join(map(str, list(value))) if to_str else value
        except Exception as e:
            logger.error(e)

    def slot_new_recheck_products_error(self, error):
        """ 查询维修产品列表出错信号处理方法 """
        CriticalMessageBoxOne(str(error))

    def slot_scanner_code_not_in_exist_data_error(self, warning):
        """ 扫码枪获取的product_id不在维修产品列表中的信号处理方法 """
        WarningMessageBoxOne(str(warning))

    def closeEvent(self, event: QCloseEvent):
        """ 关闭该窗口 """
        super().closeEvent(event)
        self.slot_leave_this_page(-1)

    def slot_leave_this_page(self, index):
        """ 父级 stackWidget 容器离开该界面的事件 """
        try:
            # 删除线程
            if index != self.parent().MaintenanceWenPageWidget_index:
                # 说明不是当前页面
                # 退出线程
                if self.thread_new_recheck_products:
                    logger.info("退出获取最新维修产品线程")
                    self.thread_new_recheck_products.terminate()
                    self.thread_new_recheck_products = None

                # 清空 canvas 的图片
                self.ui.canvas.label_el.clear()
                self.ui.canvas.label_vi.clear()
                self.ui.canvas.label_vi_back.clear()
            else:
                # 清空产品信息
                self.ui.panel_product_detail.clear()
        except Exception as e:
            logger.error(e, exc_info=True)

    def get_mes_defect_pos(self, db_position, product_spec: tuple, reverse_position,
                           reverse_position_h=False, reverse_position_v=False):
        """ 获取从数据库POSITION字段的缺陷转化为在MES上报的缺陷
        :param db_position: 缺陷位置,如[2, 11]
        :param product_spec: 产品规格:如(6, 22)
        :param reverse_position: 是否反转电池片位置
        :param reverse_position_h: 是否反转标尺 横向标尺
        :param reverse_position_v: 是否反转标尺 纵向标尺
        :return: A11
        """
        pos = db_position

        # 横向和纵向标尺都需要反转
        row, column = product_spec
        if reverse_position_h and reverse_position_v:
            pos_str = chr(65 + row - pos[0]) + str(column - pos[1] + 1)
        # 横向标尺需要反转
        elif reverse_position_h is True and reverse_position_v is False:
            pos_str = chr(4 + pos[0]) + str(column - pos[1] + 1)
        # 纵向标尺需要反转
        elif reverse_position_h is False and reverse_position_v is True:
            pos_str = chr(65 + row - pos[0]) + str(pos[1])
        # 无需反转
        else:
            pos_str = chr(64 + pos[0]) + str(pos[1])
        return pos_str


class UI_BeforeWenMainPageWidget(object):
    def __init__(self, parent):
        # 窗口设置
        layout = QVBoxLayout(parent)

        # 添加控件
        layout_1 = QHBoxLayout()
        self.q_board = ShowBoardWidget(parent)
        self.q_board.setObjectName("q_board")
        layout_1.addWidget(self.q_board)

        # ：：添加弹簧布局
        layout_1.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # TODO Done 20200905: 添加产品详情面板 和 任务列表按钮
        self.panel_product_detail = ProductDetailPanel(parent)
        self.panel_product_detail.setObjectName("panel_product_detail")
        layout_1.addWidget(self.panel_product_detail)

        btn_frame = QFrame(parent=parent)
        btn_frame.setMaximumHeight(71)
        btn_frame.setObjectName("btn_frame")
        layout_btn_frame = QHBoxLayout(btn_frame)
        layout_btn_frame.setContentsMargins(0, 0, 0, 0)

        # ：：添加弹簧布局
        layout_btn_frame.addItem(QSpacerItem(35, 1, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # 添加文本框
        self.scan_label = QLabel("扫码枪:")
        self.scan_lineEdit = QLineEdit()
        self.scan_lineEdit.setObjectName('scan_lineEdit')
        self.scan_lineEdit.setPlaceholderText("请将鼠标移至此处")
        layout_btn_frame.addWidget(self.scan_label)
        layout_btn_frame.addWidget(self.scan_lineEdit)

        # ：：添加弹簧布局
        layout_btn_frame.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout_1.addWidget(btn_frame)
        layout.addLayout(layout_1)

        layout_2 = QHBoxLayout()
        self.canvas = ImageWidget(parent)
        layout_2.addWidget(self.canvas)

        layout.addLayout(layout_2)


class QCenterLabel(QLabel):
    def __init__(self, *args):
        super().__init__(*args)
        self.setAlignment(Qt.AlignCenter)


class QTitleLabel(QLabel):
    def __init__(self, *args):
        super().__init__(*args)


""" ========================= 继承的基础类 start ================================ """


class QTableListWidget(QTableWidget):

    def __init__(self, *args):
        super().__init__(*args)
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.resizeColumnsToContents()
        # 选中表头不高亮
        self.horizontalHeader().setHighlightSections(False)
        # 取消行号
        self.verticalHeader().setHidden(True)
        # 设置不能编辑
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 单行模式选择
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        # 垂直滚动条按项移动
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)

        # 数据
        self.prev_index = -1
        self.current_index = -1
        self.data = []

    def set_column_width(self, index, width):
        """ 指定列宽 """
        # 对第0列单独设置固定宽度
        self.horizontalHeader().setSectionResizeMode(index, QHeaderView.Fixed)
        # 设置固定宽度
        self.setColumnWidth(index, width)

    def add_row(self, row_data):
        """ 添加单行数据 """
        self.data.append(row_data)
        self.update(append=[row_data])

    def del_row(self, row_index):
        """ 删除单行数据 """
        self.data.pop(row_index)
        self.update()

    def add_rows(self, rows_data):
        """ 添加多行数据 """
        self.data.extend(rows_data)
        self.update(append=rows_data)

    def reset_rows(self, rows_data):
        """ 重设表格数据 """
        self.data = rows_data
        self.update()

    def update(self, append=None):
        """ 更新数据 """
        if not append:
            append = []

        try:
            if append:
                # 是更新数据
                row = self.rowCount()
                new_rows = len(append)
                self.setRowCount(row + new_rows)
                rows_data = append
            else:
                # 重绘
                row = 0
                self.setRowCount(len(self.data))
                rows_data = self.data

            # 绘制表格
            self.draw_table(row, rows_data)
        except Exception as e:
            logger.error(e)

    def draw_table(self, new_row_index, rows_data):
        """
        :param new_row_index: 新添加首行的行索引
        :param rows_data: 数据列表，[QTableListWidgetModel, ]
        :return:
        """
        raise NotImplementedError()

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        pos = event.pos()
        item = self.indexAt(pos)
        self.current_index = item.row()

    def autosize(self):
        widths = [0 for _ in self.headers]
        height = self.horizontalHeader().height()
        # 计算每一列的最小尺寸
        for r, row in enumerate(self.dataframe):
            height += self.rowHeight(r)
            for c, col in enumerate(row):
                w = self.calculate_minsize(col)
                if w > widths[c]:
                    widths[c] = w
                    self.set_column_width(c, w)

        width = sum(widths)
        self.resize(QSize(width, height))

    def calculate_minsize(self, text):
        word_size = self.fontInfo().pixelSize()
        # fixme 20200611: 统计长度的时候，中文和 英文占位不同
        text_len = 4 * word_size  # 多个字的宽度作为缓冲
        for s in text:
            if ord(s) < 128:
                text_len += word_size * 1 / 2
            else:
                text_len += word_size * 1

        return text_len


class QTableListWidgetModel(object):
    def __init__(self, data=None):
        self.data = data if data else []
        self.MODIFIED = False  # 此数据是否修改


""" ========================= 继承的基础类 end ================================ """


class RecheckProductList(QTableListWidget):
    signal_add_data = pyqtSignal(int)  # 添加数据的信号（参数添加的行数）

    def add_rows(self, rows_data):
        """ 添加多行数据 """
        super().add_rows(rows_data)
        self.signal_add_data.emit(len(rows_data))
        self.setMouseTracking(True)

    def del_row(self, row_index):
        """ 删除一行数据 """
        super().del_row(row_index)

    def draw_table(self, new_row_index, rows_data):
        try:
            for i, row_data in enumerate(rows_data):
                _row_data = row_data.data[:]
                _row_data.insert(0, str(new_row_index + i + 1))
                for col, data in enumerate(_row_data):
                    # 每个一单元格
                    q_table_item = QTableWidgetItem()
                    q_table_item.setToolTip(str(data))
                    q_table_item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                    # 填充
                    q_table_item.setText(str(data))
                    if col == 2:
                        if str(data) == "OK":
                            q_table_item.setForeground(Qt.green)
                        else:
                            q_table_item.setForeground(Qt.red)
                    self.setItem(new_row_index + i, col, q_table_item)
                    # 20201104: 经过讨论分析，不需要再维修界面做维修记录查询的功能
                    # if col == 4 and str(data) == "已维修":
                    #     self.setCellWidget(new_row_index + i, col, self.btn_for_label(str(data), row_data.PRODUCT_ID, row_data.PRODUCT_CODE))
                    # else:
                    #     q_table_item.setText(str(data))
                    #     self.setItem(new_row_index + i, col, q_table_item)
        except Exception as e:
            logger.error(e)

    def update_row(self, row_index):
        """ 更新一行的方法 """
        try:
            row_data = self.data[row_index].data
            _row_data = row_data[:]
            _row_data.insert(0, str(row_index + 1))
            for col, data in enumerate(_row_data):
                # 每个一单元格
                q_table_item = QTableWidgetItem()
                q_table_item.setToolTip(str(data))
                q_table_item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                # 填充
                q_table_item.setText(str(data))
                self.setItem(row_index, col, q_table_item)
                # if col == 4: #  and str(data) == "人工-已维修"
                #     self.setCellWidget(row_index + 1, col, self.btn_for_label(str(data), row_data.PRODUCT_ID, row_data.PRODUCT_CODE))
                # else:
                #     q_table_item.setText(str(data))
                #     self.setItem(row_index + 1, col, q_table_item)
        except Exception as e:
            logger.error(e)

    def btn_for_label(self, vlaue, product_id, product_code):
        try:
            operation_column_btn_widget = QWidget()
            operation_column_btn_widget.setStyleSheet("""
                background-color: none;
            """)
            layOut = QHBoxLayout(operation_column_btn_widget)
            label = OptionLabel(parent=self, widget=OptionBtnWidget(product_id, product_code))
            label.setText(vlaue)
            label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            layOut.addWidget(label)  # 开始-按钮
            layOut.setContentsMargins(0, 0, 0, 0)
            layOut.setSpacing(2)
            return operation_column_btn_widget
        except Exception as e:
            logger.error(e, exc_info=True)


class DlDefects(QTableListWidget):

    def __init__(self, *args):
        super().__init__(*args)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def draw_table(self, new_row_index, rows_data):
        try:
            for i, row_data in enumerate(rows_data):
                _row_data = row_data.data[:]
                _row_data.insert(0, str(new_row_index + i + 1))
                for col, data in enumerate(_row_data):
                    # 每个一单元格
                    q_table_item = QTableWidgetItem()
                    q_table_item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                    # 填充
                    q_table_item.setText(str(data))
                    q_table_item.setToolTip(str(data))
                    self.setItem(new_row_index + i, col, q_table_item)
        except Exception as e:
            logger.error(e)


class ManualDefects(QTableListWidget):
    """ 人工缺陷 """
    signal_del_row = pyqtSignal(int, str)  # 删除一行的信号，（index，{附加信息}）
    signal_add_rows = pyqtSignal(int, dict)  # 添加行的信号，(row_count, {附加信息})

    def __init__(self, *args):
        super().__init__(*args)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def draw_table(self, new_row_index, rows_data):
        try:
            for i, row_data in enumerate(rows_data):
                _row_data = row_data.data[:]
                _row_data.insert(0, str(new_row_index + i + 1))
                # _row_data.append("删除")
                for col, data in enumerate(_row_data):
                    # 每个一单元格
                    q_table_item = QTableWidgetItem()
                    q_table_item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                    if col == 4:
                        # 操作栏自定义
                        q_btn_del = QPushButton(str(data), self)
                        q_btn_del.clicked.connect(self.delete_row(new_row_index + i))
                        q_btn_del.setCursor(Qt.PointingHandCursor)
                        self.setCellWidget(new_row_index + i, col, q_btn_del)
                    else:
                        q_table_item.setText(str(data))
                        q_table_item.setToolTip(str(data))
                        self.setItem(new_row_index + i, col, q_table_item)
        except Exception as e:
            logger.error(e)

    def delete_row(self, row_index):
        """ 点击删除按钮 """

        def wrapper():
            if hasattr(self.data[row_index], 'SHAPE'):
                self.signal_del_row.emit(row_index, self.data[row_index].SHAPE_UUID)  # 发送信号
            else:
                self.signal_del_row.emit(row_index, '')  # 发送信号

        return wrapper


class ShowBoardWidget(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QGridLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        # self.setMaximumWidth(71)
        self.setMaximumHeight(71)
        # 标题
        layout.addWidget(QCenterLabel("缺陷数量"), 0, 0)
        layout.addWidget(QCenterLabel("EL缺陷数"), 0, 1)
        layout.addWidget(QCenterLabel("VI缺陷数"), 0, 2)
        layout.addWidget(QCenterLabel("检测结果"), 0, 3)

        self.q_label_10 = QCenterLabel("0")
        self.q_label_10.setObjectName("q_label_10")
        layout.addWidget(self.q_label_10, 1, 0)
        self.q_label_11 = QCenterLabel("0")
        self.q_label_11.setObjectName("q_label_11")
        layout.addWidget(self.q_label_11, 1, 1)
        self.q_label_12 = QCenterLabel("0")
        self.q_label_12.setObjectName("q_label_12")
        layout.addWidget(self.q_label_12, 1, 2)
        self.q_label_13 = QCenterLabel("NG")
        self.q_label_13.setObjectName("q_label_13")
        layout.addWidget(self.q_label_13, 1, 3)

    def init_attr(self):
        self.q_label_10.setText("0")
        self.q_label_11.setText("0")
        self.q_label_12.setText("0")
        self.q_label_13.setText("NG")

class ImageWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 创建主要布局管理器
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # 设置整体背景颜色为白色
        self.setStyleSheet("background-color: white !important;")

        # 创建三个 QLabel，并添加到布局中
        self.label_el = MyLabel("你好")
        self.label_vi = MyLabel("你好")
        self.label_vi_back = MyLabel("你好")
        self.main_layout.addWidget(self.label_el)
        self.main_layout.addWidget(self.label_vi)
        self.main_layout.addWidget(self.label_vi_back)
        self.setStyleSheet("background-color: white;")

"""============================ Threads ======================================="""

class MyLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFont(QFont("Arial", 20))
        self.setStyleSheet("color: red; background-color: white;")
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setWordWrap(True)

class ReqMaintenanceProductThread(QThread):
    """ 单独线程去实时更新维修列表 """
    signal_new_recheck_products = pyqtSignal(list, str, bool)  # (查询的产品列表，是否是累加数据)
    signal_new_recheck_products_error = pyqtSignal(str)  # 查询产品失败的信号
    signal_scanner_code_in_exist_data = pyqtSignal(str)  # 扫码枪获取的product_code在拉取的数据列表之中，此时需要选中该产品
    signal_scanner_code_not_in_exist_data_error = pyqtSignal(str)  # 扫码枪获取的product_code不在拉取的数据列表之中(可能未复检)

    def __init__(self, task_id, p_status, scanner_edit, reverse_position=False):
        """
        :param task_id: 检测任务ID列表
        :param p_status: 过滤列表的表头
        :param reverse_position: 是否反转缺陷位

        20200905 更新策略：
        线程不再退出，如果没有

        退出该线程的两个条件：
        -- 1、检测任务不是正在检测的状态
        -- 界面被切换出去，

        """
        super().__init__()
        # 定义属性
        self.task_id = task_id
        self.stop = False
        # self.limit = 200  # 一次查询的数据量
        self.existed_product_ids = []  # 已存在列表中的产品CODE
        self.existed_product_codes = []  # 已存在列表中的产品CODE
        self.current_product_ids = []
        self.cruds = MaintenanceTaskCrud()  # 查询数据库的对象
        self.p_status = p_status
        self.undo_update_times = 0  # 计数器，未更新产品列表次数
        self.models = []
        self.new_models = []
        self.scanner_edit = scanner_edit
        self.first_time = True  # 首次进线程
        self.do_update_data = False  # 数据是否已增量更新
        self.scanner_id_got_in = False  # 是否收到扫码枪获取的产品id,且已在self.existed_product_ids中
        self.scanner_code = None

        self._reverse_position = reverse_position  # new-2022-01-10

    def run(self):
        """ 线程运行的方法 """
        # 根据检测任务ID，去查询新增的维修产品列表
        # 如果不让停止
        while not self.stop:
            try:
                product_list_refresh_time = CONSTANT.get("product_list_refresh_time", 10)
                scanner_code = self.get_scanner_code()  # 每次去获取扫码枪输入的组件码都睡0.5秒
                if scanner_code is None:  # 没有收到扫码枪的product_id
                    time.sleep(0.1)
                    continue
                else:  # 扫码枪已经获取到了scanner_code了
                    scanner_code = scanner_code.strip()
                    logger.info(f"从扫码枪获取的组件码为：======{scanner_code}")
                    self.scanner_code = upper_scanner_code = scanner_code.upper()
                    self.update_main_data()  # 重试一次增量拉取更新数据
                    # 发送信号表示扫码枪获取的product_id不在已拉取的existed_product_ids列表里面
                    existed_upper_product_codes = [p.upper() for p in self.existed_product_codes]
                    if upper_scanner_code in existed_upper_product_codes:
                        self.scanner_id_got_in = True
                    else:  # 发送信号表示扫码枪获取的product_id不在已拉取的existed_product_ids列表里面
                        warnning_mes = self.check_scanner_code(upper_scanner_code)
                        not self.stop and self.signal_scanner_code_not_in_exist_data_error.emit(warnning_mes)

                # 只要数据有更新，就要发送一次数据更新的信号
                # if self.do_update_data:  # 这里必然不是首次更新维修产品列表了，因为首次就会更新一次
                not self.stop and self.signal_new_recheck_products.emit(self.new_models, scanner_code,
                                                                            True)

            except Exception as e:
                logger.error(e, exc_info=True)

    def get_scanner_code(self):
        if self.stop:  # 如果要退出线程直接返回
            return
        res_code = None
        if len(self.scanner_edit.text()) > 0:
            res_code = self.scanner_edit.text()
        self.time_sleep_interval(0.5)
        if res_code:
            self.scanner_edit.setText("")
        return res_code

    def check_scanner_code(self, scan_code):
        import re
        if self.stop:  # 如果要退出线程直接返回
            return
        warnning_msg = f"当前扫码输入产品{scan_code}不在维修产品列表中。"
        try:
            vaild_code_pattern = r"(\d{4,}$)|(^[A-Za-z]\w{10,}$)"  # 正确的组件码当为四位以上纯数字或字母开头的11位以上字符串
            res = re.match(vaild_code_pattern, scan_code)
            if res is None:  # 非法组件码
                warnning_msg = f"{scan_code}为无效组件码，请检查系统输入法是否为英文。"
            else:
                # 合法组件码，需要去数据库查询改检测产品状态
                result, message = self.cruds.search_by_product_code_intask(scan_code, self.task_id)
                if result:
                    if result == "DangerousOK":
                        warnning_msg = f"当前扫码输入产品{scan_code}被{message}，产品流向出错。请立即停线并进行排查！如有不明请及时联系现场相关人员处理。"
                    elif result == "Error":  # 要是代码没Bug，应该走不到这个分支
                        warnning_msg = f"当前扫码输入产品{scan_code}未及时更新到维修产品列表中，请稍候两秒再试或联系相关人员解决。"
                        logger.error(f"产品{scan_code}未及时更新到维修产品列表中:========")
                    elif result == "UnCheck":  # 可能是未复检的产品
                        warnning_msg = f"当前扫码输入产品{scan_code}不在维修产品列表中，可能是未复检的产品。请排查原因！如有不明请及时联系现场相关人员处理。"
                        logger.error(f"产品{scan_code}可能是未复检的产品，但是流入了维修区。")
                else:  # 在任务里没有查到这个检测产品，在其他任务里面查一下
                    result = self.cruds.search_by_product_code_notintask(scan_code, self.task_id)
                    if result:
                        warnning_msg = f"当前扫码输入产品{scan_code}不在该任务中，请切换任务进行维修。可能的任务名：{result}。"
        except Exception as e:
            logger.error(f"检查扫码枪所输入的组件码异常：{e}", exc_info=True)
        return warnning_msg

    def update_main_data(self, is_append=True):
        try:
            if self.stop:  # 如果要退出线程直接返回
                return
            # 增量获取维修产品对象，查询所有的产品
            models, ng_product_ids = self.cruds.retrive_list(self.task_id,
                                                             self.existed_product_ids,
                                                             p_status=self.p_status,
                                                             reverse_position=self._reverse_position,
                                                             scanner_code=self.scanner_code,
                                                             )
            if is_append:  # 增量更新self.do_update_data置为True，self.new_models
                self.do_update_data = True
                self.new_models = models
            self.models = models
            self.existed_product_ids.extend(ng_product_ids)
            self.existed_product_codes = [m.PRODUCT_CODE for m in self.models]
            self.undo_update_times = 0  # 只要拉取一次维修产品对象，无更新计数器就清零
        except Exception as e:
            logger.error(f"查询维修产品列表失败：{e}", exc_info=True)
            not self.stop and self.signal_new_recheck_products_error.emit(f"查询维修产品列表失败")

    def time_sleep_interval(self, time_sum, time_interval=0.1):
        """
        :param time_sum:  要间隔的时间
        :param time_interval: 单次循环的时间
        :return: 0-正常执行完; 1-线程要退出
        """
        for _ in range(int(time_sum / time_interval)):
            if self.stop:  # 如果要退出线程直接返回，因为下面旧
                return
            time.sleep(time_interval)

    def quit(self):
        logger.debug(f"停止检测任务<{self.task_id}>实时刷新维修产品列表")
        self.stop = True


if __name__ == '__main__':
    sys.path.append("..")

    app = QApplication(sys.argv)
    win = MaintenanceWenPageWidget(1111)
    win.show()

    sys.exit(app.exec_())
