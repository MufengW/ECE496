from datetime import datetime
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5.QtCore import QTime, QTimer
from PyQt5.QtWidgets import QFrame
import numpy as np
import time
from threading import Timer, Lock
import pytz
from tzlocal import get_localzone
from random import randint


import TradingBotConfig as theConfig
from UIWidgets import ButtonHoverStart
from UIWidgets import ButtonHoverStart
from UIWidgets import ButtonHoverPause
from UIWidgets import ButtonHoverSettings
# from UIWidgets import ButtonHoverDonation
from UIWidgets import ButtonHoverInfo
from UIWidgets import RadioHoverSimulation
from UIWidgets import RadioHoverTrading
from UIWidgets import SliderHoverRiskLevel
from UIWidgets import SliderHoverSensitivityLevel
from UIWidgets import LabelClickable
from UISettings import UISettings
# from UIDonation import UIDonation
from UIInfo import UIInfo


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localTimezone = pytz.timezone(str(get_localzone()))

    def tickStrings(self, values, scale, spacing):

        try:
            if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == False): #
                valuesToReturn = [(datetime.fromtimestamp(value, self.localTimezone).strftime("%H:%M:%S\n%b%d")) for value in values]
            else:
                valuesToReturn = [(datetime.fromtimestamp(value, self.localTimezone).strftime("%H:%M:%S")) for value in values]
        except BaseException as e:
            print("UIGR - Exception in tick strings: %s" % str(e))

        return valuesToReturn

