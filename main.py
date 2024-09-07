# -*- coding: utf-8 -*-
import sys

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from CamOperation_class_trig import CameraOperation
from MvCameraControl_class import *
from MvErrorDefine_const import *
from CameraParams_header import *
import ctypes
from  utils import *
import Oval_2, Circle, Capsule
import Home, Camera_trig
from Settings_Cam import *
import time
from datetime import datetime
import cv2 as cv
import numpy as np
if __name__ == "__main__":
    global deviceList
    deviceList = MV_CC_DEVICE_INFO_LIST()
    global cam
    cam = MvCamera()
    global nSelCamIndex
    nSelCamIndex = 0
    global obj_cam_operation
    obj_cam_operation = 0
    global isOpen
    isOpen = False
    global isGrabbing
    isGrabbing = False
    global is_image 
    is_image = False
    global img_path
    img_path = None
    global cropped_image
    cropped_image = None
    global roi
    roi = None
    timer = QTimer()
    settings = QSettings("YourCompany", "YourApp")
    # Get the current date
    current_date = datetime.now()
    # Format the date as a string, e.g., '2024-05-24'
    date_string = "D:/Pharma3/NG_Images/NG_Images_" + current_date.strftime('%Y-%m-%d')
    if not os.path.exists(date_string):
        # Create a directory with the date string as the name
        os.makedirs(date_string)
    # Bind drop-down list to device information index
    def xFunc():
        global nSelCamIndex
        nSelCamIndex = TxtWrapBy("[", "]", ui.ComboDevices.get())

    # Decoding Characters
    def decoding_char(c_ubyte_value):
        c_char_p_value = ctypes.cast(c_ubyte_value, ctypes.c_char_p)
        try:
            decode_str = c_char_p_value.value.decode('gbk')  # Chinese characters
        except UnicodeDecodeError:
            decode_str = str(c_char_p_value.value)
        return decode_str
    
    # Get param
    def get_param():
        ret = obj_cam_operation.Get_parameter()
        if ret != MV_OK:
            strError = "Get param failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.StandardButton.Ok)
        else:
            ui.edtExposureTime.setText("{0:.2f}".format(obj_cam_operation.exposure_time))
            ui.edtGain.setText("{0:.2f}".format(obj_cam_operation.gain))
            ui.edtFrameRate.setText("{0:.2f}".format(obj_cam_operation.frame_rate))

    def is_float(str):
        try:
            float(str)
            return True
        except ValueError:
            return False
    # Set param
    def save_settings():
        frame_rate = ui.edtFrameRate.text()
        exposure = ui.edtExposureTime.text()
        gain = ui.edtGain.text()
        set_conf()
        if is_float(frame_rate)!=True or is_float(exposure)!=True or is_float(gain)!=True:
            strError = "Set param failed ret:" + ToHexStr(MV_E_PARAMETER)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.StandardButton.Ok)
            return MV_E_PARAMETER
        
        ret = obj_cam_operation.Set_parameter(frame_rate, exposure, gain)
        if ret != MV_OK:
            strError = "Set param failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.StandardButton.Ok)
        print("set ok")
        return MV_OK
    def set_conf():
        text =  ui.Threshold.text()
        ui.Threshold.setText(text)
        text2 = ui.Broken.text()
        ui.Broken.setText(text2)
        text3 = ui.Eccentricity.text()
        ui.Eccentricity.setText(text3)
    # enum devices
    def enum_devices():
        # Define global variables
        global deviceList
        global obj_cam_operation

        # Initialize device list
        deviceList = MV_CC_DEVICE_INFO_LIST()

        # Enumerate devices
        ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, deviceList)
        if ret != 0:
            strError = "Enum devices fail! ret = :" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.StandardButton.Ok)
            return ret

        # Check if devices are found
        if deviceList.nDeviceNum == 0:
            QMessageBox.warning(mainWindow, "Info", "Find no device", QMessageBox.StandardButton.Ok)
            return ret
        print("Find %d devices!" % deviceList.nDeviceNum)

        # Initialize device list for UI
        devList = []
        for i in range(0, deviceList.nDeviceNum):
            mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                print("\ngige device: [%d]" % i)
                user_defined_name = decoding_char(mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName)
                model_name = decoding_char(mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName)
                print("device user define name: " + user_defined_name)
                print("device model name: " + model_name)

                nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                print("current ip: %d.%d.%d.%d " % (nip1, nip2, nip3, nip4))
                devList.append(
                    "[" + str(i) + "]GigE: " + user_defined_name + " " + model_name + "(" + str(nip1) + "." + str(
                        nip2) + "." + str(nip3) + "." + str(nip4) + ")")
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print("\nu3v device: [%d]" % i)
                user_defined_name = decoding_char(mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName)
                model_name = decoding_char(mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName)
                print("device user define name: " + user_defined_name)
                print("device model name: " + model_name)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: " + strSerialNumber)
                devList.append("[" + str(i) + "]USB: " + user_defined_name + " " + model_name
                               + "(" + str(strSerialNumber) + ")")

        # Update UI ComboBox with the device list
        ui.ComboDevices.clear()
        ui.ComboDevices.addItems(devList)
        ui.ComboDevices.setCurrentIndex(0)

