# -*- coding: utf-8 -*-
"""
Main camera control thread using Amcam SDK with PyQt GUI integration.
Includes functionality for live preview, snap image, exposure control,
and mosaic image stitching.
"""

# 尝试导入 amcam 模块，如果失败则进入仿真模式（模拟环境）
try:
    import gxipy as gx 
    camera_sim = None
except:
    print('no camera driver, using simulation')
    camera_sim = 1

global SIM
SIM = False
###########################################
from PyQt5.QtCore import  QThread

try:
    import artdaq as ni
    from artdaq.constants import AcquisitionType as Atype
    from artdaq.constants import Edge
    from artdaq.constants import (LineGrouping)
except:
    SIM = True
############################################
# 通用模块导入
import ctypes, sys, time
import initAPI
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import *
import numpy as np
from qimage2ndarray import *
import traceback
from Generaic_functions import *  # 自定义函数集合，可能包含图像处理或转换方法
from libtiff import TIFF
import qimage2ndarray as qpy
import sys
from PIL import Image
import matplotlib.pyplot as plt
import os
import math
import artdaq as ni
from artdaq.constants import LineGrouping

import os

class UVLightThread(QThread):
    def __init__(self):
        #定义LightThread类的初始化函数，以及一些通用变量
        super().__init__()

        self.number = 3


    def run(self):
        self.QueueOut()

    # 异步任务处理主循环（用于执行 UI 下发的命令）
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            try:
                if self.item.action == 'LightON':
                    self.LightON(self.item.selection)
                elif self.item.action == 'LightOFF':
                    self.LightOFF(self.item.selection)
                elif self.item.action == 'LightTest':
                    self.LightTest(self.item.selection)
                else:
                    message = 'Invalid light action: ' + self.item.action
                    self.ui.statusbar.showMessage(message)
                    self.log.write(message)
            except Exception as error:
                message =  "\nAn error occurred in UVLight action, skipping: " + str(error)
                print(message)
                self.ui.statusbar.showMessage(message)
                self.log.write(message)
                print(traceback.format_exc())
            self.item = self.queue.get()
        print('close light')
        self.LightOFF()
        self.ui.statusbar.showMessage("Camera Thread successfully exited")
        

    def LightON(self,selection):
        feedback = selection.get('feedback',False)
        with ni.Task() as light_task:
            light_task.do_channels.add_do_chan("Robot/port1/line5:7", line_grouping=LineGrouping.CHAN_PER_LINE)
            light_task.write([1, 1, 1])
        if feedback:
            self.StagebackQueue.put('LightON Finished')
                
    def LightOFF(self,selection):
        feedback = selection.get('feedback',False)
        with ni.Task() as light_task:
            light_task.do_channels.add_do_chan("Robot/port1/line5:7", line_grouping=LineGrouping.CHAN_PER_LINE)
            light_task.write([0, 0, 0])
        if feedback:
            self.StagebackQueue.put('LightOFF Finished')

    def LightTest(self,selection):
        feedback = selection.get('feedback', False)
        lightlist = selection.get('lightlist', [1, 1, 1])
        with ni.Task() as light_task:
            light_task.do_channels.add_do_chan("Robot/port1/line5:7", line_grouping=LineGrouping.CHAN_PER_LINE)
            light_task.write(lightlist)
        if feedback:
            self.StagebackQueue.put('LightOFF Finished')