import TradingBotConfig as theConfig
import Notifier as theNotifier
import time

class Trader(object):

    def __init__(self, transactionManager, marketData, UIGraph, Settings):
        self.theTransactionManager = transactionManager
        self.theMarketData = marketData
        self.theUIGraph = UIGraph
        # Application settings data instance
        self.theSettings = Settings

        self.TRAD_ResetTradingParameters()

    def TRAD_ResetTradingParameters(self):
        self.currentState = 'IDLE'
        self.nextState = 'IDLE'

        self.currentPriceValue = 0
        self.previousMACDValue = 0
        self.currentMACDValue = 0
        self.currentBuyPriceInFiat = 0
        #self.MACDConfirmationCounter = 0
        #self.MACDStrength = 0
        self.bought = False
        self.autoSellSamplesCounter = 0
        self.sellTriggerInPercent = self.theSettings.SETT_GetSettings()["sellTrigger"]
        self.ongoingBuyOrderWasFree = False

    def TRAD_InitiateNewTradingSession(self, startSession):
        self.TRAD_ResetTradingParameters()
        self.theTransactionManager.TRNM_InitiateNewTradingSession(startSession)
        if (startSession == True):
            theNotifier.SendWhatsappMessage("*Astibot: New trading session* started on the %s trading pair!" % self.theSettings.SETT_GetSettings()["strTradingPair"])

    def TRAD_TerminateTradingSession(self):
        self.theTransactionManager.TRNM_TerminateCurrentTradingSession()

    def TRAD_ProcessDecision(self):
        state = int(time.time()) % 2
        if state == 0:
            self.theTransactionManager.Place_Market_Order("BUY")
        elif state == 1:
            self.theTransactionManager.Place_Market_Order("SELL")
        # else:
        #     self.theTransactionManager.Place_Market_Order("SELL")