###################--------------------------###################
    # open device
    def open_device():
        global deviceList
        global nSelCamIndex
        global obj_cam_operation
        global isOpen
        global cam
        if isOpen:
            QMessageBox.warning(mainWindow, "Error", 'Camera is Running!', QMessageBox.StandardButton.Ok)
            return MV_E_CALLORDER

        nSelCamIndex = ui.ComboDevices.currentIndex()
        if nSelCamIndex < 0:
            QMessageBox.warning(mainWindow, "Error", 'Please select a camera!', QMessageBox.StandardButton.Ok)
            return MV_E_CALLORDER

        obj_cam_operation = CameraOperation(cam, deviceList, nSelCamIndex)
        ret = obj_cam_operation.Open_device()
        if 0 != ret:
            strError = "Open device failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.StandardButton.Ok)
            isOpen = False
        else:
            cameraUI()
            isOpen = True
            enable_controls_Camera()
            start_updateDateTime()
            set_software_trigger_mode()
            get_param()
           
    # Close device
    def close_device():
        global isOpen
        global isGrabbing
        stop_updateDateTime()
        if isOpen:
            obj_cam_operation.Close_device()
            isOpen = False
            homeUI()
        isGrabbing = False
        enable_controls_Home()
    def offCamera():
        global isOpen
        if isOpen:
            obj_cam_operation.Close_device()
        
###################--------------------------###################
    # Start grab image
    def start_grabbing():
        global obj_cam_operation
        global isGrabbing 
        ret = obj_cam_operation.Start_grabbing()
        
        # ret = obj_cam_operation.Start_grabbing()
        if ret != 0:
            strError = "Start grabbing failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.StandardButton.Ok)
        else:
            isGrabbing = True
            enable_controls_Camera()
            obj_cam_operation.image_signal.connect(detect_cam)
            
                

    # Stop grab image
    def stop_grabbing():
        global isGrabbing
        ret = obj_cam_operation.Stop_grabbing()
        if ret != 0:
            strError = "Stop grabbing failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.StandardButton.Ok)
        else:
            isGrabbing = False
            enable_controls_Camera()
###################--------------------------###################

    # set software trigger mode
    def set_software_trigger_mode():
        global isGrabbing
        ret = obj_cam_operation.Set_trigger_mode(True)
        if ret != 0:
            strError = "Set trigger mode failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.StandardButton.Ok)
        else:
            ui.bnSoftwareTrigger.setEnabled(isGrabbing)

    # ch: en:set trigger software
    def trigger_once():
        ret = obj_cam_operation.Trigger_once()
        if ret != 0:
            strError = "TriggerSoftware failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.StandardButton.Ok)
    
    
###################--------------------------###################
    
    def enable_controls_Home():
        global isOpen
        ui.bnOpen.setEnabled(not isOpen)
 
    # en:set enable status
    def enable_controls_Camera():
        global isGrabbing
        global isOpen
        # Set the status of the group first, and then set the status of each control individually.
        signal_icon()
    
        ui.bnClose.setEnabled(isOpen)
        ui.bnStart.setEnabled(isOpen and (not isGrabbing))
        ui.bnStop.setEnabled(isOpen and isGrabbing)
        ui.label_signal_start.setVisible(isOpen and isGrabbing)
        ui.label_signal_stop.setVisible(isOpen and (not isGrabbing))
        ui.bnSoftwareTrigger.setEnabled(isGrabbing)

        ui.groupConfig_Oval.setEnabled(isOpen)
    
