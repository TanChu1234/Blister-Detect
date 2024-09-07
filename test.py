    
# # Define the content you want to save
# content = "This is the content that will be saved to the text file."

# # Open the file in write mode ('w'). This will create a new file or overwrite an existing file.
# with open('log_2024-07-11/output.txt', 'w') as file:
#     # Write the content to the file
#     file.write(content)

# print("Content has been saved to output.txt")


from PyQt6.QtWidgets import QApplication, QMainWindow, QHeaderView, QTableWidgetItem
import sys
import Camera_trig, Home
from Settings_Cam import *
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

def add_data():
    row_position = ui.tableWidget.rowCount()
    ui.tableWidget.insertRow(row_position)
    ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(ui.label_check.text()))
    ui.tableWidget.setItem(row_position, 1, QTableWidgetItem("2"))
    ui.tableWidget.setItem(row_position, 2, QTableWidgetItem("3"))
    ui.tableWidget.setItem(row_position, 3, QTableWidgetItem("4"))
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
def reset_table():
    ui.tableWidget.setRowCount(0)
def update_time():
    current_time = QtCore.QDateTime.currentDateTime()
    ui.labelDate.setText(current_time.toString('yyyy-MM-dd HH:mm:ss'))

def start_updateDateTime():
    timer.timeout.connect(update_time)
    timer.start(1000)
    update_time()

def stop_updateDateTime():
    timer.stop()

def loadSettings(ui):
    global template_path
    global save_roi
    template_path = settings.value("last_directory", "")
    save_roi = settings.value("save_roi", "")
    if ui.stackedWidget.currentIndex() == 0:
        save_roi = settings.value("save_roi", "")
        # ui.label_Roi.setText(str(save_roi))
    elif ui.stackedWidget.currentIndex() == 1:
        save_roi = settings.value("save_roi_1", "")
        # ui.label_Roi.setText(str(save_roi))
    elif ui.stackedWidget.currentIndex() == 2:
        save_roi = settings.value("save_roi_2", "")
        # ui.label_Roi.setText(str(save_roi))
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
    ui.Pixel_2.setText(settings.value("pixel2", ""))
    ui.ROI_2.setText(settings.value("roi2", ""))
    ui.min_area_2.setText(settings.value("min2", ""))
    ui.max_area_2.setText(settings.value("max2", ""))
    # print(save_roi)
def on_combobox_change(index):
    # Update the QStackedWidget based on the selected option
    ui.stackedWidget.setCurrentIndex(index)
def getVariableHome(index):
    global fl_thres
    global int_broken_pixel
    global fl_ecc
    global int_segment
    global pixels_thres
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
        pixels = ui.Pixel_2.text()
        pixels_thres = int(pixels)
        segment = ui.ROI_2.text()
        int_segment = int(segment)
        min_area = ui.min_area_2.text()
        int_minArea = int(min_area)
        max_area = ui.max_area_2.text()
        int_maxArea = int(max_area)
    print(intMinBlob)

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
        settings.setValue("pixel2", ui.Pixel_2.text())
        settings.setValue("roi2", ui.ROI_2.text())
        settings.setValue("min2", ui.min_area_2.text())
        settings.setValue("max2", ui.max_area_2.text())
        # QMessageBox.information(mainWindow, "Title", "The ROI_capsule has been saved.")
def open_device():
    cameraUI()
def close_device():
    homeUI()
def detectHome():
    getVariableHome(ui.stackedWidget.currentIndex())
def detectCam():
    getValueFromQDialog()
def homeUI():
    global ui  
    ui = Home.Ui_MainWindow()
    ui.setupUi(mainWindow)
    loadSettings(ui)
    ui.comboBox_type.currentIndexChanged.connect(on_combobox_change)
    ui.save0.clicked.connect(saveSetting)
    ui.save1.clicked.connect(saveSetting)
    ui.save2.clicked.connect(saveSetting)
    ui.bnDetect.clicked.connect(detectHome)
    ui.bnOpen.clicked.connect(open_device)
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
    ui.bnSoftwareTrigger.clicked.connect(detectCam)
    ui.bnSettings.clicked.connect(open_settings_dialog)
    ui.bnAdd_data.clicked.connect(add_data)
    ui.bnSave_data.clicked.connect(save_data)
    ui.bnClear_data.clicked.connect(reset_table)
    mainWindow.show()        

def open_settings_dialog():
    settings_dialog = MyDialog(ui.comboBox_type.currentIndex())
    settings_dialog.exec()
    # loadSettings(ui)
def getValueFromQDialog():
    global fl_thres
    global int_broken_pixel
    global fl_ecc
    global int_segment
    global pixels_thres
    global int_minArea
    global int_maxArea
    global intMinBlob
    global intMaxBlob
    global intCracks
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
        pixels = settings_dialog.Pixel_2.text()
        pixels_thres = int(pixels)
        segment = settings_dialog.ROI_2.text()
        int_segment = int(segment)
        min_area = settings_dialog.min_area_2.text()
        int_minArea = int(min_area)
        max_area = settings_dialog.max_area_2.text()
        int_maxArea = int(max_area)
    print(minBlob)
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
            settings.setValue("pixel2", self.Pixel_2.text())
            settings.setValue("roi2", self.ROI_2.text())
            settings.setValue("min2", self.min_area_2.text())
            settings.setValue("max2", self.max_area_2.text())
            # QMessageBox.information(mainWindow, "Title", "The ROI_capsule has been saved.")
            
      
 
if __name__ == "__main__":
    isOpen = True
    isGrabbing = False
    timer = QtCore.QTimer()
    settings = QtCore.QSettings("YourCompany", "YourApp")
    ui = ''
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    homeUI()
    app.exec()
    sys.exit()
