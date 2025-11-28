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

# 主相机线程类，继承自 QThread，用于异步相机操作
class UVCameraThread(QThread):
    def __init__(self):
        #定义Camera类的初始化函数，以及一些通用变量
        super().__init__()

        self.hcam = None       # 相机句柄
        self.buf = None        # 图像数据缓存区
        self.w = 1904          # 图像宽度
        self.h = 1904          # 图像高度
        self.setx = 480          # x偏置
        self.sety = 480         # y偏置
        self.sliceNum = 0      # 当前图像切片编号
        self.saved = 0         # 当前保存图像数
        self.hcam_fr = None    # 相机外部特征句柄

        # 如果不是模拟模式，就初始化真实相机
        if camera_sim is None:
            self.Init_Camera()
            #if self.hcam is not None:
                #self.hcam_fr.get_float_feature("ExposureTime").set(100000.0)
                #self.hcam_fr.get_float_feature("Gain").set(12.0)

    def run(self):
        self.QueueOut()

    # 异步任务处理主循环（用于执行 UI 下发的命令）
    def QueueOut(self):
        num = 0
        self.item = self.queue.get()  # 获取消息队列中的第一个任务
        while self.item.action != 'exit':
            try:
                if self.item.action == 'Snap':
                    self.Snap(self.item.selection)
                elif self.item.action == 'Live':
                    self.Live()
                elif self.item.action == 'Zcycle':
                    self.Zcycle()
                elif self.item.action == 'update_Exposure':
                    self.update_Exposure()
                elif self.item.action == 'GetExposure':
                    self.GetExposure()
                elif self.item.action == 'AutoExposure':
                    self.AutoExposure()
                elif self.item.action == 'update_Gain':
                    self.update_Gain()
                elif self.item.action == 'GetGain':
                    self.GetGain()
                elif self.item.action == 'AutoGain':
                    self.AutoGain()
                elif self.item.action == 'LightON':
                    self.Light_on(self.item.selection)
                elif self.item.action == 'LightOFF':
                    self.Light_off(self.item.selection)
                elif self.item.action == 'InitSaveCount':
                    self.saved = 0
                elif self.item.action == 'Init_Mosaic':
                    self.Init_Mosaic(self.item.args)
                elif self.item.action == 'Display_Mosaic':
                    self.Display_Mosaic(self.item.args)
                elif self.item.action == 'Save_Mosaic':
                    self.Save_Mosaic()
                else:
                    message = 'Invalid camera action: ' + self.item.action
                    self.ui.statusbar.showMessage(message)
                    self.log.write(message)
            except Exception as error:
                message = "\nAn error occurred in UVCamera action, skipping: " + str(error)
                print(message)
                self.ui.statusbar.showMessage(message)
                self.log.write(message)
                print(traceback.format_exc())
            num += 1
            self.item = self.queue.get()  # 获取下一个任务
        print('close camera')
        self.Close()
        self.ui.statusbar.showMessage("Camera Thread successfully exited")
        
    
    def GetImage(self,feedback = False,collect = False):
        if self.hcam is not None:
            self.hcam_fr.get_float_feature("ExposureTime").set(self.ui.Exposure.value()*1000.0)
            if self.ui.Avetimes.value() <= 1:
                self.buf = self.hcam.data_stream[0].get_image()
                self.image = self.buf.get_numpy_array()
            else:
                all_images = []
                for i in range(self.ui.Avetimes.value()):
                    self.buf = self.hcam.data_stream[0].get_image()
                    img = self.buf.get_numpy_array()
                    all_images.append(img)
                self.image = np.clip(np.rint(np.mean(all_images, axis = 0)), 0, 65535).astype(np.uint16)
            self.img_16bit = Image.fromarray(self.image.astype(np.uint16), mode='I;16')
            self.img_8bit = ((self.image - self.image.min()) / (self.image.max() - self.image.min()) * 255).astype(np.uint8)
            pixmap = ImagePlot(Image.fromarray(self.img_8bit))  # 转换为Qt可显示格式
            # self.ui.Image.clear()
            self.ui.Image.setPixmap(pixmap)  # 显示在界面上

            if collect:
                save_path = self.PathQueue.get()
                self.img_16bit.save(save_path, "TIFF")
                self.StagebackQueue.put('BackSnap Finished')
                return            
            if self.ui.Save.isChecked():
                self.saved += 1
                save_path = f"{self.ui.DIR.toPlainText()}/{self.sliceNum}-{str(self.saved).zfill(3)}.tif"
                self.img_16bit.save(save_path, "TIFF")
            # self.ui.CurrentExpo.setValue(self.hcam_fr.get_float_feature("ExposureTime").get()/1000)


            self.ui.statusbar.showMessage('Image taken')
            print('1 image taken')
            if feedback == True:
                
                self.CBackQueue.put(self.img_8bit)
                self.StagebackQueue.put('BackSnap Finished')
            

    # 初始化并打开真实相机
    def Init_Camera(self):
        # 已修改完毕
        # 判断是否使用真实相机。如果导入 amcam 成功，camera_sim 为 None，代表使用真实硬件
        if camera_sim is None:
            device_manager = gx.DeviceManager()  # 打开设备

            if device_manager.update_all_device_list()[0] == 0:
                # 如果没有找到任何相机设备
                print("No camera found")
                self.hcam = None  # 清空相机句柄

            else:
                
                self.hcam = device_manager.open_device_by_index(1)  # 打开设备，返回相机句柄对象
                

                try:
                    self.hcam_fr = self.hcam.get_remote_device_feature_control() # 返回设备属性对象
                    self.hcam_fr.get_enum_feature("GainAuto").set("Off")
                    self.hcam_fr.get_enum_feature("ExposureAuto").set("Off")
                    self.hcam_fr.get_enum_feature("PixelFormat").set("MONO12")
                    self.hcam_fr.get_int_feature("Width").set(self.w)
                    self.hcam_fr.get_int_feature("Height").set(self.h)
                    self.hcam_fr.get_int_feature("OffsetX").set(self.setx)
                    self.hcam_fr.get_int_feature("Offsety").set(self.sety)
                    #self.hcam_fr.get_int_feature("OffsetX").set(1428-self.w//2)
                    #self.hcam_fr.get_int_feature("Offsety").set(1424-self.h//2)

                
                except Exception as ex:
                    # 打开失败，打印错误
                    print(ex)

                else:
                    self.w = self.hcam_fr.get_int_feature("Width").get()
                    self.h = self.hcam_fr.get_int_feature("Height").get()



    # 拍照功能（一次触发）
    def Snap(self,selection):
        feedback = selection.get('feedback',False)
        collect = selection.get('collect',False)
        if self.hcam is not None:
            # self.Light_on()
            self.hcam.stream_on() 

        self.GetImage(feedback,collect)
        self.hcam.stream_off()



    # 实时预览功能
    def Live(self):
        if self.hcam is not None:
            self.hcam.stream_on()
            
            while self.ui.LiveButton.isChecked():
                self.GetImage()
            self.ui.LiveButton.setText('Live')
            self.hcam.stream_off()
            

    # 设置曝光时间（从界面获取值）
    def update_Exposure(self):
        if self.hcam is not None:
            self.hcam_fr.get_float_feature("ExposureTime").set(self.ui.Exposure.value()*1000.0)
            self.ui.CurrentExpo.setValue(self.hcam_fr.get_float_feature("ExposureTime").get()/1000.0)
        
    # 获取曝光时间
    def GetExposure(self):
        if self.hcam is not None:
            return self.hcam_fr.get_float_feature("ExposureTime").get()/1000.0

    # 控制自动曝光开关
    def AutoExposure(self):
        if self.hcam is not None:
            if self.ui.AutoExpo.isChecked():
                self.hcam_fr.get_enum_feature("ExposureAuto").set("Continuous")
            else:
                self.hcam_fr.get_enum_feature("ExposureAuto").set("Off")
                self.ui.Exposure.setValue(self.ui.CurrentExpo.value())
                
    def update_Gain(self):
        if self.hcam is not None:
            self.hcam_fr.get_float_feature("Gain").set(self.ui.Gain.value()*1.0)
            self.ui.CurrentGain.setValue(self.hcam_fr.get_float_feature("Gain").get()/1.0)
        
    # 获取曝光时间
    def GetGain(self):
        if self.hcam is not None:
            return self.hcam_fr.get_float_feature("Gain").get()/1.0

    # 控制自动曝光开关
    def AutoGain(self):
        if self.hcam is not None:
            if self.ui.AutoGain.isChecked():
                self.hcam_fr.get_enum_feature("GainAuto").set("Continuous")
            else:
                self.hcam_fr.get_enum_feature("GainAuto").set("Off")
                self.ui.Gain.setValue(self.ui.CurrentGain.value())



    def Init_Mosaic(self, args = []):
        Xtiles = args[1][0]  # 马赛克列数
        Ytiles = args[1][1]  # 马赛克行数
        #self.scale = min(math.gcd(self.h,self.w),32) #求小于32的最大公约数作为scale
        self.scale = 8

        self.surf = np.zeros([Ytiles*(self.h//self.scale), Xtiles*(self.w//self.scale)], dtype=np.uint8)
        pixmap = ImagePlot(self.surf)
        self.ui.Mosaic.clear()
        self.ui.Mosaic.setPixmap(pixmap)
        self.sliceNum += 1

        filename = f'slice-{self.sliceNum}-Tiles X-{Xtiles}-by Y-{Ytiles}-.bin'
        filePath = os.path.join(self.ui.DIR.toPlainText(), filename)
        open(filePath, 'wb').close()


    def Display_Mosaic(self, args = []):
        Xtiles = args[1][0]
        Ytiles = args[1][1]
        Y = Ytiles - args[0][1] - 1
        X = args[0][0] if args[0][1] % 2 == 1 else Xtiles - args[0][0] - 1

        self.surf[self.h//self.scale*Y:self.h//self.scale*(Y+1),
                  self.w//self.scale*X:self.w//self.scale*(X+1)] = self.img_8bit[::self.scale, ::self.scale]

        pixmap = ImagePlot(self.surf)
        self.ui.Mosaic.clear()
        self.ui.Mosaic.setPixmap(pixmap)

    # 保存马赛克拼图图像
    def Save_Mosaic(self):
        if self.ui.Save.isChecked():
            pixmap = ImagePlot(self.surf)
            pixmap.save(f'{self.ui.DIR.toPlainText()}/slice{self.sliceNum}coase.tif', "TIFF")

    # 关闭相机并释放资源
    def Close(self):
        if self.hcam is not None:
            self.hcam.close_device()
            self.hcam = None

    def Light_on(self,selection):
        feedback = selection.get('feedback',False)
        with ni.Task() as light_task:
            light_task.do_channels.add_do_chan("Robot/port1/line5:7", line_grouping=LineGrouping.CHAN_PER_LINE)
            light_task.write([1, 1, 1])
        if feedback:
            self.StagebackQueue.put('Light Turned On')
            

    def Light_off(self,selection):
        feedback = selection.get('feedback',False)
        with ni.Task() as light_task:
            light_task.do_channels.add_do_chan("Robot/port1/line5:7", line_grouping=LineGrouping.CHAN_PER_LINE)
            light_task.write([0, 0, 0])
        if feedback:
            self.StagebackQueue.put('Light Turned Off')

            
    def MoveMicro(self,COOR):
        if not (SIM):
            with ni.Task('AOtask') as AOtask:
                AOtask.ao_channels.add_ao_voltage_chan(physical_channel='Robot/ao3', \
                                                      min_val=0, max_val=10.0, \
                                                      units=ni.constants.VoltageUnits.VOLTS)
                voltage = COOR * 0.05
                voltage = max(0.0, min(10.0, voltage))
                AOtask.write(voltage, auto_start=True)
                AOtask.wait_until_done(timeout = 1)
                AOtask.stop()
                self.ui.ZMcurrent.setValue(COOR)
                self.ui.ZMPosition.setValue(COOR)
                print(f"[Micro Stage] Moved to position: {COOR}")
        

    # def Light_on(self):
    #     with artdaq.Task() as light_task:
    #         light_task.do_channels.add_do_chan("Robot/port1/line6:7", line_grouping=LineGrouping.CHAN_PER_LINE)
    #         light_task.write([1, 1])

    # def Light_off(self):
    #     with artdaq.Task() as light_task:
    #         light_task.do_channels.add_do_chan("Robot/port1/line6:7", line_grouping=LineGrouping.CHAN_PER_LINE)
    #         light_task.write([0, 0])