###################--------------------------###################
    def signal_icon():
        global ui      
        pixmap = QPixmap(r"D:\Pharma3\icon\logo.png") 
        ui.label_logo.setPixmap(pixmap.scaled(ui.label_logo.width(), ui.label_logo.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        pixmap = QPixmap(r"D:\Pharma3\icon\green.png") 
        ui.label_signal_start.setPixmap(pixmap.scaled(ui.label_signal_start.width(), ui.label_signal_start.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        pixmap = QPixmap(r"D:\Pharma3\icon\red.png")    
        ui.label_signal_stop.setPixmap(pixmap.scaled(ui.label_signal_stop.width(), ui.label_signal_stop.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

###################--------------------------###################
    def update_time():
        current_time = QDateTime.currentDateTime()
        ui.labelDate.setText(current_time.toString('yyyy-MM-dd HH:mm:ss'))

    def start_updateDateTime():
        timer.timeout.connect(update_time)
        timer.start(1000)
        update_time()

    def stop_updateDateTime():
        timer.stop()

###################--------------------------###################
    def table_data():
        # Create the QTableWidget with 5 rows and 3 columns
        ui.tableWidget.setRowCount(5)
        ui.tableWidget.setColumnCount(4)
        # Set the table headers
        ui.tableWidget.setHorizontalHeaderLabels(['DATE', 'ID', 'QUANTITY', 'STATUS'])
        # Make columns stretch to fit the table's width
        ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Populate the table with sample data
        for row in range(5):
            for column in range(4):
                ui.tableWidget.setItem(row, column, QTableWidgetItem(f"Item {row},{column}"))
    def save_data():
        with open('Log/log_2024-07-11.txt', 'w') as file:
    #     # Write the content to the file
    #     file.write(content)) as file:
            rowCount = ui.tableWidget.rowCount()
            columnCount = ui.tableWidget.columnCount()
            
            # Write headers
            headers = [ui.tableWidget.horizontalHeaderItem(col).text() for col in range(columnCount)]
            file.write('\t'.join(headers) + '\n')
            
            # Write data
            for row in range(rowCount):
                rowData = []
                for column in range(columnCount):
                    item = ui.tableWidget.item(row, column)
                    rowData.append(item.text() if item is not None else '')
                file.write('\t'.join(rowData) + '\n')
    def add_data():
        row_position = ui.tableWidget.rowCount()
        ui.tableWidget.insertRow(row_position)
        ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(ui.label_check.text()))
        ui.tableWidget.setItem(row_position, 1, QTableWidgetItem("2"))
        ui.tableWidget.setItem(row_position, 2, QTableWidgetItem("3"))
        ui.tableWidget.setItem(row_position, 3, QTableWidgetItem("4"))
    def reset_table():
        ui.tableWidget.setRowCount(0)
###################--------------------------###################
    def on_radio_button_toggled():
        radio_button = QApplication.instance().sender()
        if radio_button.isChecked():
            pass
###################--------------------------###################
    def loadTeamplateImage():
        global template_path
        options = QFileDialog.Option.ReadOnly  # Use the enum directly without calling it
        
        template_path, _ = QFileDialog.getOpenFileName(mainWindow, "Open Image File", "", "Image Files (*.png *.jpg *.bmp)", options=options)
        if template_path:
            settings = QSettings("YourCompany", "YourApp")
            settings.setValue("last_directory", template_path)
            ui.label_template_dir.setText("Template Saved: " + template_path)
            pixmap = QPixmap(template_path)
            # ui.label_temp.setPixmap(pixmap.scaled(ui.label_temp.width(), ui.label_temp.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            ui.label_temp.setPixmap(pixmap)
        else:
            loadSettings()
            # template_path = ui.label_template_dir.text().split(': ', 1)[1] 

        
    def loadImages():
        global img_path
        folder_path = QFileDialog.getExistingDirectory(mainWindow, "Select Folder")
        if folder_path:
            image_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                                if f.lower().endswith(('.png', '.jpg', '.bmp'))]
            image_paths.sort()  # Sort the list of image paths

            ui.listWidget.clear()
            for img_path in image_paths:
                pixmap = QPixmap(img_path)
                icon = QIcon(pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                item = QListWidgetItem(icon, os.path.basename(img_path))
                item.setData(Qt.ItemDataRole.UserRole, img_path)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                ui.listWidget.addItem(item)
                
            if image_paths:
                img_path = image_paths[0]
                displayImage(image_paths[0])

    def displayImage(imagePath):
        global is_image
        global image_arr
        global scale_factor_w, scale_factor_h
        image_arr = cv.imread(imagePath)
        height, width, channel = image_arr.shape
        bytesPerLine = 3 * width
        qImg = QImage(image_arr.data, width, height, bytesPerLine, QImage.Format.Format_BGR888)

       # Create pixmap and scale it
        pixmap = QPixmap.fromImage(qImg)
        scaled_pixmap = pixmap.scaled(ui.label_img_out.width(), ui.label_img_out.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # Update the label with the scaled pixmap
        ui.label_img_out.setPixmap(scaled_pixmap)
        ui.label_img_out.setText("")  # Clear the label text
        ui.label_img_out.setCursor(Qt.CursorShape.CrossCursor)

        # Calculate actual scaled dimensions
        scaled_width = scaled_pixmap.width()
        scaled_height = scaled_pixmap.height()

        # Calculate scale factors based on the actual displayed image size
        scale_factor_w = width / scaled_width
        scale_factor_h = height / scaled_height
        
        is_image = True
    def displayImageFromItem(item):
        global img_path
        img_path = item.data(Qt.ItemDataRole.UserRole)
        displayImage(img_path)

###################--------------------------###################
    def on_crop_rect_changed(x, y, width, height):
        # Handle the rectangle coordinates here
        global scale_factor_w, scale_factor_h
        global image_arr
        global template_path
        global cropped_image
        global roi
        if is_image:
            # Calculate the offsets if the aspect ratio is preserved
            display_width = ui.label_img_out.width()
            display_height = ui.label_img_out.height()
            scaled_width = int(display_height * image_arr.shape[1] / image_arr.shape[0])
            scaled_height = int(display_width * image_arr.shape[0] / image_arr.shape[1])
            
            if scaled_width <= display_width:
                offset_x = (display_width - scaled_width) / 2
                offset_y = 0
            else:
                offset_x = 0
                offset_y = (display_height - scaled_height) / 2

            # Adjust coordinates to account for the offsets
            x -= offset_x
            y -= offset_y

            # Convert coordinates to original image scale
            orig_start_x = int(x * scale_factor_w)
            orig_start_y = int(y * scale_factor_h)
            orig_end_x = int((x + width) * scale_factor_w)
            orig_end_y = int((y + height) * scale_factor_h)

            # Ensure coordinates are within the image bounds
            orig_start_x = max(0, min(orig_start_x, image_arr.shape[1] - 1))
            orig_start_y = max(0, min(orig_start_y, image_arr.shape[0] - 1))
            orig_end_x = max(0, min(orig_end_x, image_arr.shape[1]))
            orig_end_y = max(0, min(orig_end_y, image_arr.shape[0]))

            cropped_image = image_arr[orig_start_y:orig_end_y, orig_start_x:orig_end_x]
            roi = [[orig_start_x, orig_start_y], [orig_end_x, orig_end_y]]

            # Debug print to check the shape of cropped image
            # print(f"Cropped image shape: {cropped_image.shape}")
            
            # Example numpy array (replace this with your actual array data)
            array_data = cropped_image.astype(np.uint8)
            # Convert numpy array to QImage
            height, width, channels = array_data.shape
            bytes_per_line = 3 * width
            qimage = QImage(array_data.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
            # Convert QImage to QPixmap
            qpixmap = QPixmap.fromImage(qimage) 
            ui.label_temp.setPixmap(qpixmap)

    def saveROI():
        global roi
        global save_roi
        save_roi = roi
        if save_roi is not None:
            ui.label_Roi.setText(str(save_roi))
            if ui.stackedWidget.currentIndex() == 0:
                settings.setValue("save_roi", save_roi)
            elif ui.stackedWidget.currentIndex() == 1:
                settings.setValue("save_roi_1", save_roi)
            elif ui.stackedWidget.currentIndex() == 2:
                settings.setValue("save_roi_2", save_roi)
            QMessageBox.information(mainWindow, "Title", "The ROI has been saved.")
        else:
            loadSettings()
            QMessageBox.warning(mainWindow, "Error", "Choose ROI before saving", QMessageBox.StandardButton.Ok)
    def saveTemPlate():
        global cropped_image
        if cropped_image is not None:
            template_path, _ = QFileDialog.getSaveFileName(ui.label_img_out, "Save Cropped Image", "", "Images (*.png *.xpm *.jpg *.jpeg *.bmp)")
            if template_path :
                cv.imwrite(template_path, cropped_image)
                
                settings.setValue("last_directory", template_path)
                ui.label_template_dir.setText("Template Directory: " + template_path)
                ui.label_img_out.active_clearRect = True
        else:
            QMessageBox.warning(mainWindow, "Error", "Choose template before saving", QMessageBox.StandardButton.Ok)

    def loadSettings():
        global template_path
        global save_roi
        template_path = settings.value("last_directory", "")
        save_roi = settings.value("save_roi", "")
        if ui.stackedWidget.currentIndex() == 0:
            save_roi = settings.value("save_roi", "")
            ui.label_Roi.setText(str(save_roi))
        elif ui.stackedWidget.currentIndex() == 1:
            save_roi = settings.value("save_roi_1", "")
            ui.label_Roi.setText(str(save_roi))
        elif ui.stackedWidget.currentIndex() == 2:
            save_roi = settings.value("save_roi_2", "")
            ui.label_Roi.setText(str(save_roi))
        ui.Threshold_0.setText(settings.value("thresh0", ""))
        ui.Broken_0.setText(settings.value("crack0", ""))
        ui.Eccentricity_0.setText(settings.value("ecc0", ""))
        ui.ROI_0.setText(settings.value("roi0", ""))
        ui.minBlob_0.setText(settings.value("minBlob0", ""))
        ui.maxBlob_0.setText(settings.value("maxBlob0", ""))
        ui.Threshold_1.setText(settings.value("thresh1", ""))
        ui.Broken_1.setText(settings.value("crack1", ""))
        ui.Eccentricity_1.setText(settings.value("ecc1", ""))
        ui.ROI_1.setText(settings.value("roi1", ""))
        ui.minBlob_1.setText(settings.value("minBlob1", ""))
        ui.maxBlob_1.setText(settings.value("maxBlob1", ""))
        ui.Threshold_2.setText(settings.value("thresh2", ""))        
        ui.value.setText(settings.value("value", ""))
        ui.hue.setText(settings.value("hue", ""))
        ui.ROI_2.setText(settings.value("roi2", ""))
        ui.min_area_2.setText(settings.value("min2", ""))
        ui.max_area_2.setText(settings.value("max2", ""))
    def on_combobox_change(index):
        # Update the QStackedWidget based on the selected option
        ui.stackedWidget.setCurrentIndex(index)
        loadSettings()
    def getVariableHome(index):
        global fl_thres
        global int_broken_pixel
        global fl_ecc
        global int_segment
        global int_hue
        global int_value
        global int_minArea
        global int_maxArea
        global intMinBlob
        global intMaxBlob
        global intCracks
        if index == 0:
            thres_text = ui.Threshold_0.text()
            fl_thres = float(thres_text)
            broken_pixel = ui.Broken_0.text()
            int_broken_pixel = int(broken_pixel)
            ecc = ui.Eccentricity_0.text()
            fl_ecc = float(ecc)
            segment = ui.ROI_0.text()
            int_segment = int(segment)
            minBlob = ui.minBlob_0.text()
            intMinBlob = int(minBlob)
            maxBlob = ui.maxBlob_0.text()
            intMaxBlob = int(maxBlob)
        elif index == 1:
            thres_text = ui.Threshold_1.text()
            fl_thres = float(thres_text)
            broken_pixel = ui.Broken_1.text()
            int_broken_pixel = int(broken_pixel)
            ecc = ui.Eccentricity_1.text()
            fl_ecc = float(ecc)
            segment = ui.ROI_1.text()
            int_segment = int(segment)
            min_area = ui.min_area_1.text()
            int_minArea = int(min_area)
            minBlob = ui.minBlob_1.text()
            intMinBlob = int(minBlob)
            maxBlob = ui.maxBlob_1.text()
            intMaxBlob = int(maxBlob)
            cracks = ui.Broken_1.text()
            intCracks = int(cracks)
        else:
            thres_text = ui.Threshold_2.text()
            fl_thres = float(thres_text)
            hue = ui.hue.text()
            int_hue = int(hue)
            value = ui.value.text()
            int_value = int(value)
            segment = ui.ROI_2.text()
            int_segment = int(segment)
            min_area = ui.min_area_2.text()
            int_minArea = int(min_area)
            max_area = ui.max_area_2.text()
            int_maxArea = int(max_area)
        # print(fl_thres)
    def saveSetting():
        if ui.stackedWidget.currentIndex() == 0:
            settings.setValue("thresh0", ui.Threshold_0.text())
            settings.setValue("crack0", ui.Broken_0.text())
            settings.setValue("ecc0", ui.Eccentricity_0.text())
            settings.setValue("roi0", ui.ROI_0.text())
            settings.setValue("minBlob0", ui.minBlob_0.text())
            settings.setValue("maxBlob0", ui.maxBlob_0.text())
            # QMessageBox.information(mainWindow, "Title", "The ROI_oval has been saved.")
        elif ui.stackedWidget.currentIndex() == 1:
            settings.setValue("thresh1", ui.Threshold_1.text())
            settings.setValue("crack1", ui.Broken_1.text())
            settings.setValue("ecc1", ui.Eccentricity_1.text())
            settings.setValue("min1", ui.min_area_1.text())
            settings.setValue("roi1", ui.ROI_1.text())
            settings.setValue("minBlob1", ui.minBlob_1.text())
            settings.setValue("maxBlob1", ui.maxBlob_1.text())
            # QMessageBox.information(mainWindow, "Title", "The ROI_circle has been saved.")
        elif ui.stackedWidget.currentIndex() == 2:
            settings.setValue("thresh2", ui.Threshold_2.text())
            settings.setValue("hue", ui.hue.text())
            settings.setValue("value", ui.value.text())
            settings.setValue("roi2", ui.ROI_2.text())
            settings.setValue("min2", ui.min_area_2.text())
            settings.setValue("max2", ui.max_area_2.text())
            # QMessageBox.information(mainWindow, "Title", "The ROI_capsule has been saved.")
        
    
###################--------------------------###################
    def open_settings_dialog():
        settings_dialog = MyDialog(ui.comboBox_type.currentIndex())
        settings_dialog.exec()
    def getValueFromQDialog():
        global fl_thres
        global int_broken_pixel
        global fl_ecc
        global int_segment
        global int_minArea
        global int_maxArea
        global intMinBlob
        global intMaxBlob
        global intCracks
        global int_value
        global int_hue
        settings_dialog = MyDialog(ui.comboBox_type.currentIndex())
        if ui.comboBox_type.currentIndex() == 0:
            thres_text = settings_dialog.Threshold_0.text()
            fl_thres = float(thres_text)
            broken_pixel = settings_dialog.Broken_0.text()
            int_broken_pixel = int(broken_pixel)
            ecc = settings_dialog.Eccentricity_0.text()
            fl_ecc = float(ecc)
            segment = settings_dialog.ROI_0.text()
            int_segment = int(segment)
            minBlob = settings_dialog.minBlob_0.text()
            intMinBlob = int(minBlob)
            maxBlob = settings_dialog.maxBlob_0.text()
            intMaxBlob = int(maxBlob)
        elif ui.comboBox_type.currentIndex() == 1:
            thres_text = settings_dialog.Threshold_1.text()
            fl_thres = float(thres_text)
            broken_pixel = settings_dialog.Broken_1.text()
            int_broken_pixel = int(broken_pixel)
            ecc = settings_dialog.Eccentricity_1.text()
            fl_ecc = float(ecc)
            segment = settings_dialog.ROI_1.text()
            int_segment = int(segment)
            min_area = settings_dialog.min_area_1.text()
            int_minArea = int(min_area)
            minBlob = settings_dialog.minBlob_1.text()
            intMinBlob = int(minBlob)
            maxBlob = settings_dialog.maxBlob_1.text()
            intMaxBlob = int(maxBlob)
            cracks = settings_dialog.Broken_1.text()
            intCracks = int(cracks)
        else:
            thres_text = settings_dialog.Threshold_2.text()
            fl_thres = float(thres_text)
            hue = settings_dialog.hue.text()
            int_hue = int(hue)
            value = settings_dialog.value.text()
            int_value = int(value)
            segment = settings_dialog.ROI_2.text()
            int_segment = int(segment)
            min_area = settings_dialog.min_area_2.text()
            int_minArea = int(min_area)
            max_area = settings_dialog.max_area_2.text()
            int_maxArea = int(max_area)
        # print(minBlob)
    class MyDialog(QtWidgets.QDialog, Ui_Dialog):
        def __init__(self, index,  parent = None):
            super(MyDialog, self).__init__(parent)
            self.setupUi(self)
            self.stackedWidget.setCurrentIndex(index)
            loadSettings(self)
            self.save0.clicked.connect(self.save)
            self.save1.clicked.connect(self.save)
            self.save2.clicked.connect(self.save)
        def save(self):
            if ui.stackedWidget.currentIndex() == 0:
                settings.setValue("thresh0", self.Threshold_0.text())
                settings.setValue("crack0", self.Broken_0.text())
                settings.setValue("ecc0", self.Eccentricity_0.text())
                settings.setValue("roi0", self.ROI_0.text())
                settings.setValue("minBlob0", self.minBlob_0.text())
                settings.setValue("maxBlob0", self.maxBlob_0.text())
                # QMessageBox.information(mainWindow, "Title", "The ROI_oval has been saved.")
            elif ui.stackedWidget.currentIndex() == 1:
                settings.setValue("thresh1", self.Threshold_1.text())
                settings.setValue("crack1", self.Broken_1.text())
                settings.setValue("ecc1", self.Eccentricity_1.text())
                settings.setValue("min1", self.min_area_1.text())
                settings.setValue("roi1", self.ROI_1.text())
                settings.setValue("minBlob1", self.minBlob_1.text())
                settings.setValue("maxBlob1", self.maxBlob_1.text())
                # QMessageBox.information(mainWindow, "Title", "The ROI_circle has been saved.")
            elif ui.stackedWidget.currentIndex() == 2:
                settings.setValue("thresh2", self.Threshold_2.text())
                settings.setValue("hue", ui.hue.text())
                settings.setValue("value", ui.value.text())
                settings.setValue("roi2", self.ROI_2.text())
                settings.setValue("min2", self.min_area_2.text())
                settings.setValue("max2", self.max_area_2.text())
                # QMessageBox.information(mainWindow, "Title", "The ROI_capsule has been saved.")
                
    def detect_home():
        global img_path
        global template_path
        global save_roi
        save = False
        getVariableHome(index=ui.stackedWidget.currentIndex())
        if not os.path.exists(template_path):
            QMessageBox.warning(mainWindow, "Error", "Choose template before detecting", QMessageBox.StandardButton.Ok)
        elif img_path is None:
            QMessageBox.warning(mainWindow, "Error", "Choose image before detecting", QMessageBox.StandardButton.Ok)
        else:
            # if template_path is not None:
            template = cv.imread(template_path, cv.IMREAD_GRAYSCALE)
            start_time = time.time()
            if ui.stackedWidget.currentIndex() == 0:
                if ui.comboBox_oval.currentIndex() == 0:
                    img_out, count = Oval_2.matchOval(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment)   
                elif ui.comboBox_oval.currentIndex() == 1:
                    img_out, count = Oval_2.checkCrack(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_broken_pixel)
                elif ui.comboBox_oval.currentIndex() == 2:
                    img_out, count = Oval_2.checkBlemish(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, intMinBlob, intMaxBlob)
                elif ui.comboBox_oval.currentIndex() == 3:
                    img_out, count = Oval_2.checkOval(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, fl_ecc)
                elif ui.comboBox_oval.currentIndex() == 4:
                    img_out, count = Oval_2.All(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_broken_pixel, intMinBlob, intMaxBlob, fl_ecc)
                if count == 6: 
                    ui.label_check.setText("OK")
                    ui.label_check.setStyleSheet("""
                #label_check {
                    background-color: rgb(0, 255, 0);
                    color: black;
                }
                """)
                else:
                    save = True
                    ui.label_check.setText("NG")
                    ui.label_check.setStyleSheet("""
                #label_check {
                    background-color: rgb(255, 0, 0);
                    color: black;
                }
                """)
            if ui.stackedWidget.currentIndex() == 1:
                if ui.comboBox_circle.currentIndex() == 0:
                    img_out, count = Circle.matchCỉcle(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment)
                elif ui.comboBox_circle.currentIndex() == 1:
                    img_out, count = Circle.checkArea(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_minArea)
                elif ui.comboBox_circle.currentIndex() == 2:
                    img_out, count = Circle.checkCircle(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_minArea, fl_ecc)
                elif ui.comboBox_circle.currentIndex() == 3:
                    img_out, count = Circle.checkStrange(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_minArea, fl_ecc, intMinBlob, intMaxBlob)
                elif ui.comboBox_circle.currentIndex() == 4:
                    img_out, count = Circle.checkCracks(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_minArea, fl_ecc, intMinBlob, intMaxBlob, intCracks)
                elif ui.comboBox_circle.currentIndex() == 5:
                    img_out, count = Circle.final(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_minArea, fl_ecc, intMinBlob, intMaxBlob, intCracks)
                if count == 1: 
                    ui.label_check.setText("OK")
                    ui.label_check.setStyleSheet("""
                #label_check {
                    background-color: rgb(0, 255, 0);
                    color: black;
                }
                """)
                else:
                    save = True
                    ui.label_check.setText("NG")
                    ui.label_check.setStyleSheet("""
                #label_check {
                    background-color: rgb(255, 0, 0);
                    color: black;
                }
                """)
            if ui.stackedWidget.currentIndex() == 2:
                if ui.comboBox_capsule.currentIndex() == 0:
                    img_out, count = Capsule.matchCapsule(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment) 
                elif ui.comboBox_capsule.currentIndex() == 1:
                    img_out, count = Capsule.checkColor(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_hue, int_value) 
                elif ui.comboBox_capsule.currentIndex() == 2:
                    img_out, count = Capsule.checkArea(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_hue, int_value, int_minArea, int_maxArea)
                elif ui.comboBox_capsule.currentIndex() == 3:
                    img_out, count = Capsule.all(img_path, template, fl_thres, save_roi[0], save_roi[1], int_segment, int_hue, int_value, int_minArea, int_maxArea)
                if count == 2: 
                    ui.label_check.setText("OK")
                    ui.label_check.setStyleSheet("""
                #label_check {
                    background-color: rgb(0, 255, 0);
                    color: black;
                }
                """)
                else:
                    save = True
                    ui.label_check.setText("NG")
                    ui.label_check.setStyleSheet("""
                #label_check {
                    background-color: rgb(255, 0, 0);
                    color: black;
                }
                """)
            end_time = time.time()
            elapsed_time = round((end_time - start_time)*1000,2)
            time_process = str(elapsed_time) + "ms"
            ui.label_time.setText(time_process)
            height, width, channels = img_out.shape
            bytes_per_line = channels * width
            q_image = QImage(img_out.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)

            # Convert the QImage to QPixmap and scale it to fit the label's size, maintaining the aspect ratio
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(ui.label_img_out.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # Set the scaled pixmap on the label
            ui.label_img_out.setPixmap(scaled_pixmap)
            
            # if save:          
            #     dt_string = datetime.now().strftime("%d_%m_%Y_%Hh%Mm%Ss")  + f"{datetime.now().microsecond // 1000:03d}ms"
            #     file_path = date_string + "/" + dt_string + ".png"
            #     cv.imwrite(file_path, img_out)      
###################--------------------------###################
    def detect_cam():
        global template_path
        template = cv.imread(template_path, cv.IMREAD_GRAYSCALE)
        # time.sleep(0.03)
        start_time = time.time()
        img_path_cam = r"D:\Pharma4\new\1.bmp"
        thres_text = ui.Threshold.text()
        fl_thres = float(thres_text)
        broken_pixel = ui.Broken.text()
        int_broken_pixel = int(broken_pixel)
        ecc = ui.Eccentricity.text()
        fl_ecc = float(ecc)
        img_out, count = all(img_path_cam, template, fl_thres, int_broken_pixel,fl_ecc)
        if count == 60: 
            ui.label_check.setText("OK")
            ui.label_check.setStyleSheet("""
        #label_check {
            background-color: rgb(0, 255, 0);
            color: black;
        }
        """)
        else:
            ui.label_check.setText("NG")
            ui.label_check.setStyleSheet("""
        #label_check {
            background-color: rgb(255, 0, 0);
            color: black;
        }
        """)
        end_time = time.time()
        elapsed_time = round((end_time - start_time)*1000,2)
        time_process = str(elapsed_time) + "ms"
        ui.label_ProcessTime.setText(time_process)
        height, width, channels = img_out.shape
        bytes_per_line = channels * width
        q_image = QImage(img_out.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)

        # Convert the QImage to QPixmap and scale it to fit the label's size, maintaining the aspect ratio
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(ui.label_img_out.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        # Set the scaled pixmap on the label
        ui.label_img_out.setPixmap(scaled_pixmap)
###################--------------------------###################
    def homeUI():
        global ui
        global template_path
        global save_roi    
        ui = Home.Ui_MainWindow()
        ui.setupUi(mainWindow)
        loadSettings()
        ui.label_template_dir.setText("Template Directory: " + template_path)
        ui.label_Roi.setText(str(save_roi))
        ui.bnEnum.clicked.connect(enum_devices)
        ui.bnOpen.clicked.connect(open_device)
        ui.bnLoadImg.clicked.connect(loadImages)
        ui.bnLoadTemplate.clicked.connect(loadTeamplateImage)
        ui.label_img_out.crop_rect_changed.connect(on_crop_rect_changed)
        ui.bnSaveTemplate.clicked.connect(saveTemPlate)
        ui.bnSaveRoi.clicked.connect(saveROI)
        ui.listWidget.itemClicked.connect(displayImageFromItem)
        ui.comboBox_type.currentIndexChanged.connect(on_combobox_change)
        ui.bnDetect.clicked.connect(detect_home)
        ui.save0.clicked.connect(saveSetting)
        ui.save1.clicked.connect(saveSetting)
        ui.save2.clicked.connect(saveSetting)
        mainWindow.setStatusBar
        mainWindow.show()

        
    def cameraUI():
        global ui
        ui = Camera_trig.Ui_MainWindow()
        ui.setupUi(mainWindow)
        table_data()
        loadSettings(ui)
        ui.comboBox_type.currentIndexChanged.connect(on_combobox_change)
        ui.save0.clicked.connect(saveSetting)
        ui.save1.clicked.connect(saveSetting)
        ui.save2.clicked.connect(saveSetting)
        ui.bnClose.clicked.connect(close_device)
        ui.bnStart.clicked.connect(start_grabbing)
        ui.bnStop.clicked.connect(stop_grabbing)
        ui.bnSetParam.clicked.connect(save_settings)
        ui.bnSettings.clicked.connect(open_settings_dialog)
        ui.edtExposureTime.returnPressed.connect(save_settings)
        ui.edtFrameRate.returnPressed.connect(save_settings)
        ui.edtGain.returnPressed.connect(save_settings)
        ui.bnSoftwareTrigger.clicked.connect(trigger_once)
        ui.bnAdd_data.clicked.connect(add_data)
        ui.bnClear_data.clicked.connect(reset_table)
        mainWindow.show()
###################--------------------------###################

    ui = ''
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    homeUI()
    app.exec()
    offCamera()
    # saveSettingHome()
    sys.exit()


