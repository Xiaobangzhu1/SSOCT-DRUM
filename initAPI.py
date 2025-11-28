# -*- coding: utf-8 -*-
"""
Created on Mon Jul  7 18:17:06 2025
@author: admin
"""
import gxipy as gx
import numpy as np
import sys
from PIL import Image
import matplotlib.pyplot as plt
import os
import artdaq
from artdaq.constants import LineGrouping

# 参数设置
num_images = 8
exposure_time = 100000.0  # 若为 -1 则开启自动曝光
gain_value = 12.0         # 若为 -1 则开启自动增益
base_save_path = "brain_5"

width, height = 2856, 2848
pixel_format = "MONO12"

# 创建保存路径
save_dir = os.path.join(base_save_path, 'Ori')
ave_dir = os.path.join(base_save_path, 'ave')
os.makedirs(save_dir, exist_ok=True)
os.makedirs(ave_dir, exist_ok=True)

# 打开设备
device_manager = gx.DeviceManager()
if device_manager.update_all_device_list()[0] == 0:
    print("No Device")
    sys.exit(1)

cam = device_manager.open_device_by_index(1)
# print("Success Open Device")

# 设备参数设置
remote = cam.get_remote_device_feature_control()

#trigger_soft_ware_feature =  remote.get_register_feature( "TriggerSoftware")

# === 自动曝光与增益控制 ===
remote.get_enum_feature("ExposureAuto").set("Off")
remote.get_enum_feature("GainAuto").set("Off")
# print("[INFO] ExposureAuto and GainAuto set to Off")

# if exposure_time == -1:
#     remote.get_enum_feature("ExposureAuto").set("On")
#     print("[INFO] ExposureAuto set to On")
# else:
#     remote.get_float_feature("ExposureTime").set(exposure_time)
#     print(f"[INFO] ExposureTime set to {exposure_time} µs")

# if gain_value == -1:
#     remote.get_enum_feature("GainAuto").set("On")
#     print("[INFO] GainAuto set to On")
# else:
#     remote.get_float_feature("Gain").set(gain_value)
#     print(f"[INFO] Gain set to {gain_value} dB")

# 像素格式
# remote.get_enum_feature("PixelFormat").set(pixel_format)
# print(f"[INFO] PixelFormat set to {pixel_format}")
# print("Success Set Device")

# # 开灯
# with artdaq.Task() as light_task:
#     light_task.do_channels.add_do_chan("Robot/port1/line6:7", line_grouping=LineGrouping.CHAN_PER_LINE)
#     light_task.write([1, 1])

# 图像采集
cam.stream_on()
all_images = []

for i in range(num_images):
    raw_image = cam.data_stream[0].get_image()
    img = raw_image.get_numpy_array()
    all_images.append(img)

    # 保存每张图
    # Image.fromarray(img.astype(np.uint16)).save(os.path.join(save_dir, f"{i+1}.tiff"), format="TIFF", compression=None)
    # print(f"Success Save Image {i+1}")

cam.stream_off()

# # 关灯
# with artdaq.Task() as light_task:
#     light_task.do_channels.add_do_chan("Robot/port1/line6:7", line_grouping=LineGrouping.CHAN_PER_LINE)
#     light_task.write([0, 0])

cam.close_device()
# print("Success Close Device")

# 平均图像计算与保存
# average_img = np.mean(all_images, axis=0)
# Image.fromarray(average_img.astype(np.uint16)).save(os.path.join(ave_dir, "average_image.tiff"), format="TIFF", compression=None)

# # 展示
# plt.imshow(all_images[0], cmap='gray')
# plt.title("First Image")
# plt.axis('off')
# plt.show()
# plt.imshow(average_img, cmap='gray')
# plt.title("Average Image")
# plt.axis('off')
# plt.show()