class UIGraph():

    MAIN_WINDOW_WIDTH_IN_PX = 1600
    MAIN_WINDOW_HEIGHT_IN_PX = 900

    MAX_NB_POINTS_ON_PLOT = 2000
    Y_AXIS_TOP_MARGIN_IN_EXTREMUM_PERCENT = 1.0001
    Y_AXIS_BOTTOM_MARGIN_IN_EXTREMUM_PERCENT = 0.9999
    PLOT1_DEFAULT_MINIMUM = 8000
    PLOT1_DEFAULT_MAXIMUM = 10000

    STR_RADIO_SIMULATION = 'Simulation Mode'
    STR_RADIO_TRADING = 'Live Trading Mode'
    STR_BUTTON_START = 'Start'
    STR_BUTTON_PAUSE = 'Pause'
    STR_BUTTON_SETTINGS = 'Settings'
    # STR_BUTTON_Donation = 'Donate'
    STR_BUTTON_INFO = 'Info'
    STR_LABEL_MONEY_MIDDLEMARKET_PRICE = 'Price : '
    STR_LABEL_INFO = 'Info : '
    STR_LABEL_CURRENT_STATE = 'Current State : '
    STR_LABEL_TOTAL_GAINS = 'Total Profit : '

    STR_BORDER_BLOCK_STYLESHEET = "QWidget {background-color : #1f1f1f;}"
    STR_USER_BLOCK_STYLESHEET = "QWidget {background-color : #1f1f1f;}"
    STR_QLABEL_STYLESHEET = "QLabel { background-color : #1f1f1f; color : white; font: 20px;}"
    STR_QLABEL_BALANCE_STYLESHEET = "QLabel { background-color : #1f1f1f; color : white; font: bold 30px;}"
    STR_QLABEL_PROFIT_GREEN_STYLESHEET = "QLabel { background-color : #1f1f1f; color : #24b62e; font: bold 14px;}"
    STR_QLABEL_PROFIT_RED_STYLESHEET = "QLabel { background-color : #1f1f1f; color : #FF2F2F; font: bold 14px;}"
    STR_QLABEL_CURRENT_STATE_LIVE_TRADING_STYLESHEET = "QLabel { background-color : #1f1f1f; color : #ff2e2e; font: bold 20px;}"
    STR_QLABEL_INFO_STYLESHEET = "QLabel { background-color : #1f1f1f; color : white; font: 20px;}"
    STR_QLABEL_INFO_ERROR_STYLESHEET = "QLabel { background-color : #1f1f1f; color : #FF2F2F; font: 20px;}"
    STR_QLABEL_INFO_GREEN_STYLESHEET = "QLabel { background-color : #1f1f1f; color : #29CF36; font: bold 20px; text-decoration: underline;}"
    STR_QLABEL_INFO_ORANGE_STYLESHEET = "QLabel { background-color : #1f1f1f; color : #FF8000; font: bold 20px; text-decoration: underline;}"
    STR_QLABEL_TOOLTIP_STYLESHEET = "QLabel { background-color : #1f1f1f; color : white; font: 10px;}"
    STR_QLABEL_CONNECTION_STATUS_STYLESHEET = "QLabel { background-color : #1f1f1f; color : green; font: 10px;}"
    STR_QLABEL_VERSION_STYLESHEET = "QLabel { background-color : #1f1f1f; color : white; font: 20px;}"
    STR_QLABEL_LIVE_DATA_STYLESHEET = "QLabel { background-color : #1f1f1f; color : #334c6b; font: 10px;}"
    STR_QRADIOBUTTON_STYLESHEET = "QRadioButton { background-color : #1f1f1f; color : white; font: 20px;} QRadioButton::indicator:checked {background-color: #61368E; border: 1px solid white;} QRadioButton::indicator:unchecked {background-color: #1f1f1f; border: 1px solid white;}"
    STR_QRADIOBUTTON_DISABLED_STYLESHEET = "QRadioButton { background-color : #1f1f1f; color : white; font: 20px;} QRadioButton::indicator:checked {background-color: #61368E; border: 1px solid #1f1f1f;} QRadioButton::indicator:unchecked {background-color: #1f1f1f; border: 1px solid #1f1f1f;}"
    STR_QBUTTON_START_STYLESHEET = "QPushButton {background-color: #23b42c; border-width: 2px; border-radius: 10px; border-color: white; font: bold 18px; color:white} QPushButton:pressed { background-color: #1d8d24 } QPushButton:hover { background-color: #1a821f }"
    STR_QBUTTON_SETTINGS_STYLESHEET = "QPushButton {background-color: #1f1f1f; border-width: 1.5px; border-radius: 20px; border-color: white; font: bold 24px; color:white} QPushButton:pressed { background-color: #B0B0B0 } QPushButton:hover { background-color: #807E80 }"
    STR_QBUTTON_SETTINGS_DISABLED_STYLESHEET = "QPushButton {background-color: #303030; border-width: 1.5px; border-radius: 20px; border-color: #838fa7; font: bold 24px; color:white}"
    STR_QBUTTON_START_DISABLED_STYLESHEET = "QPushButton {background-color: #9f9f9f; border-width: 2px; border-radius: 10px; border-color: white; font: bold 18px; color:white}"
    STR_QBUTTON_LOADING_STYLESHEET = "QPushButton {background-color: #9f9f9f; border-width: 2px; border-radius: 10px; border-color: white; font: bold 15px; color:white}"
    STR_QBUTTON_STOP_STYLESHEET = "QPushButton {background-color: #ff1824; border-width: 2px; border-radius: 10px; border-color: white; font: bold 18px; color:white} QPushButton:pressed { background-color: #aa0009 } QPushButton:hover { background-color: #aa0009 }"
    STR_QBUTTON_PAUSE_STYLESHEET = "QPushButton {background-color: #ddbd00; border-width: 2px; border-radius: 10px; border-color: white; font: bold 18px; color:white} QPushButton:pressed { background-color: #b3af00 } QPushButton:hover { background-color: #b3af00 }"
    STR_QBUTTON_PAUSE_DISABLED_STYLESHEET = "QPushButton {background-color: #9f9f9f; border-width: 2px; border-radius: 10px; border-color: white; font: bold 18px; color:white}"
    STR_QFRAME_SEPARATOR_STYLESHEET = "background-color: rgb(20, 41, 58);"
    STR_QSLIDER_STYLESHEET = "QSlider::handle:hover {background-color: #C6D0FF;} QSlider::handle:horizontal {background-color: #61368E;}"

    def __init__(self, QtApplication, Settings):
        print("UIGR - UIGraph Constructor")

        self.theSettings = Settings

        self.firstGraphDataInitIsDone = False

        # Settings-dependant variables init
        # self.STR_LABEL_FIAT_BALANCE = str(self.theSettings.SETT_GetSettings()["strFiatType"]) + " Account Balance : "
        # self.STR_LABEL_CRYPTO_BALANCE = str(self.theSettings.SETT_GetSettings()["strCryptoType"]) + " Account Balance : "
        self.STR_LABEL_FIAT_BALANCE = ""
        self.STR_LABEL_CRYPTO_BALANCE = ""
    
        # Window initialization
        self.theQtApp = QtApplication
        self.mainWidget = QtGui.QWidget()
        self.rootGrid = QtGui.QGridLayout() # for setting + info layout
        self.mainWidget.setWindowTitle('Astibot')        
        self.mainWidget.resize(self.MAIN_WINDOW_WIDTH_IN_PX, self.MAIN_WINDOW_HEIGHT_IN_PX)
        self.mainWidget.setWindowIcon(QtGui.QIcon("'logos/' + AstibotIcon.png"))
        
        # Customize main widget (window)
        self.mainWidget.setStyleSheet("background-color:#1f1f1f;")
        # self.mainWidget.setAutoFillBackground(True) # TODO: not sure what it does
               
        # By default consider the data series will start now. This can be overridden
        self.MostRecentPointTimestamp = time.time()

        # Widget additional data initialization
        self.bStartButtonHasBeenClicked = False
        self.bPauseButtonHasBeenClicked = False
        self.timerBlinkWidgets = QtCore.QTimer()
        self.timerBlinkWidgets.timeout.connect(self.TimerRaisedBlinkWidgets)
        self.timerBlinkWidgets.start(1000)
        self.isLblCurrentStateBlinking = False
        self.currentRiskLineRawAvgValue = 0
        self.currentSensitivitySliderValue = 3
        self.sensitivitySliderValueHasChanged = True

        # Graph data initialization
        pg.setConfigOptions(antialias=True)
        nbPointsOnPlot = self.MAX_NB_POINTS_ON_PLOT
        self.UIGR_ResetAllGraphData(False, -1, nbPointsOnPlot)
        self.transactionHistory = []

        # Layouts and widgets init
        self.initializeTopWindowWidgets()
        self.initializeGraphWidgets()
        self.initializeRootLayout()
        self.mainWidget.setLayout(self.mainGridLayout)

        # Graph refresh and multithreading management
        self.isContinuousGraphRefreshEnabled = False
        self.areNewSamplesRequested = False
        self.timerUpdateGraph = QtCore.QTimer()
        self.timerUpdateGraph.timeout.connect(self.UIGR_updateGraphsSimuTimer)
        self.currentAppState = ""
        # True if a pending UI refresh has been requested from a background thread calling a UIGR API
        self.safeUIRefreshIsRequested = False
        # Necessary storage of safe UI updates
        self.lblInfoInErrorStyle = False
        self.lblInfoStr = ""
        self.realProfit = 0.0
        self.theoricProfit = 0.0
        self.percentageProfit = 0.0
        self.displayProfitAsInSimulation = False
        self.priceLabelStr = ""
        self.strEURBalance = ""
        self.strCryptoBalance = ""
        self.strLiveData = "-"

        # Live data update timer
        self.timerUpdateLiveData = QtCore.QTimer()
        self.timerUpdateLiveData.timeout.connect(self.UIGR_updateLiveDataTimer)
        self.timerUpdateLiveData.start(150)

        # End if UI init, show window
        self.mainWidget.show()

        # Child windows
        self.theUISettings = UISettings(Settings)
        # self.theUIDonation = UIDonation(Settings)
        self.theUIInfo = UIInfo()

        # Set child UIs to clickable label that can open them
        # self.lblInfo.SetUIs(self.theUISettings, self.theUIDonation) 
        self.lblInfo.SetUIs(self.theUISettings) 

        print("UIGR - UIGraph init done!")

    # Argument startTimeStamp :
    # - Set to -1 if the graph will be batch updated with a number of data greater than nbPointsOnPlot : time
    # axis will be ok and next samples will be added on the left shifting the whole graph
    # - Set to the timestamp of the first sample that will be added to the graph. This function will then build a
    # retro time axis so that, during the period where added samples < nbPointsOnPlot, next samples will be added
    # on the left shifting the whole graph
    def UIGR_ResetAllGraphData(self, applyToGraphs, startTimeStamp, nbPointsOnPlot):

        print("UIGR - Reseting all graph data with applyToGraphs = %s, startTimeStamp = %s, nbPointsOnPlot = %s" % (applyToGraphs, startTimeStamp, nbPointsOnPlot))
        self.totalNbIterations = 0
        self.totalNbGraphUpdates = 0
        self.timeOfLastSampleDisplayed = 0
        self.nbPointsOnPlot = nbPointsOnPlot
        self.currentRiskLineRawAvgValue = 0

        self.graphDataTime = []
        self.graphDataBitcoinPrice = []
        self.graphDataBitcoinPriceSmoothSlow = []
        self.graphDataBitcoinPriceSmoothFast = []
        self.graphDataBitcoinPriceMarker1 = []
        self.graphDataBitcoinPriceMarker2 = []
        self.graphDataBitcoinRiskLine = []
        self.graphDataIndicatorMACD = []
        self.minInPlot1 = self.PLOT1_DEFAULT_MINIMUM
        self.maxInPlot1 = self.PLOT1_DEFAULT_MAXIMUM

        self.graphDataTime = np.zeros(self.nbPointsOnPlot)

        # Y-Data vectors : put empty values (apprently set to zero)
        self.graphDataBitcoinPrice = np.zeros(self.nbPointsOnPlot) #For tests np.random.normal(size=self.nbPointsOnPlot)
        self.graphDataBitcoinPriceSmoothFast = np.zeros(self.nbPointsOnPlot)
        self.graphDataBitcoinPriceSmoothSlow = np.zeros(self.nbPointsOnPlot)
        self.graphDataBitcoinPriceMarker1 = np.zeros(self.nbPointsOnPlot)
        self.graphDataBitcoinPriceMarker2 = np.zeros(self.nbPointsOnPlot)
        self.graphDataBitcoinRiskLine = np.zeros(self.nbPointsOnPlot)
        self.graphDataIndicatorMACD = np.zeros(self.nbPointsOnPlot)

        if (startTimeStamp != -1):
            # Time vector : put old timestamps until now so that the "present time" will be located at the right of the graph
            self.graphDataTime = self.initInitialTimeVector(startTimeStamp)

    # Called from Main (UI) thread - OK
    def UIGR_StartContinuousGraphRefresh(self, refreshPeriodInMs):

        if (self.isContinuousGraphRefreshEnabled == False):
            print("UIGR - Starting continuous graph refresh")
            self.isContinuousGraphRefreshEnabled = True
            self.areNewSamplesRequested = True
            self.timerUpdateGraph.start(refreshPeriodInMs)

    # Called from Main (UI) thread - OK
    def UIGR_StopContinuousGraphRefresh(self):
        print("refresh stop")
        if (self.isContinuousGraphRefreshEnabled == True):
            print("UIGR - Stopping continuous graph refresh")
            self.isContinuousGraphRefreshEnabled = False
            self.areNewSamplesRequested = False
            self.timerUpdateGraph.stop()

    def UIGR_AreNewSamplesRequested(self):
        if (self.areNewSamplesRequested == True):
            self.areNewSamplesRequested = False
            return True
        else:
            return False

    def EventStartButtonClick(self):
        self.bStartButtonHasBeenClicked = True

    def EventPauseButtonClick(self):
        self.bPauseButtonHasBeenClicked = True

    def EventSettingsButtonClick(self):
        self.theUISettings.UIST_ShowWindow()
       
    # def EventDonationButtonClick(self):
    #     self.theUIDonation.UIDO_ShowWindow()

    def EventInfoButtonClick(self):
        self.theUIInfo.UIFO_ShowWindow()

    def EventRadioModeToggle(self):
        theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET = not self.radioButtonSimulation.isChecked()

    def UIGR_IsStartButtonClicked(self):
        if (self.bStartButtonHasBeenClicked == True):
            self.bStartButtonHasBeenClicked = False
            return True
        else:
            return False

    def UIGR_IsPauseButtonClicked(self):
        if (self.bPauseButtonHasBeenClicked == True):
            self.bPauseButtonHasBeenClicked = False
            return True
        else:
            return False

    def UIGR_GetSelectedRadioMode(self):
        if (self.radioButtonSimulation.isChecked() == True):
            return "Simulation"
        else:
            return "Trading"

    def EventMovedSliderRiskLevel(self):

        newRiskLineValue = theConfig.CONFIG_RISK_LINE_PERCENTS_ABOVE_THRESHOLD_TO_BUY_MIN + ((self.sliderRiskLevel.value() / 100.0) * (theConfig.CONFIG_RISK_LINE_PERCENTS_ABOVE_THRESHOLD_TO_BUY_MAX - theConfig.CONFIG_RISK_LINE_PERCENTS_ABOVE_THRESHOLD_TO_BUY_MIN))
        if (abs(newRiskLineValue - theConfig.CONFIG_RiskLinePercentsAboveThresholdToBuy) > 0.0005):
            theConfig.CONFIG_RiskLinePercentsAboveThresholdToBuy = newRiskLineValue
            riskPercent = round((theConfig.CONFIG_RiskLinePercentsAboveThresholdToBuy - 1) * 100, 1)
            self.lblRiskLevelSlider1.setText("Risk level: %s%%" % str(riskPercent))

            # Refresh risk line plot data
            self.graphDataBitcoinRiskLine.fill(self.currentRiskLineRawAvgValue * theConfig.CONFIG_RiskLinePercentsAboveThresholdToBuy)
            # Update graph
            # self.plot1GraphRiskLine.setData(x=self.graphDataTime, y=self.graphDataBitcoinRiskLine)

            if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
                # Force UI refresh. After a long running time, UI refresh is not automatic sometimes
                self.plot1.update()

    def EventMovedSliderSensitivityLevel(self):
        print("slider moved to %s" % self.sliderSensitivityLevel.value())
        if (self.sliderSensitivityLevel.value() != self.currentSensitivitySliderValue):
            self.currentSensitivitySliderValue = self.sliderSensitivityLevel.value()
            self.lblSensitivityLevelSlider1.setText("Dips sensitivity: %s/6" % str(self.currentSensitivitySliderValue))
            self.sensitivitySliderValueHasChanged = True



    def UIGR_hasSensitivityLevelValueChanged(self):
        return self.sensitivitySliderValueHasChanged

    def UIGR_getSensitivityLevelValue(self):
        self.sensitivitySliderValueHasChanged = False
        return self.currentSensitivitySliderValue

    def initializeRootLayout(self):
        print("UIGR - InitializeRootLayout")
        self.mainGridLayout.setContentsMargins(0, 0, 0, 0)

        self.rootBlockTop = QtGui.QWidget()
        self.rootBlockTop.setStyleSheet(self.STR_BORDER_BLOCK_STYLESHEET)

        # Top ====================================
        # self.buttonSettings = ButtonHoverSettings(self.lblToolTip, self.STR_BUTTON_SETTINGS)
        # self.buttonSettings.setVisible(True)
        # self.buttonSettings.clicked.connect(self.EventSettingsButtonClick)
        # self.buttonSettings.setFixedWidth(110)
        # self.buttonSettings.setFixedHeight(28)
        # self.buttonSettings.setStyleSheet(self.STR_QBUTTON_SETTINGS_STYLESHEET)
        # self.buttonSettings.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        # # self.buttonDonation = ButtonHoverDonation(self.lblToolTip, self.STR_BUTTON_Donation)
        # # self.buttonDonation.setVisible(True)
        # # self.buttonDonation.clicked.connect(self.EventDonationButtonClick)
        # # self.buttonDonation.setFixedWidth(110)
        # # self.buttonDonation.setFixedHeight(28)
        # # self.buttonDonation.setStyleSheet(self.STR_QBUTTON_SETTINGS_STYLESHEET)
        # # self.buttonDonation.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        # self.buttonInfo = ButtonHoverInfo(self.lblToolTip, self.STR_BUTTON_INFO)
        # self.buttonInfo.setVisible(True)
        # self.buttonInfo.clicked.connect(self.EventInfoButtonClick)
        # self.buttonInfo.setFixedWidth(110)
        # self.buttonInfo.setFixedHeight(28)
        # self.buttonInfo.setStyleSheet(self.STR_QBUTTON_SETTINGS_STYLESHEET)
        # self.buttonInfo.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        # self.lblVersion = QtGui.QLabel("Version " + str(theConfig.CONFIG_VERSION))
        # self.lblVersion = QtGui.QLabel("Cryptocurency Quantitative Trading System")
        # self.lblVersion.setStyleSheet(self.STR_QLABEL_VERSION_STYLESHEET);
        # self.lblVersion.setAlignment(QtCore.Qt.AlignLeft)
        # self.lblVersion.setFixedHeight(28)

        self.rootTopBlock = QtGui.QWidget()
        self.rootTopBlock.setStyleSheet(self.STR_BORDER_BLOCK_STYLESHEET)
        self.rootTopBlock.setFixedHeight(60)
        self.rootHboxTop = QtGui.QHBoxLayout()
        self.rootHboxTop.setContentsMargins(40, 0, 40, 0) # left, top, right, bottom
        # self.lblLogo = QtGui.QLabel("lblLogo")
        # pixmap = QtGui.QPixmap('AstibotLogo.png')
        # self.lblLogo.setPixmap(pixmap)
        # self.rootHboxTop.addWidget(self.lblLogo)
        # self.rootHboxTop.addWidget(self.lblVersion)
        # self.rootHboxTop.addWidget(self.buttonSettings, QtCore.Qt.AlignRight)
        # # self.rootHboxTop.addWidget(self.buttonDonation, QtCore.Qt.AlignRight)
        # self.rootHboxTop.addWidget(self.buttonInfo, QtCore.Qt.AlignRight)
        self.rootTopBlock.setLayout(self.rootHboxTop)
        
        self.mainGridLayout.addWidget(self.rootTopBlock, 0, 0, 1, 5)

        # Bottom ==================================
        self.rootBottomBlock = QtGui.QWidget()
        self.rootBottomBlock.setStyleSheet(self.STR_BORDER_BLOCK_STYLESHEET)
        self.rootBottomBlock.setFixedHeight(80)

        # self.FiatHboxBottom = QtGui.QHBoxLayout()
        # self.FiatHboxBottom.setContentsMargins(40, 0, 40, 0) # left, top, right, bottom
        # self.rootVboxBottomRight = QtGui.QVBoxLayout()

        self.lblToolTip.setStyleSheet(self.STR_QLABEL_TOOLTIP_STYLESHEET);
        self.lblToolTip.setWordWrap(True);
        self.lblToolTip.setFixedWidth((self.MAIN_WINDOW_WIDTH_IN_PX / 2))
        self.lblToolTip.setFixedHeight(42)
        
        self.lblConnection = QtGui.QLabel("Connection Test")
        self.lblConnection.setAlignment(QtCore.Qt.AlignRight)
        self.lblConnection.setStyleSheet(self.STR_QLABEL_CONNECTION_STATUS_STYLESHEET);
        self.lblConnection.setAlignment(QtCore.Qt.AlignRight)
        
        self.lblLiveData = QtGui.QLabel("Live Data Test")
        self.lblLiveData.setStyleSheet(self.STR_QLABEL_LIVE_DATA_STYLESHEET);
        self.lblLiveData.setAlignment(QtCore.Qt.AlignRight)


        # self.rootVboxBottomRight = QtGui.QVBoxLayout()
        # self.rootVboxBottomRight.addWidget(self.lblConnection)
        # self.rootVboxBottomRight.addWidget(self.lblLiveData)   
        # self.FiatHboxBottom.addWidget(self.lblToolTip, QtCore.Qt.AlignLeft)          
        # self.FiatHboxBottom.addWidget(self.lblCurrentState, 1, 2)
        # self.FiatHboxBottom.addWidget(self.lblInfo, 2, 2)     
        # self.FiatHboxBottom.addLayout(self.rootVboxBottomRight, 1, 1, QtCore.Qt.AlignRight)
        # self.rootBottomBlock.setLayout(self.FiatHboxBottom)
        
        self.mainGridLayout.addWidget(self.rootBottomBlock, 14, 0, 1, 5)
        
        # self.mainGridLayout.addWidget(self.lblToolTip, 3, 1, 1, 2, QtCore.Qt.AlignLeft)


        # Left and Right
        self.rootLeftBlock = QtGui.QWidget()
        self.rootLeftBlock.setStyleSheet(self.STR_BORDER_BLOCK_STYLESHEET)
        self.rootLeftBlock.setFixedWidth(40)
        self.rootRightBlock = QtGui.QWidget()
        self.rootRightBlock.setStyleSheet(self.STR_BORDER_BLOCK_STYLESHEET)
        self.rootRightBlock.setFixedWidth(40)
        self.mainGridLayout.addWidget(self.rootLeftBlock, 0, 0, 14, 1)
        self.mainGridLayout.addWidget(self.rootRightBlock, 0, 5, 14, 1)


    def initializeTopWindowWidgets(self):

        # Pre requisite for further inits
        self.lblToolTip = QtGui.QLabel("");

        self.rootMiddleBlock1 = QtGui.QWidget()
        self.rootMiddleBlock1.setStyleSheet(self.STR_BORDER_BLOCK_STYLESHEET)
        self.rootMiddleBlock1.setFixedHeight(15)
        self.rootMiddleBlock2 = QtGui.QWidget()
        self.rootMiddleBlock2.setStyleSheet(self.STR_BORDER_BLOCK_STYLESHEET)
        self.rootMiddleBlock2.setFixedHeight(15)

        # Part 1
        self.hBox1 = QtGui.QHBoxLayout()
        self.vBoxRootButtons = QtGui.QVBoxLayout()
        self.vBoxRadioModeButtons = QtGui.QVBoxLayout()
        self.vBoxSliders = QtGui.QVBoxLayout()
        self.hBoxSliders1 = QtGui.QHBoxLayout()
        self.hBoxSliders2 = QtGui.QHBoxLayout()
        self.hBox1.setSpacing(10)

        self.buttonSettings = ButtonHoverSettings(self.lblToolTip, self.STR_BUTTON_SETTINGS)
        self.buttonSettings.setVisible(True)
        self.buttonSettings.clicked.connect(self.EventSettingsButtonClick)
        self.buttonSettings.setFixedWidth(110)
        self.buttonSettings.setFixedHeight(28)
        self.buttonSettings.setStyleSheet(self.STR_QBUTTON_SETTINGS_STYLESHEET)
        self.buttonSettings.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        # self.buttonDonation = ButtonHoverDonation(self.lblToolTip, self.STR_BUTTON_Donation)
        # self.buttonDonation.setVisible(True)
        # self.buttonDonation.clicked.connect(self.EventDonationButtonClick)
        # self.buttonDonation.setFixedWidth(110)
        # self.buttonDonation.setFixedHeight(28)
        # self.buttonDonation.setStyleSheet(self.STR_QBUTTON_SETTINGS_STYLESHEET)
        # self.buttonDonation.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        # self.buttonInfo = ButtonHoverInfo(self.lblToolTip, self.STR_BUTTON_INFO)
        # self.buttonInfo.setVisible(True)
        # self.buttonInfo.clicked.connect(self.EventInfoButtonClick)
        # self.buttonInfo.setFixedWidth(110)
        # self.buttonInfo.setFixedHeight(28)
        # self.buttonInfo.setStyleSheet(self.STR_QBUTTON_SETTINGS_STYLESHEET)
        # self.buttonInfo.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.radioButtonSimulation = RadioHoverSimulation(self.lblToolTip, self.STR_RADIO_SIMULATION)
        self.radioButtonSimulation.setChecked(False)
        # self.radioButtonSimulation.setFixedWidth(200)
        self.radioButtonSimulation.setStyleSheet(self.STR_QRADIOBUTTON_STYLESHEET);
        self.radioButtonSimulation.toggled.connect(self.EventRadioModeToggle)
        self.radioButtonSimulation.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.radioButtonTrading = RadioHoverTrading(self.lblToolTip, self.STR_RADIO_TRADING)
        self.radioButtonTrading.setChecked(True)
        # self.radioButtonTrading.setFixedWidth(200)
        self.radioButtonTrading.setStyleSheet(self.STR_QRADIOBUTTON_STYLESHEET);
        self.radioButtonTrading.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.buttonPause = ButtonHoverPause(self.lblToolTip, self.STR_BUTTON_PAUSE)
        self.buttonPause.setVisible(True)
        self.buttonPause.clicked.connect(self.EventPauseButtonClick)
        # self.buttonPause.setFixedWidth(80)
        self.buttonPause.setFixedHeight(60)
        self.buttonPause.setStyleSheet(self.STR_QBUTTON_PAUSE_STYLESHEET)
        self.buttonPause.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.buttonStart = ButtonHoverStart(self.lblToolTip, self.STR_BUTTON_START)
        self.buttonStart.setVisible(True)
        self.buttonStart.clicked.connect(self.EventStartButtonClick)
        # self.buttonStart.setFixedWidth(80)
        self.buttonStart.setFixedHeight(60)
        self.buttonStart.setStyleSheet(self.STR_QBUTTON_START_STYLESHEET)   
        self.buttonStart.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.vBoxRootButtons.addWidget(self.buttonSettings, QtCore.Qt.AlignRight)
        # self.vBoxRootButtons.addWidget(self.buttonDonation, QtCore.Qt.AlignRight)
        # self.vBoxRootButtons.addWidget(self.buttonInfo, QtCore.Qt.AlignRight)
        self.vBoxRadioModeButtons.addWidget(self.radioButtonSimulation)
        self.vBoxRadioModeButtons.addWidget(self.radioButtonTrading)
        self.hBox1.addLayout(self.vBoxRadioModeButtons)
        self.hBox1.addWidget(self.buttonPause)
        self.hBox1.addWidget(self.buttonStart)
        self.hBox1.addLayout(self.vBoxRootButtons)

        # Slider Risk level
        riskPercent = round((theConfig.CONFIG_RiskLinePercentsAboveThresholdToBuy - 1) * 100, 1)
        self.lblRiskLevelSlider1 = QtGui.QLabel("Risk level: %s%%" % str(riskPercent));
        # self.lblRiskLevelSlider1.setFixedWidth(140)
        self.lblRiskLevelSlider2 = QtGui.QLabel("Low");
        # self.lblRiskLevelSlider2.setFixedWidth(30);
        self.lblRiskLevelSlider3 = QtGui.QLabel("High");
        # self.lblRiskLevelSlider3.setFixedWidth(30)
        self.sliderRiskLevel = SliderHoverRiskLevel(self.lblToolTip, QtCore.Qt.Horizontal)
        self.sliderRiskLevel.setMinimum(0)
        self.sliderRiskLevel.setMaximum(100)
        self.sliderRiskLevel.setFixedWidth(250)
        self.sliderRiskLevel.setValue(round((theConfig.CONFIG_RiskLinePercentsAboveThresholdToBuy - theConfig.CONFIG_RISK_LINE_PERCENTS_ABOVE_THRESHOLD_TO_BUY_MIN) * 100 / (theConfig.CONFIG_RISK_LINE_PERCENTS_ABOVE_THRESHOLD_TO_BUY_MAX - theConfig.CONFIG_RISK_LINE_PERCENTS_ABOVE_THRESHOLD_TO_BUY_MIN)))
        self.sliderRiskLevel.valueChanged.connect(self.EventMovedSliderRiskLevel)
        self.sliderRiskLevel.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.EventMovedSliderRiskLevel() # Refresh trading parameter according to slider initial position
        self.lblRiskLevelSlider1.setStyleSheet(self.STR_QLABEL_STYLESHEET)
        self.lblRiskLevelSlider2.setStyleSheet(self.STR_QLABEL_STYLESHEET)
        self.lblRiskLevelSlider3.setStyleSheet(self.STR_QLABEL_STYLESHEET)
        self.sliderRiskLevel.setStyleSheet(self.STR_QSLIDER_STYLESHEET)

        # self.lblSensitivityLevelSlider1 = QtGui.QLabel("Dips sensitivity: ");
        # self.lblSensitivityLevelSlider1.setFixedWidth(140)
        # self.lblSensitivityLevelSlider2 = QtGui.QLabel("Low");
        # self.lblSensitivityLevelSlider2.setFixedWidth(30)
        # self.lblSensitivityLevelSlider3 = QtGui.QLabel("High");
        # self.lblSensitivityLevelSlider3.setFixedWidth(30)
        # self.sliderSensitivityLevel = SliderHoverSensitivityLevel(self.lblToolTip, QtCore.Qt.Horizontal)
        # self.sliderSensitivityLevel.setMinimum(1)
        # self.sliderSensitivityLevel.setMaximum(6)
        # self.sliderSensitivityLevel.setTickInterval(1)
        # self.sliderSensitivityLevel.setSingleStep(1)
        # self.sliderSensitivityLevel.setFixedWidth(130)
        # self.sliderSensitivityLevel.setValue(self.currentSensitivitySliderValue)
        # self.sliderSensitivityLevel.setTickPosition(QtGui.QSlider.TicksBelow)
        # self.sliderSensitivityLevel.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        # self.sliderSensitivityLevel.valueChanged.connect(self.EventMovedSliderSensitivityLevel)
        # self.lblSensitivityLevelSlider1.setStyleSheet(self.STR_QLABEL_STYLESHEET)
        # self.lblSensitivityLevelSlider2.setStyleSheet(self.STR_QLABEL_STYLESHEET)
        # self.lblSensitivityLevelSlider3.setStyleSheet(self.STR_QLABEL_STYLESHEET)
        # self.sliderSensitivityLevel.setStyleSheet(self.STR_QSLIDER_STYLESHEET)

        # self.vBoxSliders.addLayout(self.hBoxSliders2, QtCore.Qt.AlignLeft)
        self.hBoxSliders1.addWidget(self.lblRiskLevelSlider1, QtCore.Qt.AlignLeft)
        self.hBoxSliders1.addWidget(self.lblRiskLevelSlider2)
        self.hBoxSliders1.addWidget(self.sliderRiskLevel)
        self.hBoxSliders1.addWidget(self.lblRiskLevelSlider3)
        # self.hBoxSliders2.addWidget(self.lblSensitivityLevelSlider1, QtCore.Qt.AlignLeft)
        # self.hBoxSliders2.addWidget(self.lblSensitivityLevelSlider2)
        # self.hBoxSliders2.addWidget(self.sliderSensitivityLevel)
        # self.hBoxSliders2.addWidget(self.lblSensitivityLevelSlider3)

        self.vBoxSliders.addLayout(self.hBoxSliders1, QtCore.Qt.AlignLeft)
        
        # Part 2
        self.StatsVBox = QtGui.QVBoxLayout()
        self.lblLivePrice = QtGui.QLabel()
        self.STR_LABEL_MONEY_MIDDLEMARKET_PRICE = self.theSettings.SETT_GetSettings()["strCryptoType"] + str(" ") + str(self.STR_LABEL_MONEY_MIDDLEMARKET_PRICE)
        self.lblLivePrice.setText(self.STR_LABEL_MONEY_MIDDLEMARKET_PRICE)
        self.lblLivePrice.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        
        self.lblTotalGains = QtGui.QLabel(self.STR_LABEL_TOTAL_GAINS)
        self.lblTotalGains.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        
        self.StatsVBox.addWidget(self.lblLivePrice, QtCore.Qt.AlignLeft)
        self.StatsVBox.addWidget(self.lblTotalGains, QtCore.Qt.AlignLeft)
        
        self.lblCryptoAbbr = QtGui.QLabel(str(self.theSettings.SETT_GetSettings()["strCryptoType"]))
        self.lblCryptoAbbr.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblCryptoMoneyBalance = QtGui.QLabel(self.STR_LABEL_CRYPTO_BALANCE)
        self.lblCryptoMoneyBalance.setStyleSheet(self.STR_QLABEL_BALANCE_STYLESHEET);
        
        self.lblCryptoLogo = QtGui.QLabel("lblLogo")
        pixmap = QtGui.QPixmap('logos/' + str(self.theSettings.SETT_GetSettings()["strCryptoType"]) + 'Logo.png')
        smaller_pixmap = pixmap.scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
        self.lblCryptoLogo.setPixmap(smaller_pixmap)
        
        self.CryptoHbox = QtGui.QHBoxLayout()
        # self.FiatHbox.setContentsMargins(40, 10, 40, 0) #
        self.CryptoVboxRight = QtGui.QVBoxLayout()
        
        self.CryptoVboxRight.addWidget(self.lblCryptoAbbr)
        self.CryptoVboxRight.addWidget(self.lblCryptoMoneyBalance)
        self.CryptoHbox.addWidget(self.lblCryptoLogo, QtCore.Qt.AlignLeft)
        self.CryptoHbox.addLayout(self.CryptoVboxRight, QtCore.Qt.AlignRight)
        
        self.CryptoBlock = QtGui.QWidget()
        self.CryptoBlock.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        # self.CryptoBlock.setFixedHeight(80)
        self.CryptoBlock.setLayout(self.CryptoHbox)
        

        self.lblFiatAbbr = QtGui.QLabel(str(self.theSettings.SETT_GetSettings()["strFiatType"]))
        self.lblFiatAbbr.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblFiatBalance = QtGui.QLabel(self.STR_LABEL_FIAT_BALANCE)
        self.lblFiatBalance.setStyleSheet(self.STR_QLABEL_BALANCE_STYLESHEET);
        
        self.lblFiatLogo = QtGui.QLabel("lblLogo")
        pixmap = QtGui.QPixmap('logos/' + str(self.theSettings.SETT_GetSettings()["strFiatType"]) + 'Logo.png')
        smaller_pixmap = pixmap.scaled(64, 64, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation)
        self.lblFiatLogo.setPixmap(smaller_pixmap)
        
        self.FiatHbox = QtGui.QHBoxLayout()
        # self.FiatHbox.setContentsMargins(40, 10, 40, 0) #
        self.FiatVboxRight = QtGui.QVBoxLayout()
        
        self.FiatVboxRight.addWidget(self.lblFiatAbbr)
        self.FiatVboxRight.addWidget(self.lblFiatBalance)
        self.FiatHbox.addWidget(self.lblFiatLogo, QtCore.Qt.AlignLeft)
        self.FiatHbox.addLayout(self.FiatVboxRight, QtCore.Qt.AlignRight)
        
        self.FiatBlock = QtGui.QWidget()
        self.FiatBlock.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        # self.FiatBlock.setFixedHeight(80)
        self.FiatBlock.setLayout(self.FiatHbox)
        
        # part 3 - transaction history
        self.rowHeadingHbox = QtGui.QHBoxLayout()
        self.row1Hbox = QtGui.QHBoxLayout()
        self.row2Hbox = QtGui.QHBoxLayout()
        self.row3Hbox = QtGui.QHBoxLayout()
        self.row4Hbox = QtGui.QHBoxLayout()
        self.row5Hbox = QtGui.QHBoxLayout()
        self.row6Hbox = QtGui.QHBoxLayout()
        self.row7Hbox = QtGui.QHBoxLayout()
        self.historyVbox = QtGui.QVBoxLayout()
        
        self.lblTradePair = QtGui.QLabel("TradePair")
        self.lblOperation = QtGui.QLabel("Operation")
        self.lblTransPrice = QtGui.QLabel("Price")
        self.lblTransAmount = QtGui.QLabel("Amount")
        self.lblTransTime = QtGui.QLabel("Time")
        self.lblTradePair.setFixedWidth(110)
        self.lblOperation.setFixedWidth(110)
        self.lblTransPrice.setFixedWidth(110)
        self.lblTransAmount.setFixedWidth(110)
        self.lblTransTime.setFixedWidth(130)
        self.lblTradePair.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblOperation.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblTransPrice.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblTransAmount.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblTransTime.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.rowHeadingHbox.addWidget(self.lblTradePair, QtCore.Qt.AlignLeft)
        self.rowHeadingHbox.addWidget(self.lblOperation, QtCore.Qt.AlignLeft)
        self.rowHeadingHbox.addWidget(self.lblTransPrice, QtCore.Qt.AlignLeft)
        self.rowHeadingHbox.addWidget(self.lblTransAmount, QtCore.Qt.AlignLeft)
        self.rowHeadingHbox.addWidget(self.lblTransTime, QtCore.Qt.AlignLeft)
        self.rowHeadingBlock = QtGui.QWidget()
        self.rowHeadingBlock.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        self.rowHeadingBlock.setLayout(self.rowHeadingHbox)
        
        self.lblLast1TransTradePair = QtGui.QLabel("")
        self.lblLast1TransOperation = QtGui.QLabel("")
        self.lblLast1TransPrice = QtGui.QLabel("")
        self.lblLast1TransAmount = QtGui.QLabel("")
        self.lblLast1TransTime = QtGui.QLabel("")
        self.lblLast1TransTradePair.setFixedWidth(110)
        self.lblLast1TransOperation.setFixedWidth(110)
        self.lblLast1TransPrice.setFixedWidth(110)
        self.lblLast1TransAmount.setFixedWidth(110)
        self.lblLast1TransTime.setFixedWidth(130)
        self.lblLast1TransTradePair.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast1TransOperation.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast1TransPrice.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast1TransAmount.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast1TransTime.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.row1Hbox.addWidget(self.lblLast1TransTradePair, QtCore.Qt.AlignLeft)
        self.row1Hbox.addWidget(self.lblLast1TransOperation, QtCore.Qt.AlignLeft)
        self.row1Hbox.addWidget(self.lblLast1TransPrice, QtCore.Qt.AlignLeft)
        self.row1Hbox.addWidget(self.lblLast1TransAmount, QtCore.Qt.AlignLeft)
        self.row1Hbox.addWidget(self.lblLast1TransTime, QtCore.Qt.AlignLeft)
        self.row1Block = QtGui.QWidget()
        self.row1Block.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        self.row1Block.setLayout(self.row1Hbox)

        self.lblLast2TransTradePair = QtGui.QLabel("")
        self.lblLast2TransOperation = QtGui.QLabel("")
        self.lblLast2TransPrice = QtGui.QLabel("")
        self.lblLast2TransAmount = QtGui.QLabel("")
        self.lblLast2TransTime = QtGui.QLabel("")
        self.lblLast2TransTradePair.setFixedWidth(110)
        self.lblLast2TransOperation.setFixedWidth(110)
        self.lblLast2TransPrice.setFixedWidth(110)
        self.lblLast2TransAmount.setFixedWidth(110)
        self.lblLast2TransTime.setFixedWidth(130)
        self.lblLast2TransTradePair.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast2TransOperation.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast2TransPrice.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast2TransAmount.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast2TransTime.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.row2Hbox.addWidget(self.lblLast2TransTradePair, QtCore.Qt.AlignLeft)
        self.row2Hbox.addWidget(self.lblLast2TransOperation, QtCore.Qt.AlignLeft)
        self.row2Hbox.addWidget(self.lblLast2TransPrice, QtCore.Qt.AlignLeft)
        self.row2Hbox.addWidget(self.lblLast2TransAmount, QtCore.Qt.AlignLeft)
        self.row2Hbox.addWidget(self.lblLast2TransTime, QtCore.Qt.AlignLeft)
        self.row2Block = QtGui.QWidget()
        self.row2Block.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        self.row2Block.setLayout(self.row2Hbox)
        
        self.lblLast3TransTradePair = QtGui.QLabel("")
        self.lblLast3TransOperation = QtGui.QLabel("")
        self.lblLast3TransPrice = QtGui.QLabel("")
        self.lblLast3TransAmount = QtGui.QLabel("")
        self.lblLast3TransTime = QtGui.QLabel("")
        self.lblLast3TransOperation.setFixedWidth(110)
        self.lblLast3TransPrice.setFixedWidth(110)
        self.lblLast3TransAmount.setFixedWidth(110)
        self.lblLast3TransTradePair.setFixedWidth(110)
        self.lblLast3TransTime.setFixedWidth(130)
        self.lblLast3TransTradePair.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast3TransOperation.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast3TransPrice.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast3TransAmount.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast3TransTime.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.row3Hbox.addWidget(self.lblLast3TransTradePair, QtCore.Qt.AlignLeft)
        self.row3Hbox.addWidget(self.lblLast3TransOperation, QtCore.Qt.AlignLeft)
        self.row3Hbox.addWidget(self.lblLast3TransPrice, QtCore.Qt.AlignLeft)
        self.row3Hbox.addWidget(self.lblLast3TransAmount, QtCore.Qt.AlignLeft)
        self.row3Hbox.addWidget(self.lblLast3TransTime, QtCore.Qt.AlignLeft)
        self.row3Block = QtGui.QWidget()
        self.row3Block.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        self.row3Block.setLayout(self.row3Hbox)
        
        self.lblLast4TransTradePair = QtGui.QLabel("")
        self.lblLast4TransOperation = QtGui.QLabel("")
        self.lblLast4TransPrice = QtGui.QLabel("")
        self.lblLast4TransAmount = QtGui.QLabel("")
        self.lblLast4TransTime = QtGui.QLabel("")
        self.lblLast4TransTradePair.setFixedWidth(110)
        self.lblLast4TransOperation.setFixedWidth(110)
        self.lblLast4TransPrice.setFixedWidth(110)
        self.lblLast4TransAmount.setFixedWidth(110)
        self.lblLast4TransTime.setFixedWidth(130)
        self.lblLast4TransTradePair.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast4TransOperation.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast4TransPrice.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast4TransAmount.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast4TransTime.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.row4Hbox.addWidget(self.lblLast4TransTradePair, QtCore.Qt.AlignLeft)
        self.row4Hbox.addWidget(self.lblLast4TransOperation, QtCore.Qt.AlignLeft)
        self.row4Hbox.addWidget(self.lblLast4TransPrice, QtCore.Qt.AlignLeft)
        self.row4Hbox.addWidget(self.lblLast4TransAmount, QtCore.Qt.AlignLeft)
        self.row4Hbox.addWidget(self.lblLast4TransTime, QtCore.Qt.AlignLeft)
        self.row4Block = QtGui.QWidget()
        self.row4Block.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        self.row4Block.setLayout(self.row4Hbox)
        
        self.lblLast5TransTradePair = QtGui.QLabel("")
        self.lblLast5TransOperation = QtGui.QLabel("")
        self.lblLast5TransPrice = QtGui.QLabel("")
        self.lblLast5TransAmount = QtGui.QLabel("")
        self.lblLast5TransTime = QtGui.QLabel("")
        self.lblLast5TransTradePair.setFixedWidth(110)
        self.lblLast5TransOperation.setFixedWidth(110)
        self.lblLast5TransPrice.setFixedWidth(110)
        self.lblLast5TransAmount.setFixedWidth(110)
        self.lblLast5TransTime.setFixedWidth(130)
        self.lblLast5TransTradePair.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast5TransOperation.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast5TransPrice.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast5TransAmount.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast5TransTime.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.row5Hbox.addWidget(self.lblLast5TransTradePair, QtCore.Qt.AlignLeft)
        self.row5Hbox.addWidget(self.lblLast5TransOperation, QtCore.Qt.AlignLeft)
        self.row5Hbox.addWidget(self.lblLast5TransPrice, QtCore.Qt.AlignLeft)
        self.row5Hbox.addWidget(self.lblLast5TransAmount, QtCore.Qt.AlignLeft)
        self.row5Hbox.addWidget(self.lblLast5TransTime, QtCore.Qt.AlignLeft)
        self.row5Block = QtGui.QWidget()
        self.row5Block.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        self.row5Block.setLayout(self.row5Hbox)
        
        self.lblLast6TransTradePair = QtGui.QLabel("")
        self.lblLast6TransOperation = QtGui.QLabel("")
        self.lblLast6TransPrice = QtGui.QLabel("")
        self.lblLast6TransAmount = QtGui.QLabel("")
        self.lblLast6TransTime = QtGui.QLabel("")
        self.lblLast6TransTradePair.setFixedWidth(110)
        self.lblLast6TransOperation.setFixedWidth(110)
        self.lblLast6TransPrice.setFixedWidth(110)
        self.lblLast6TransAmount.setFixedWidth(110)
        self.lblLast6TransTime.setFixedWidth(130)
        self.lblLast6TransTradePair.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast6TransOperation.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast6TransPrice.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast6TransAmount.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast6TransTime.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.row6Hbox.addWidget(self.lblLast6TransTradePair, QtCore.Qt.AlignLeft)
        self.row6Hbox.addWidget(self.lblLast6TransOperation, QtCore.Qt.AlignLeft)
        self.row6Hbox.addWidget(self.lblLast6TransPrice, QtCore.Qt.AlignLeft)
        self.row6Hbox.addWidget(self.lblLast6TransAmount, QtCore.Qt.AlignLeft)
        self.row6Hbox.addWidget(self.lblLast6TransTime, QtCore.Qt.AlignLeft)
        self.row6Block = QtGui.QWidget()
        self.row6Block.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        self.row6Block.setLayout(self.row6Hbox)
        
        self.lblLast7TransTradePair = QtGui.QLabel("")
        self.lblLast7TransOperation = QtGui.QLabel("")
        self.lblLast7TransPrice = QtGui.QLabel("")
        self.lblLast7TransAmount = QtGui.QLabel("")
        self.lblLast7TransTime = QtGui.QLabel("")
        self.lblLast7TransTradePair.setFixedWidth(110)
        self.lblLast7TransOperation.setFixedWidth(110)
        self.lblLast7TransPrice.setFixedWidth(110)
        self.lblLast7TransAmount.setFixedWidth(110)
        self.lblLast7TransTime.setFixedWidth(130)
        self.lblLast7TransTradePair.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast7TransOperation.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast7TransPrice.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast7TransAmount.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblLast7TransTime.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.row7Hbox.addWidget(self.lblLast7TransTradePair, QtCore.Qt.AlignLeft)
        self.row7Hbox.addWidget(self.lblLast7TransOperation, QtCore.Qt.AlignLeft)
        self.row7Hbox.addWidget(self.lblLast7TransPrice, QtCore.Qt.AlignLeft)
        self.row7Hbox.addWidget(self.lblLast7TransAmount, QtCore.Qt.AlignLeft)
        self.row7Hbox.addWidget(self.lblLast7TransTime, QtCore.Qt.AlignLeft)
        self.row7Block = QtGui.QWidget()
        self.row7Block.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        self.row7Block.setLayout(self.row7Hbox)
        # self.historyVbox.addLayout(self.rowHeadingHbox, QtCore.Qt.AlignRight)
        # self.historyVbox.addLayout(self.row1Hbox, QtCore.Qt.AlignRight)
        # self.historyVbox.addLayout(self.row2Hbox, QtCore.Qt.AlignRight)
        # self.historyVbox.addLayout(self.row3Hbox, QtCore.Qt.AlignRight)
        # self.historyVbox.addLayout(self.row4Hbox, QtCore.Qt.AlignRight)

        # self.HistoryBlock = QtGui.QWidget()
        # self.HistoryBlock.setStyleSheet(self.STR_USER_BLOCK_STYLESHEET)
        # # self.CryptoBlock.setFixedHeight(80)
        # self.HistoryBlock.setLayout(self.row1Hbox)
        # self.HistoryBlock.setLayout(self.row2Hbox)
        
        #   moving
        self.lblCurrentState = QtGui.QLabel(self.STR_LABEL_CURRENT_STATE)
        self.lblCurrentState.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblCurrentState.setWordWrap(True);
        # self.lblCurrentState.setFixedWidth((self.MAIN_WINDOW_WIDTH_IN_PX / 2))
        self.lblInfo = LabelClickable(self.STR_LABEL_INFO)
        # self.lblInfo.setFixedHeight(42)
        self.lblInfo.setStyleSheet(self.STR_QLABEL_STYLESHEET);
        self.lblInfo.setWordWrap(True);
        # self.lblInfo.setFixedWidth((self.MAIN_WINDOW_WIDTH_IN_PX / 2))
        # Add widgets to layout
        self.mainGridLayout = QtGui.QGridLayout()   

        self.mainGridLayout.addWidget(self.FiatBlock, 1, 1)
        self.mainGridLayout.addWidget(self.CryptoBlock, 1, 2)
        self.mainGridLayout.addLayout(self.StatsVBox, 1, 3)
        self.ControlVBox = QtGui.QVBoxLayout()
        self.ControlVBox.addLayout(self.hBox1, QtCore.Qt.AlignLeft)
        self.ControlVBox.addLayout(self.vBoxSliders, QtCore.Qt.AlignLeft)
        self.mainGridLayout.addLayout(self.ControlVBox, 1, 4, QtCore.Qt.AlignLeft)
        
        # self.mainGridLayout.addLayout(self.historyVbox, 4, 4, QtCore.Qt.AlignCenter)
        

        self.mainGridLayout.addWidget(self.rowHeadingBlock, 3, 4, QtCore.Qt.AlignCenter)
        self.mainGridLayout.addWidget(self.row1Block, 4, 4, QtCore.Qt.AlignCenter)
        self.mainGridLayout.addWidget(self.row2Block, 5, 4, QtCore.Qt.AlignCenter)
        self.mainGridLayout.addWidget(self.row3Block, 6, 4, QtCore.Qt.AlignCenter)
        self.mainGridLayout.addWidget(self.row4Block, 7, 4, QtCore.Qt.AlignCenter)
        self.mainGridLayout.addWidget(self.row5Block, 8, 4, QtCore.Qt.AlignCenter)
        self.mainGridLayout.addWidget(self.row6Block, 9, 4, QtCore.Qt.AlignCenter)
        self.mainGridLayout.addWidget(self.row7Block, 10, 4, QtCore.Qt.AlignCenter)
        
        self.mainGridLayout.addWidget(self.lblCurrentState, 12, 4, QtCore.Qt.AlignCenter)
        self.mainGridLayout.addWidget(self.lblInfo, 13, 4, QtCore.Qt.AlignCenter)
        
        self.mainGridLayout.setRowStretch(1, 0)
        self.mainGridLayout.setRowStretch(11, 1)
        # self.mainGridLayout.setRowStretch(9, 5)
        # self.mainGridLayout.setColumnStretch(0, 0)
        # self.mainGridLayout.setColumnStretch(4, 2)

        # self.mainGridLayout.addWidget(self.rootMiddleBlock1, 5, 0, 1, 4)
        # self.mainGridLayout.addWidget(self.lblFiatBalance, 1, 1, QtCore.Qt.AlignLeft)
        # self.mainGridLayout.addWidget(self.lblCryptoMoneyBalance, 2, 1, QtCore.Qt.AlignLeft)
        # self.mainGridLayout.addWidget(self.lblLivePrice, 3, 2)
        # self.mainGridLayout.addWidget(self.lblTotalGains, 4, 2, QtCore.Qt.AlignLeft)
        # self.mainGridLayout.addLayout(self.vBoxRootButtons, 1, 4, QtCore.Qt.AlignCenter)
        
        # self.mainGridLayout.addLayout(self.hBox1, 1, 3, QtCore.Qt.AlignCenter)
        # self.mainGridLayout.addLayout(self.vBoxSliders, 2, 3, 1, 1, QtCore.Qt.AlignCenter)
        

        # self.mainGridLayout.addWidget(self.rootMiddleBlock2, 7, 0, 1, 4)
        
        
        # Each column of the grid layout has the same total width proportion
        # self.mainGridLayout.setColumnStretch(1, 1)
        # self.mainGridLayout.setColumnStretch(2, 5)
        # self.mainGridLayout.setColumnStretch(3, 10)

    def initializeGraphWidgets(self):

        pg.setConfigOption('foreground', 'w')
        pg.setConfigOption('background', (31, 31, 31))
        pg.GraphicsLayout(border=(31,31,31))
        
        self.strPlot1Title = str(self.theSettings.SETT_GetSettings()["strCryptoType"]) + ' Market Overview (' + str(self.theSettings.SETT_GetSettings()["strFiatType"]) + ')'
        self.plot1 = pg.PlotWidget(title=self.strPlot1Title, axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self.plot1.setYRange(self.minInPlot1, self.maxInPlot1)
        self.plot1.setMouseEnabled(True, True) # Mettre False, True pour release
        self.plot1.setMenuEnabled(False)
        self.plot1.showGrid(x=True, y=True, alpha=0.2)
        fontForTickValues = QtGui.QFont()
        fontForTickValues.setPixelSize(20)
        # fontForTickValues.setBold(True)
        axis = self.plot1.getAxis('bottom')  # This is the trick
        axis.setStyle(textFillLimits = [(0, 0.7)], tickFont = fontForTickValues)
        axis = self.plot1.getAxis('left')  # This is the trick
        axis.setStyle(tickFont = fontForTickValues)

        # self.plot1.plotItem.vb.setBackgroundColor((15, 25, 34, 255))
        # self.plot2 = pg.PlotWidget(title='Astibot decision indicator (normalized)')
        # self.plot2.showGrid(x=True,y=True,alpha=0.1)
        # self.plot2.setYRange(-100, 100)
        # self.plot2.setMouseEnabled(False, True)
        # self.plot2.setMouseEnabled(False)
        # self.plot2.hideAxis('bottom')
        
        # Graphs take one row but 2 columns
        self.mainGridLayout.addWidget(self.plot1, 2, 1, 12, 3)
        # self.mainGridLayout.addWidget(self.plot2, 10, 1, 1, 2)
   
        # Graph curves initialization
        self.plot1GraphLivePrice = self.plot1.plot(x=self.graphDataTime, y=self.graphDataBitcoinPrice, name='     Price') # , clipToView=True
        self.plot1GraphLivePrice.setPen(color=(97,54,142), width=3)
        # self.plot1GraphSmoothPriceFast = self.plot1.plot(x=self.graphDataTime, y=self.graphDataBitcoinPriceSmoothFast, name='    Price Fast MA')
        # self.plot1GraphSmoothPriceFast.setPen(color=(3,86,243), width=2)
        # self.plot1GraphSmoothPriceSlow = self.plot1.plot(x=self.graphDataTime, y=self.graphDataBitcoinPriceSmoothSlow, name='    Price Slow MA')
        # self.plot1GraphSmoothPriceSlow.setPen(color=(230,79,6), width=2)        
        # self.plot1GraphRiskLine = self.plot1.plot(x=self.graphDataTime, y=self.graphDataBitcoinRiskLine, name='    Risk Line')
        # self.plot1GraphRiskLine.setPen(color=(255,46,46), width=2, style=QtCore.Qt.DotLine)
        self.plot1Markers1 = self.plot1.plot(x=self.graphDataTime, y=self.graphDataBitcoinPriceMarker1, name='      Buy', pen=None, symbol='o', symbolPen=(0, 255, 0), symbolBrush=(0, 255, 0), symbolSize = 3)
        self.plot1Markers2 = self.plot1.plot(x=self.graphDataTime, y=self.graphDataBitcoinPriceMarker2, name='      Sell', pen=None, symbol='o', symbolPen=(255, 0, 0), symbolBrush=(255, 0, 0), symbolSize = 3)

        # Graph 2 (Indicators) curves initialization
        # self.plot2GraphIndicatorMACD = self.plot2.plot(x=self.graphDataTime, y=self.graphDataIndicatorMACD, pen='y', name='     MACD')
        self.graphicObject = pg.GraphicsObject()

    def initInitialTimeVector(self, firstFutureSampleTimeStamp):
        np.set_printoptions(suppress=True)
        timeBetweenRetrievedSamplesInSec = 60
        startTimeValue = firstFutureSampleTimeStamp - (self.nbPointsOnPlot * timeBetweenRetrievedSamplesInSec)
        tempTimeVector = np.linspace(startTimeValue, firstFutureSampleTimeStamp, self.nbPointsOnPlot)
        self.timeOfLastSampleDisplayed = startTimeValue

        return tempTimeVector


    def UIGR_updateNextIterationData(self, newTime, newSpotPrice, newSmoothPriceFast, newSmoothPriceSlow, newRiskLineRawAvgValue, newIndicatorMACD):
        # Don't append data that were before the oldest time in the graphs and that are older than the last sample displayed
        if (newTime > self.timeOfLastSampleDisplayed):

            self.graphDataTime[-1] = newTime
            self.timeOfLastSampleDisplayed = newTime
            self.graphDataBitcoinPrice[-1] = newSpotPrice
            self.graphDataBitcoinPriceSmoothFast[-1] = newSmoothPriceFast
            self.graphDataBitcoinPriceSmoothSlow[-1] = newSmoothPriceSlow
            self.graphDataBitcoinPriceMarker1[-1] = 0
            self.graphDataBitcoinPriceMarker2[-1] = 0
            self.currentRiskLineRawAvgValue = newRiskLineRawAvgValue
            self.graphDataBitcoinRiskLine.fill(newRiskLineRawAvgValue * theConfig.CONFIG_RiskLinePercentsAboveThresholdToBuy)

            self.graphDataIndicatorMACD[-1] = newIndicatorMACD

            # Shift data in the array one sample left (see also: np.roll)
            self.graphDataTime[:-1] = self.graphDataTime[1:]
            self.graphDataBitcoinPrice[:-1] = self.graphDataBitcoinPrice[1:]
            self.graphDataBitcoinPriceSmoothFast[:-1] = self.graphDataBitcoinPriceSmoothFast[1:]
            self.graphDataBitcoinPriceSmoothSlow[:-1] = self.graphDataBitcoinPriceSmoothSlow[1:]
            self.graphDataBitcoinPriceMarker1[:-1] = self.graphDataBitcoinPriceMarker1[1:]
            self.graphDataBitcoinPriceMarker2[:-1] = self.graphDataBitcoinPriceMarker2[1:]
            self.graphDataBitcoinRiskLine[:-1] = self.graphDataBitcoinRiskLine[1:]
            self.graphDataIndicatorMACD[:-1] = self.graphDataIndicatorMACD[1:]

            self.totalNbIterations = self.totalNbIterations + 1


    # Experimentation pour live trading aussi
    def UIGR_updateGraphsSimuTimer(self):
        if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == False):
            if (self.totalNbIterations > theConfig.CONFIG_NB_POINTS_INIT_SIMU_GRAPH):
                self.UIGR_updateGraphs()
                self.totalNbGraphUpdates = self.totalNbGraphUpdates + 1

                # Perform UI apdates that were requested from the background thread
                self.UIGR_SAFE_updatePriceLbl()

                if (self.safeUIRefreshIsRequested == True):
                    self.safeUIRefreshIsRequested = False
                    self.UIGR_SAFE_updateInfoText()
                    self.UIGR_SAFE_updateTotalProfit()
                    self.UIGR_SAFE_updateAccountsBalance()
        else:
            self.UIGR_updateGraphs()

            # Perform UI updates that were requested from the background thread
            self.UIGR_SAFE_updatePriceLbl()

            if (self.safeUIRefreshIsRequested == True):
                self.safeUIRefreshIsRequested = False
                self.UIGR_SAFE_updateInfoText()
                self.UIGR_SAFE_updateTotalProfit()
                self.UIGR_SAFE_updateAccountsBalance()


    def UIGR_updateGraphs(self):

        self.plot1GraphLivePrice.setData(x=self.graphDataTime, y=self.graphDataBitcoinPrice)
        # self.plot1GraphSmoothPriceFast.setData(x=self.graphDataTime, y=self.graphDataBitcoinPriceSmoothFast)
        # self.plot1GraphSmoothPriceSlow.setData(x=self.graphDataTime, y=self.graphDataBitcoinPriceSmoothSlow)
        self.plot1Markers1.setData(x=self.graphDataTime, y=self.graphDataBitcoinPriceMarker1)  # buy
        self.plot1Markers2.setData(x=self.graphDataTime, y=self.graphDataBitcoinPriceMarker2)  # sell
        # self.plot1GraphRiskLine.setData(x=self.graphDataTime, y=self.graphDataBitcoinRiskLine)
        # self.plot2GraphIndicatorMACD.setData(x=self.graphDataTime, y=self.graphDataIndicatorMACD, fillLevel=0, brush=(255, 243, 20, 80))
        # Update Y avis scale in live market mode
        if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
            if (self.totalNbIterations > 1): # Avoid computing min on a full of zeros array which throws an exception
                maxInPlot1 = np.amax(self.graphDataBitcoinPrice) * self.Y_AXIS_TOP_MARGIN_IN_EXTREMUM_PERCENT
                minInPlot1 = (min(i for i in self.graphDataBitcoinPrice if i > 0)) * self.Y_AXIS_BOTTOM_MARGIN_IN_EXTREMUM_PERCENT
                # Set larget Y scaling if chart amplitude is too weak
                if ((maxInPlot1 - minInPlot1) < (self.graphDataBitcoinPrice[-1] * 0.02)):
                    maxInPlot1 = maxInPlot1 * 1.006
                    minInPlot1 = minInPlot1 * 0.994
            else:
                minInPlot1 = self.PLOT1_DEFAULT_MINIMUM
                maxInPlot1 = self.PLOT1_DEFAULT_MAXIMUM

            # Y range update only on change to avoid permanent axis rescaling which affects the user experience when zomming
            if ((self.minInPlot1 != minInPlot1) or (self.maxInPlot1 != maxInPlot1)):
                self.minInPlot1 = minInPlot1
                self.maxInPlot1 = maxInPlot1
                self.plot1.setYRange(minInPlot1, maxInPlot1)

            # Force UI refresh. After a long running time, UI refresh is not automatic sometimes
            QtGui.QApplication.processEvents()
            self.plot1.update()
        else:
            # Simulation mode
            if (self.totalNbIterations > 1): # Avoid computing min on a full of zeros array which throws an exception
                if (self.totalNbGraphUpdates % 4 == 0):
                    maxInPlot1 = np.amax(self.graphDataBitcoinPrice) * self.Y_AXIS_TOP_MARGIN_IN_EXTREMUM_PERCENT
                    minInPlot1 = (min(i for i in self.graphDataBitcoinPrice if i > 0)) * self.Y_AXIS_BOTTOM_MARGIN_IN_EXTREMUM_PERCENT
                    # Set larget Y scaling if chart amplitude is too weak
                    if ((maxInPlot1 - minInPlot1) < (self.graphDataBitcoinPrice[-1] * 0.02)):
                        maxInPlot1 = maxInPlot1 * 1.006
                        minInPlot1 = minInPlot1 * 0.994

                    # Y range update only on change to avoid permanent axis rescaling which affects the user experience when zomming
                    if ((self.minInPlot1 != minInPlot1) or (self.maxInPlot1 != maxInPlot1)):
                        self.minInPlot1 = minInPlot1
                        self.maxInPlot1 = maxInPlot1
                        self.plot1.setYRange(minInPlot1, maxInPlot1)

                    # Every 3 refreshes is sufficient
                    QtGui.QApplication.processEvents()
                    self.plot1.update()

            # Shall be at the end
            self.areNewSamplesRequested = True


    def UIGR_performManualYRangeRefresh(self):
        if (self.totalNbIterations > 1): # Avoid computing min on a full of zeros array which throws an exception
            maxInPlot1 = np.amax(self.graphDataBitcoinPrice) * self.Y_AXIS_TOP_MARGIN_IN_EXTREMUM_PERCENT
            minInPlot1 = (min(i for i in self.graphDataBitcoinPrice if i > 0)) * self.Y_AXIS_BOTTOM_MARGIN_IN_EXTREMUM_PERCENT
            # Set larget Y scaling if chart amplitude is too weak
            if ((maxInPlot1 - minInPlot1) < (self.graphDataBitcoinPrice[-1] * 0.02)):
                maxInPlot1 = maxInPlot1 * 1.006
                minInPlot1 = minInPlot1 * 0.994
        else:
            minInPlot1 = self.PLOT1_DEFAULT_MINIMUM
            maxInPlot1 = self.PLOT1_DEFAULT_MAXIMUM

        # Y range update only on change to avoid permanent axis rescaling which affects the user experience when zomming
        if ((self.minInPlot1 != minInPlot1) or (self.maxInPlot1 != maxInPlot1)):
            self.minInPlot1 = minInPlot1
            self.maxInPlot1 = maxInPlot1
            self.plot1.setYRange(minInPlot1, maxInPlot1)

    def UIGR_updateTransactionHistory(self, transHistory):
        if transHistory != []:
            self.transactionHistory = transHistory
            Hist_length = len(transHistory)
            # updating each row
            # row 1
            self.lblLast1TransTradePair.setText(self.transactionHistory[-1]["symbol"])
            self.lblLast1TransOperation.setText(self.transactionHistory[-1]["side"])
            self.lblLast1TransPrice.setText(self.transactionHistory[-1]["price"])
            self.lblLast1TransAmount.setText(self.transactionHistory[-1]["quantity"])
            self.lblLast1TransTime.setText(self.transactionHistory[-1]["time"])
            if Hist_length < 2:
                return
            # row 2
            self.lblLast2TransTradePair.setText(self.transactionHistory[-2]["symbol"])
            self.lblLast2TransOperation.setText(self.transactionHistory[-2]["side"])
            self.lblLast2TransPrice.setText(self.transactionHistory[-2]["price"])
            self.lblLast2TransAmount.setText(self.transactionHistory[-2]["quantity"])
            self.lblLast2TransTime.setText(self.transactionHistory[-2]["time"])
            if Hist_length < 3:
                return
            # row 3
            self.lblLast3TransTradePair.setText(self.transactionHistory[-3]["symbol"])
            self.lblLast3TransOperation.setText(self.transactionHistory[-3]["side"])
            self.lblLast3TransPrice.setText(self.transactionHistory[-3]["price"])
            self.lblLast3TransAmount.setText(self.transactionHistory[-3]["quantity"])
            self.lblLast3TransTime.setText(self.transactionHistory[-3]["time"])
            if Hist_length < 4:
                return
            # row 4
            self.lblLast4TransTradePair.setText(self.transactionHistory[-4]["symbol"])
            self.lblLast4TransOperation.setText(self.transactionHistory[-4]["side"])
            self.lblLast4TransPrice.setText(self.transactionHistory[-4]["price"])
            self.lblLast4TransAmount.setText(self.transactionHistory[-4]["quantity"])
            self.lblLast4TransTime.setText(self.transactionHistory[-4]["time"])
            if Hist_length < 5:
                return
            # row 5
            self.lblLast5TransTradePair.setText(self.transactionHistory[-5]["symbol"])
            self.lblLast5TransOperation.setText(self.transactionHistory[-5]["side"])
            self.lblLast5TransPrice.setText(self.transactionHistory[-5]["price"])
            self.lblLast5TransAmount.setText(self.transactionHistory[-5]["quantity"])
            self.lblLast5TransTime.setText(self.transactionHistory[-5]["time"])
            if Hist_length < 6:
                return
            # row 6
            self.lblLast6TransTradePair.setText(self.transactionHistory[-6]["symbol"])
            self.lblLast6TransOperation.setText(self.transactionHistory[-6]["side"])
            self.lblLast6TransPrice.setText(self.transactionHistory[-6]["price"])
            self.lblLast6TransAmount.setText(self.transactionHistory[-6]["quantity"])
            self.lblLast6TransTime.setText(self.transactionHistory[-6]["time"])
            if Hist_length < 7:
                return
            # row 7
            self.lblLast7TransTradePair.setText(self.transactionHistory[-7]["symbol"])
            self.lblLast7TransOperation.setText(self.transactionHistory[-7]["side"])
            self.lblLast7TransPrice.setText(self.transactionHistory[-7]["price"])
            self.lblLast7TransAmount.setText(self.transactionHistory[-7]["quantity"])
            self.lblLast7TransTime.setText(self.transactionHistory[-7]["time"])

    def UIGR_updateAccountsBalance(self, EURBalance, CryptoBalance):
        self.strEURBalance = str(EURBalance)

        # Avoid display like 1e-7
        if (CryptoBalance <= theConfig.CONFIG_CRYPTO_PRICE_QUANTUM):
            CryptoBalance = 0.0
        self.strCryptoBalance = str(CryptoBalance)

        # If there's no risk from being called from a background thread, update UI here
        if (self.isContinuousGraphRefreshEnabled == False):
            if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
                strSimulationPrecision = " (Live Trade)"
            else:
                strSimulationPrecision = " (Simulation)"
            # self.lblFiatBalance.setText(self.STR_LABEL_FIAT_BALANCE + self.strEURBalance + ' ' + str(self.theSettings.SETT_GetSettings()["strFiatType"]) + strSimulationPrecision)
            # self.lblCryptoMoneyBalance.setText(self.STR_LABEL_CRYPTO_BALANCE + self.strCryptoBalance + ' ' + str(self.theSettings.SETT_GetSettings()["strCryptoType"]) + strSimulationPrecision)

            self.lblFiatAbbr.setText(str(self.theSettings.SETT_GetSettings()["strFiatType"]) + strSimulationPrecision)
            self.lblFiatBalance.setText(self.STR_LABEL_FIAT_BALANCE + self.strEURBalance)
            self.lblCryptoAbbr.setText(str(self.theSettings.SETT_GetSettings()["strCryptoType"]) + strSimulationPrecision)
            self.lblCryptoMoneyBalance.setText(self.STR_LABEL_CRYPTO_BALANCE + self.strCryptoBalance)
        else:
            self.safeUIRefreshIsRequested = True

    def UIGR_SAFE_updateAccountsBalance(self):
        if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
            strSimulationPrecision = " (Live Trade)"
        else:
            strSimulationPrecision = " (Simulation)"
        # self.lblFiatBalance.setText(self.STR_LABEL_FIAT_BALANCE + self.strEURBalance + ' ' + str(self.theSettings.SETT_GetSettings()["strFiatType"]) + strSimulationPrecision)
        # self.lblCryptoMoneyBalance.setText(self.STR_LABEL_CRYPTO_BALANCE + self.strCryptoBalance + ' ' + str(self.theSettings.SETT_GetSettings()["strCryptoType"]) + strSimulationPrecision)
            self.lblFiatAbbr.setText(str(self.theSettings.SETT_GetSettings()["strFiatType"])+ strSimulationPrecision)
            self.lblFiatBalance.setText(self.STR_LABEL_FIAT_BALANCE + self.strEURBalance)
            self.lblCryptoAbbr.setText(str(self.theSettings.SETT_GetSettings()["strCryptoType"]) + strSimulationPrecision)
            self.lblCryptoMoneyBalance.setText(self.STR_LABEL_CRYPTO_BALANCE + self.strCryptoBalance)

    def UIGR_updatePriceLbl(self, newPrice):

        self.priceLabelStr = str(newPrice)

        # If there's no risk from being called from a background thread, update UI here
        if (self.isContinuousGraphRefreshEnabled == False):
            self.lblLivePrice.setText(self.STR_LABEL_MONEY_MIDDLEMARKET_PRICE + self.priceLabelStr + " " + str(self.theSettings.SETT_GetSettings()["strFiatType"]))
        else:
            pass # No need to set a flag, price lbl update is automatic in background


    def UIGR_SAFE_updatePriceLbl(self):
        self.lblLivePrice.setText(self.STR_LABEL_MONEY_MIDDLEMARKET_PRICE + self.priceLabelStr + " " + str(self.theSettings.SETT_GetSettings()["strFiatType"]))

    def UIGR_updateCurrentState(self, newState, isLiveTrading, blink):
        if (blink == True):
            self.isLblCurrentStateBlinking = True
        else:
            self.isLblCurrentStateBlinking = False
            self.lblCurrentState.setVisible(True)

        self.lblCurrentState.setText(str(newState))
        if (isLiveTrading == True):
            self.lblCurrentState.setStyleSheet(self.STR_QLABEL_CURRENT_STATE_LIVE_TRADING_STYLESHEET)
        else:
            self.lblCurrentState.setStyleSheet(self.STR_QLABEL_STYLESHEET)

    def UIGR_toogleStatus(self):
        self.lblCurrentState.setVisible(False);

    def UIGR_updateTotalProfit(self, realProfit, theoricProfit, percentageProfit, isSimulation):
        self.realProfit = realProfit
        self.theoricProfit = theoricProfit
        self.percentageProfit = percentageProfit
        self.displayProfitAsInSimulation = isSimulation

        # If there's no risk from being called from a background thread, update UI here
        if (self.isContinuousGraphRefreshEnabled == False):
            if (self.displayProfitAsInSimulation == True):
                self.lblTotalGains.setText(self.STR_LABEL_TOTAL_GAINS + str(self.theoricProfit) + " " + str(self.theSettings.SETT_GetSettings()["strFiatType"]) + " (" + str(self.percentageProfit) + "%)")
            else:
                self.lblTotalGains.setText(self.STR_LABEL_TOTAL_GAINS + str(self.realProfit) + " " + str(self.theSettings.SETT_GetSettings()["strFiatType"]) + " (" + str(self.percentageProfit) + "%)")

            if (self.theoricProfit > 0):
                self.lblTotalGains.setStyleSheet(self.STR_QLABEL_PROFIT_GREEN_STYLESHEET)
            elif (self.theoricProfit < 0):
                self.lblTotalGains.setStyleSheet(self.STR_QLABEL_PROFIT_RED_STYLESHEET)
            else:
                self.lblTotalGains.setStyleSheet(self.STR_QLABEL_STYLESHEET)
        else:
            self.safeUIRefreshIsRequested = True

    def UIGR_SAFE_updateTotalProfit(self):
        if (self.displayProfitAsInSimulation == True):
            self.lblTotalGains.setText(self.STR_LABEL_TOTAL_GAINS + str(self.theoricProfit) + " " + str(self.theSettings.SETT_GetSettings()["strFiatType"]) + " (" + str(self.percentageProfit) + "%)")
        else:
            self.lblTotalGains.setText(self.STR_LABEL_TOTAL_GAINS + str(self.realProfit) + " " + str(self.theSettings.SETT_GetSettings()["strFiatType"]) + " (" + str(self.percentageProfit) + "%)")

        if (self.theoricProfit > 0):
            self.lblTotalGains.setStyleSheet(self.STR_QLABEL_PROFIT_GREEN_STYLESHEET)
        elif (self.theoricProfit < 0):
            self.lblTotalGains.setStyleSheet(self.STR_QLABEL_PROFIT_RED_STYLESHEET)
        else:
            self.lblTotalGains.setStyleSheet(self.STR_QLABEL_STYLESHEET)


    def UIGR_updateInfoText(self, newInfoText, isError):
        self.lblInfoInErrorStyle = isError
        self.lblInfoStr = newInfoText

        # If there's no risk from being called from a background thread, update UI here
        if (self.isContinuousGraphRefreshEnabled == False):
            # Actual update
            self.lblInfo.setText(self.lblInfoStr)
            if (self.lblInfoInErrorStyle == True):
                self.lblInfo.setStyleSheet(self.STR_QLABEL_INFO_ERROR_STYLESHEET)
            else:
                self.lblInfo.setStyleSheet(self.STR_QLABEL_INFO_STYLESHEET);

            # Automatic style change if needed
            if ((("Welcome" in self.lblInfoStr) == True)):
                self.lblInfo.setStyleSheet(self.STR_QLABEL_INFO_GREEN_STYLESHEET)
                self.lblInfo.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            elif (("here to unlock" in self.lblInfoStr) == True):
                self.lblInfo.setStyleSheet(self.STR_QLABEL_INFO_ORANGE_STYLESHEET)
                self.lblInfo.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            else:
                # Set default cursor back
                self.lblInfo.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        else:
            self.safeUIRefreshIsRequested = True

    def UIGR_SAFE_updateInfoText(self):
        self.lblInfo.setText(self.lblInfoStr)
        if (self.lblInfoInErrorStyle == True):
            self.lblInfo.setStyleSheet(self.STR_QLABEL_INFO_ERROR_STYLESHEET);
        else:
            self.lblInfo.setStyleSheet(self.STR_QLABEL_INFO_STYLESHEET);
        pass

    def UIGR_updateLoadingDataProgress(self, progressInPercent):
        if (self.buttonStart.text() != "Start"):
            self.buttonStart.setText("Loading\nData...\n%s%%" % progressInPercent)

    def TimerRaisedBlinkWidgets(self):
        if (self.isLblCurrentStateBlinking == True):
            if (self.lblCurrentState.isVisible() == False):
                self.lblCurrentState.setVisible(True)
            else:
                self.lblCurrentState.setVisible(False)

    def UIGR_resetConnectionText(self):
        self.lblConnection.setText("")

    def UIGR_updateConnectionText(self, newText):
        if (self.lblConnection.text() == ""):
            self.lblConnection.setText(newText)

    def UIGR_updateLiveData(self, newData):
        self.strLiveData = (str(newData)[:100])

    def UIGR_updateLiveDataTimer(self):
        self.lblLiveData.setText(self.strLiveData)

    # Will be added to data on the next call to UIGR_updateNextIterationData()
    # Will be displayed on the next call to UIGR_updateGraphs
    # 1 => Buy marker
    # 2 => Sell marker
    # This function needs to be called after UIGR_updateNextIterationData to avoid the markers to be overwritten
    def UIGR_addMarker(self, op, timestamp, price):
        time = round(timestamp/1000/10) * 10
        time_idx = int((time - self.graphDataTime[0]) / 10 - 1)
        markerNumber = 1 if op == 'BUY' else 2
        print("UIGR - Marker added at %s" % price)
        if (markerNumber == 1):
            # Added on the last-but-one sample in order to avoid last sample to be overwritten by UIGR_updateNextIterationData
            self.graphDataBitcoinPriceMarker1[time_idx] = self.graphDataBitcoinPrice[time_idx]
            pass
        elif (markerNumber == 2):
            # Added on the last-but-one sample in order to avoid last sample to be overwritten by UIGR_updateNextIterationData
            self.graphDataBitcoinPriceMarker2[time_idx] = self.graphDataBitcoinPrice[time_idx]
            pass

    def UIGR_getRadioButtonSimulation(self):
        return self.radioButtonSimulation;

    def UIGR_getRadioButtonTrading(self):
        return self.radioButtonTrading;

    def UIGR_SetRadioButtonsEnabled(self, bEnable):
        self.radioButtonSimulation.setEnabled(bEnable)
        self.radioButtonTrading.setEnabled(bEnable)
        if (bEnable == True):
            self.radioButtonSimulation.setStyleSheet(self.STR_QRADIOBUTTON_STYLESHEET)
            self.radioButtonTrading.setStyleSheet(self.STR_QRADIOBUTTON_STYLESHEET)
        else:
            self.radioButtonSimulation.setStyleSheet(self.STR_QRADIOBUTTON_DISABLED_STYLESHEET)
            self.radioButtonTrading.setStyleSheet(self.STR_QRADIOBUTTON_DISABLED_STYLESHEET)

    def UIGR_SetStartButtonEnabled(self, bEnable):
        self.buttonStart.setEnabled(bEnable)

    def UIGR_SetStartButtonAspect(self, aspect):
        if (aspect == "START"):
            self.buttonStart.setText("Start")
            self.buttonStart.setStyleSheet(self.STR_QBUTTON_START_STYLESHEET)
        if (aspect == "START_DISABLED"):
            self.buttonStart.setText("Start")
            self.buttonStart.setStyleSheet(self.STR_QBUTTON_START_DISABLED_STYLESHEET)
        elif (aspect == "STOP"):
            self.buttonStart.setText("Stop")
            self.buttonStart.setStyleSheet(self.STR_QBUTTON_STOP_STYLESHEET)
        elif (aspect == "LOADING"):
            self.buttonStart.setText("Loading\ndata...")
            self.buttonStart.setStyleSheet(self.STR_QBUTTON_LOADING_STYLESHEET)

    def UIGR_SetPauseButtonEnabled(self, bEnable):
        self.buttonPause.setEnabled(bEnable)
        self.buttonPause.setVisible(bEnable)

    def UIGR_SetPauseButtonAspect(self, aspect):
        if (aspect == "PAUSE"):
            self.buttonPause.setText("Pause")
            self.buttonPause.setStyleSheet(self.STR_QBUTTON_PAUSE_STYLESHEET)
        if (aspect == "PAUSE_DISABLED"):
            self.buttonPause.setText("Pause")
            self.buttonPause.setStyleSheet(self.STR_QBUTTON_PAUSE_DISABLED_STYLESHEET)
        elif (aspect == "RESUME"):
            self.buttonPause.setText("Resume")
            self.buttonPause.setStyleSheet(self.STR_QBUTTON_PAUSE_STYLESHEET)

    def UIGR_SetSettingsButtonsEnabled(self, bEnable):
        self.buttonSettings.setEnabled(bEnable)
        if (bEnable == True):
            self.buttonSettings.setStyleSheet(self.STR_QBUTTON_SETTINGS_STYLESHEET)
        else:
            self.buttonSettings.setStyleSheet(self.STR_QBUTTON_SETTINGS_DISABLED_STYLESHEET)

    # def UIGR_SetDonationButtonsEnabled(self, bEnable):
    #     self.buttonDonation.setEnabled(bEnable)
    #     if (bEnable == True):
    #         self.buttonDonation.setStyleSheet(self.STR_QBUTTON_SETTINGS_STYLESHEET)
    #     else:
    #         self.buttonDonation.setStyleSheet(self.STR_QBUTTON_SETTINGS_DISABLED_STYLESHEET)

    def UIGR_SetCurrentAppState(self, appState):
        self.currentAppState = appState

    # Perform UI actions due to a trading pair change
    def UIGR_NotifyThatTradingPairHasChanged(self):
        self.STR_LABEL_MONEY_MIDDLEMARKET_PRICE = self.theSettings.SETT_GetSettings()["strCryptoType"] + str(" MiddleMarket price : ")
        self.lblLivePrice.setText(self.STR_LABEL_MONEY_MIDDLEMARKET_PRICE)

        # Non destructive "search and replace" because of the possible '(Simulation)' annotation
        self.lblFiatBalance.setText(self.lblFiatBalance.text().replace("USD", "---"))
        self.lblFiatBalance.setText(self.lblFiatBalance.text().replace("EUR", "---"))
        self.lblFiatBalance.setText(self.lblFiatBalance.text().replace("---", self.theSettings.SETT_GetSettings()["strFiatType"]))

        self.lblCryptoMoneyBalance.setText(self.lblCryptoMoneyBalance.text().replace("USD", "---"))
        self.lblCryptoMoneyBalance.setText(self.lblCryptoMoneyBalance.text().replace("EUR", "---"))
        self.lblCryptoMoneyBalance.setText(self.lblCryptoMoneyBalance.text().replace("---", self.theSettings.SETT_GetSettings()["strFiatType"]))

        self.lblTotalGains.setText(self.lblTotalGains.text().replace("USD", "---"))
        self.lblTotalGains.setText(self.lblTotalGains.text().replace("EUR", "---"))
        self.lblTotalGains.setText(self.lblTotalGains.text().replace("---", self.theSettings.SETT_GetSettings()["strFiatType"]))

        # self.STR_LABEL_FIAT_BALANCE = str(self.theSettings.SETT_GetSettings()["strFiatType"]) + " Account Balance : "
        # self.STR_LABEL_CRYPTO_BALANCE = str(self.theSettings.SETT_GetSettings()["strCryptoType"]) + " Account Balance : "
        self.STR_LABEL_FIAT_BALANCE = ""
        self.STR_LABEL_CRYPTO_BALANCE = ""

        self.strPlot1Title = str(self.theSettings.SETT_GetSettings()["strTradingPair"]) + ' Coinbase Pro Market Price (' + str(self.theSettings.SETT_GetSettings()["strFiatType"]) + ')'
        self.plot1.setTitle(self.strPlot1Title)

        self.UIGR_ResetAllGraphData(True, -1, 600)

    # def UIGR_SetTransactionManager(self, transactionManager):
    #     self.theUIDonation.UIDO_SetTransactionManager(transactionManager)
        
    # def UIGR_RequestDonationWindowDisplay(self):
    #     self.theUIDonation.UIDO_ShowWindow()

    def UIGR_closeBackgroundOperations(self):
        self.timerUpdateLiveData.stop()
