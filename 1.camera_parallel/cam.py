
#coding=utf-8
import cv2
import numpy as np
import mvsdk
from datetime import datetime
import os
import time
from multiprocessing import Queue,Process

class cam:
    def __init__(self,idx):
        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        if nDev < 1:
            print("No camera was found!")
            return
        for i, DevInfo in enumerate(DevList):
            print("{}: {} {}".format(i, DevInfo.GetFriendlyName(), DevInfo.GetPortType()))

        DevInfo = DevList[idx]
        self.hCamera = 0
        try:
            self.hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
            return

        cap = mvsdk.CameraGetCapability(self.hCamera)
        monoCamera = (cap.sIspCapacity.bMonoSensor != 0)

        # RoI Binning
        # RoIImage = mvsdk.tSdkImageResolution()
        # RoIImage.iIndex = 255
        # RoIImage.iWidthFOV = 648 
        # RoIImage.iHeightFOV = 486 
        # RoIImage.iWidth = 648 
        # RoIImage.iHeight = 486
        # mvsdk.CameraSetImageResolution(self.hCamera,RoIImage)      

        mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)
        mvsdk.CameraSetTriggerMode(self.hCamera, 0)
        mvsdk.CameraSetAeState(self.hCamera, 1)
        mvsdk.CameraSetAeExposureRange(self.hCamera,100*1000,100*1000)
        mvsdk.CameraPlay(self.hCamera)
        
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)
    def read(self):
        pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
        mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
        mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
        frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
        # print(frame.shape)
        frame = cv2.resize(frame, (512,512))
        return frame
    def kill(self):
        mvsdk.CameraUnInit(self.hCamera)
        mvsdk.CameraAlignFree(self.pFrameBuffer)

'''
single-processor
'''

# if __name__ == "__main__":
#     cam_1=cam(0)
#     cam_2=cam(1)
#     cam_3=cam(2)
#     cam_4=cam(3)
#     idx=0
#     while True:
#         print("=============={} frames=============".format(idx))
#         t0=time.time()
#         frame1 = cam_1.read()
#         t1=time.time()
#         print("cam_1 spends {} s".format(t1-t0))
#         frame2 = cam_2.read()
#         t2=time.time()
#         print("cam_2 spends {} s".format(t2-t1))
#         frame3 = cam_3.read()
#         t3=time.time()
#         print("cam_3 spends {} s".format(t3-t2))
#         frame4 = cam_4.read()
#         t4=time.time()
#         print("cam_4 spends {} s".format(t4-t3))
#         print("total time {} s".format(t4-t0))
#         idx+=1
#         # frames=[]
#         # frames.append(frame1)
#         # frames.append(frame2)
#         # frames.append(frame3)
#         # frames.append(frame4)
#         # frames_1=np.hstack(frames[:2])
#         # frames_2=np.hstack(frames[2:])
#         # frames=np.vstack([frames_1,frames_2])

#         # cv2.imshow('0',frame1)
#         # cv2.waitKey(1)
        
    

def read_frames(cam_idx, frame_queue, trigger_queue):
    cam_instance = cam(cam_idx)
    while True:
        # Wait for the trigger signal
        trigger = trigger_queue.get()
        if trigger:
            frame = cam_instance.read()
            frame_queue.put(frame)
'''
mutil-processor
'''
if __name__ == "__main__":
    frame_queue_1 = Queue(0)
    frame_queue_2 = Queue(0)
    frame_queue_3 = Queue(0)
    frame_queue_4 = Queue(0)

    trigger_queue_1 = Queue(0)
    trigger_queue_2 = Queue(0)
    trigger_queue_3 = Queue(0)
    trigger_queue_4 = Queue(0)

    process_1 = Process(target=read_frames, args=(0, frame_queue_1, trigger_queue_1))
    process_2 = Process(target=read_frames, args=(1, frame_queue_2, trigger_queue_2))
    process_3 = Process(target=read_frames, args=(2, frame_queue_3, trigger_queue_3))
    process_4 = Process(target=read_frames, args=(3, frame_queue_4, trigger_queue_4))

    process_1.start()
    process_2.start()
    process_3.start()
    process_4.start()
    idx=0
    while True:
        # Send trigger signals to both processes
        print("=============={} frames=============".format(idx))
        trigger_queue_1.put(True)
        trigger_queue_2.put(True)
        trigger_queue_3.put(True)
        trigger_queue_4.put(True)
        t0=time.time()
        frame1 = frame_queue_1.get()
        t1=time.time()
        print("cam_1 spends {} s".format(t1-t0))
        frame2 = frame_queue_2.get()
        t2=time.time()
        print("cam_2 spends {} s".format(t2-t1))
        frame3 = frame_queue_3.get()
        t3=time.time()
        print("cam_3 spends {} s".format(t3-t2))
        frame4 = frame_queue_4.get()
        t4=time.time()
        print("cam_4 spends {} s".format(t4-t3))
        print("total time {} s".format(t4-t0))
        idx+=1

# #         # frames=[]
# #         # frames.append(frame1)
# #         # frames.append(frame2)
# #         # frames.append(frame3)
# #         # frames.append(frame4)
# #         # frames_1=np.hstack(frames[:2])
# #         # frames_2=np.hstack(frames[2:])
# #         # frames=np.vstack([frames_1,frames_2])

# #         # cv2.imshow('0',frames)
# #         # cv2.waitKey(1)
        
