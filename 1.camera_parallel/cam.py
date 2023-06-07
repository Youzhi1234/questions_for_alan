
#coding=utf-8
import cv2
import numpy as np
import mvsdk
from datetime import datetime
import os
import time

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

        RoIImage = mvsdk.tSdkImageResolution()
        RoIImage.iIndex = 255
        RoIImage.iWidthFOV = 648 
        RoIImage.iHeightFOV = 486 
        RoIImage.iWidth = 648 
        RoIImage.iHeight = 486
        mvsdk.CameraSetImageResolution(self.hCamera,RoIImage)      

        mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)
        mvsdk.CameraSetTriggerMode(self.hCamera, 0)
        mvsdk.CameraSetAeState(self.hCamera, 1)
        mvsdk.CameraSetAeExposureRange(self.hCamera,1*1000,10*1000)
        
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
        print(frame.shape)
        frame = cv2.resize(frame, (512,512))
        return frame
    def kill(self):
        mvsdk.CameraUnInit(self.hCamera)
        mvsdk.CameraAlignFree(self.pFrameBuffer)


if __name__ == "__main__":
    # now = datetime.now()
    # dt_string = now.strftime("%Y-%m-%d_%H-%M-%S")
    # print(dt_string)
    # cam_1_folder=f"datasets/TTCI/video/{dt_string}/01"
    # cam_2_folder=f"datasets/TTCI/video/{dt_string}/02"
    # cam_3_folder=f"datasets/TTCI/video/{dt_string}/03"
    # cam_4_folder=f"datasets/TTCI/video/{dt_string}/04"
    # os.makedirs(cam_1_folder)
    # os.makedirs(cam_2_folder)
    # os.makedirs(cam_3_folder)
    # os.makedirs(cam_4_folder)

    cam_1=cam(0)
    cam_2=cam(1)
    # cam_3=cam(2)
    # cam_4=cam(3)
    idx=0
    while True:
        t=time.time()
        frames=[]
        frame1 = cam_1.read()
        frames.append(frame1)
        frame2 = cam_2.read()
        # frames.append(frame2)
        # frame3 = cam_3.read()
        # frames.append(frame3)
        # frame4 = cam_4.read()
        # frames.append(frame4)
        # cv2.imwrite(cam_1_folder+'/'+str(idx).zfill(5)+'.jpg',frame1)
        # cv2.imwrite(cam_2_folder+'/'+str(idx).zfill(5)+'.jpg',frame2)
        # cv2.imwrite(cam_3_folder+'/'+str(idx).zfill(5)+'.jpg',frame3)
        # cv2.imwrite(cam_4_folder+'/'+str(idx).zfill(5)+'.jpg',frame4)
        
        frames_1=np.hstack(frames[:2])
        # frames_2=np.hstack(frames[2:])
        # frames=np.vstack([frames_1,frames_2])

        cv2.imshow('0',frames_1)
        cv2.waitKey(1)
        idx+=1
        # time.sleep(0.1)
        print(time.time()-t)
        

        

# def read_frames(cam_idx, frame_queue, trigger_queue):
#     cam_instance = cam(cam_idx)
#     while True:
#         # Wait for the trigger signal
#         trigger = trigger_queue.get()
#         if trigger:
#             frame = cam_instance.read()
#             frame_queue.put(frame)

# if __name__ == "__main__":
#     frame_queue_1 = Queue(0)
#     frame_queue_2 = Queue(0)
#     trigger_queue_1 = Queue(0)
#     trigger_queue_2 = Queue(0)

#     process_1 = Process(target=read_frames, args=(0, frame_queue_1, trigger_queue_1))
#     process_2 = Process(target=read_frames, args=(1, frame_queue_2, trigger_queue_2))

#     process_1.start()
#     process_2.start()

#     while True:
#         # Send trigger signals to both processes
#         T = time.time()
#         trigger_queue_1.put(True)
#         trigger_queue_2.put(True)
#         frame1 = frame_queue_1.get()
#         print(time.time() - T)
#         frame2 = frame_queue_2.get()
#         print(time.time() - T)
#         cv2.imshow('0',frame1)
#         cv2.imshow('1',frame2)
#         cv2.waitKey(1)
        
#         # print(frame1.shape)
#         # print(frame2.shape)

#     process_1.join()
#     process_2.join()