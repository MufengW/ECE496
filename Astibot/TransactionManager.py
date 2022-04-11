import time
from datetime import datetime

import threading

from GDAXControler import GDAXControler
from UIGraph import UIGraph
import TradingBotConfig as theConfig
import Notifier as theNotifier

class TransactionManager(object):


    def __init__(self, GDAXControler, UIGraph, MarketData, Settings):
        self.theGDAXControler = GDAXControler
        self.theUIGraph = UIGraph
        self.theMarketData = MarketData
        # Application settings data instance
        self.theSettings = Settings

        self.FiatAccountBalance = 0
        self.FIATAccountBalanceSimulated = 0
        self.initialFiatAccountBalance = 0 # Only necessary in Trading mode. In simulation mode, profit is only theoric
        self.initialInvestedFiatAmount = 0
        self.CryptoAccountBalance = 0
        self.cryptoAccountBalanceSimulated = 0
        self.theoricalProfit = 0
        self.realProfit = 0
        self.percentageProfit = 0
        self.currentBuyAmountInCryptoWithoutFee = 0
        self.currentBuyAmountInCryptoWithFee = 0
        self.currentSoldAmountInCryptoViaLimitOrder = 0
        self.averageSellPriceInFiat = 0
        self.platformTakerFeeInPercent = float(self.theSettings.SETT_GetSettings()["platformTakerFee"]) * 0.01
        self.pendingNotificationToSend = ""

        self.buyTimeInTimeStamp = 0
        self.currentBuyInitialPriceInEUR = 0

        self.theUIGraph.UIGR_updateAccountsBalance(round(self.FiatAccountBalance, 6), round(self.CryptoAccountBalance, 6))
        self.theUIGraph.UIGR_updateTotalProfit(self.realProfit, self.theoricalProfit, self.percentageProfit, False)
        self.threadOrderPlacingLock = threading.Lock()
        self.isOrderPlacingActive = False
        self.orderPlacingType = 'NONE'
        self.orderPlacingState = 'NONE'
        self.orderPlacingMinMaxPrice = 0
        self.orderPlacingCurrentPriceInFiat = 0
        self.transactionHistory = []
        self.isRunning = True


    def TRNM_InitiateNewTradingSession(self, startSession):
        self.theoricalProfit = 0
        self.realProfit = 0
        self.percentageProfit = 0
        self.currentBuyAmountInCryptoWithoutFee = 0
        self.currentBuyAmountInCryptoWithFee = 0
        self.currentSoldAmountInCryptoViaLimitOrder = 0
        self.averageSellPriceInFiat = 0
        self.buyTimeInTimeStamp = 0
        self.currentBuyInitialPriceInEUR = 0
        self.pendingNotificationToSend = ""
        self.isOrderPlacingActive = False
        self.orderPlacingType = 'NONE'
        self.orderPlacingState = 'NONE'
        self.orderPlacingMinMaxPrice = 0
        self.orderPlacingCurrentPriceInFiat = 0

        # Refresh platform taker fee
        self.platformTakerFeeInPercent = float(self.theSettings.SETT_GetSettings()["platformTakerFee"]) * 0.01
        print("TRNM - Initiating new trading session. Applied platformTakerFee multiplicator is %s" % self.platformTakerFeeInPercent)

        # In simulation mode, simulate an amount of money on the account
        if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == False):
            self.initialFiatAccountBalance = 0
            self.FIATAccountBalanceSimulated = float(self.theSettings.SETT_GetSettings()["simulatedFiatBalance"])
            self.initialInvestedFiatAmount = float(self.theSettings.SETT_GetSettings()["investPercentage"]) * 0.01 * self.FIATAccountBalanceSimulated
            self.cryptoAccountBalanceSimulated = 0
            self.theUIGraph.UIGR_updateAccountsBalance(self.FIATAccountBalanceSimulated, self.cryptoAccountBalanceSimulated)
            self.theUIGraph.UIGR_updateTotalProfit(self.realProfit, self.theoricalProfit, self.percentageProfit, True)
        else:
            self.initialFiatAccountBalance = self.theGDAXControler.GDAX_GetFiatAccountBalance()
            print("TRNM - Initial fiat balance is %s" % self.initialFiatAccountBalance)
            self.FIATAccountBalanceSimulated = 0
            self.cryptoAccountBalanceSimulated = 0
            self.initialInvestedFiatAmount = float(self.theSettings.SETT_GetSettings()["investPercentage"]) * 0.01 * self.initialFiatAccountBalance
            self.theUIGraph.UIGR_updateTotalProfit(self.realProfit, self.theoricalProfit, self.percentageProfit, False)
            self.theGDAXControler.GDAX_RefreshAccountsDisplayOnly()
            self.theGDAXControler.GDAX_RequestAccountsBalancesUpdate()

        if (startSession == True):
            self.theUIGraph.UIGR_updateInfoText("Waiting for next buy opportunity", False)

    def TRNM_TerminateCurrentTradingSession(self):
        print("TRNM - Terminating current trading session...")

        self.FIATAccountBalanceSimulated = 0
        self.cryptoAccountBalanceSimulated = 0
        self.theUIGraph.UIGR_updateInfoText("", False)
        self.pendingNotificationToSend = ""
        self.isOrderPlacingActive = False
        self.isOrderPlacingActive = True
        self.orderPlacingCurrentPriceInFiat = 0
        self.isOrderPlacingActive = False
        self.orderPlacingState = "NONE"

        if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == False):
            pass
        else:
            # In real trading mode let GDAX controler update the accounts labels. TRNM will manage
            # money / refresh itself when initiating the new trading session
            self.theGDAXControler.GDAX_CancelOngoingLimitOrder()

    def TRNM_getCryptoBalance(self):
        return self.theGDAXControler.GDAX_GetCryptoAccountBalance()

    def TRNM_ForceAccountsUpdate(self):
        self.theGDAXControler.GDAX_RequestAccountsBalancesUpdate()

    def TRNM_getBTCBalance(self):
        return self.theGDAXControler.GDAX_GetBTCAccountBalance()

    def Place_Market_Order(self, buyOrSell):
        if (buyOrSell == "BUY"):
            print("TRNM - Limit %s requested" % (buyOrSell))
            self.theUIGraph.UIGR_updateInfoText("Placing %s order" % (buyOrSell), False)
            self.threadOrderPlacingLock.acquire()
            self.TRNM_BuyNow()
            self.threadOrderPlacingLock.release()
        elif (buyOrSell == "SELL"):
            print("TRNM - Limit %s requested" % (buyOrSell))
            self.theUIGraph.UIGR_updateInfoText("Placing %s order" % (buyOrSell), False)
            self.threadOrderPlacingLock.acquire()
            self.TRNM_SellNow(False)
            self.threadOrderPlacingLock.release()
        else:
            print("TRNM - Limit %s requested, unknown order type" % buyOrSell)

    def computeBuyCapabilityInCrypto(self, includeHeldBalance):
        buyCapabilityInCrypto = 0.0
        accountBalanceHeld = 0.0

        if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
            self.FiatAccountBalance = self.theGDAXControler.GDAX_GetFiatAccountBalance()
            if (includeHeldBalance):
                accountBalanceHeld = self.theGDAXControler.GDAX_GetFiatAccountBalanceHeld()
                self.FiatAccountBalance += accountBalanceHeld
            currentPriceInFiat = self.theGDAXControler.GDAX_GetRealTimePriceInEUR()
            buyCapabilityInCrypto = float(self.FiatAccountBalance) / float(currentPriceInFiat)
            print("TRNM - computeBuyCapabilityInCrypto: capability is %s (current balance is %s + %s (hold))" % (buyCapabilityInCrypto, self.FiatAccountBalance, accountBalanceHeld))
        else:
            buyCapabilityInCrypto = self.FIATAccountBalanceSimulated / self.theMarketData.MRKT_GetLastRefPrice()
        return buyCapabilityInCrypto

    def computeProfitEstimation(self, isSellFeeApplied, soldAmountInCryptoWithFee):
        # Don't include fee to get actual amount of money invested by the user (its cost for user point of view), not the amount of money actually invested in the platform after deducing the fee
        InvestmentInFiat = self.currentBuyInitialPriceInEUR * self.currentBuyAmountInCryptoWithoutFee
        if (isSellFeeApplied):
            SellPriceWithFeeInFiat = (self.averageSellPriceInFiat * soldAmountInCryptoWithFee) * (1-(self.platformTakerFeeInPercent))
        else:
            SellPriceWithFeeInFiat = (self.averageSellPriceInFiat * soldAmountInCryptoWithFee)

        print("TRNM - ComputeProfitEstimation : Buy  price with fee: %s" % InvestmentInFiat)
        print("TRNM - ComputeProfitEstimation : Sell price with fee: %s, fee applied? %s" % (SellPriceWithFeeInFiat, isSellFeeApplied))
        profitEstimation = (SellPriceWithFeeInFiat - InvestmentInFiat)
        return [profitEstimation, SellPriceWithFeeInFiat]


    def TRNM_BuyNow(self):
        if ((self.theGDAXControler.GDAX_IsConnectedAndOperational() == "True") or (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == False)):
            if (self.currentBuyAmountInCryptoWithoutFee == 0): # Security : no telesopic buys
                bOrderIsSuccessful = False

                # Refresh account balances =======================================================================
                self.FiatAccountBalance = self.theGDAXControler.GDAX_GetFiatAccountBalance()
                self.CryptoAccountBalance = self.theGDAXControler.GDAX_GetCryptoAccountBalance()

                # Compute capability  ============================================================================
                BuyCapabilityInCrypto = self.computeBuyCapabilityInCrypto(False)
                print("TRNM - Buy Now, capability is: %s Crypto (fiat balance is %s, crypto balance is %s)" % (BuyCapabilityInCrypto, self.FiatAccountBalance, self.CryptoAccountBalance))

                # Compute and fill Buy data ======================================================================
                if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
                    self.currentBuyInitialPriceInEUR = self.theGDAXControler.GDAX_GetRealTimePriceInEUR()
                else:
                    self.currentBuyInitialPriceInEUR = self.theMarketData.MRKT_GetLastRefPrice()
                ratioOfCryptoCapabilityToBuy = float(self.theSettings.SETT_GetSettings()["investPercentage"]) * 0.01
                self.currentBuyAmountInCryptoWithoutFee = BuyCapabilityInCrypto * ratioOfCryptoCapabilityToBuy
                self.currentBuyAmountInCryptoWithFee = BuyCapabilityInCrypto * ratioOfCryptoCapabilityToBuy * (1-(self.platformTakerFeeInPercent))

                # Perform transaction  ===========================================================================
                print("TRNM - Buy Now, amount is: %s Crypto" % self.currentBuyAmountInCryptoWithoutFee)
                bAmountIsAboveMinimumRequested = self.theGDAXControler.GDAX_IsAmountToBuyAboveMinimum(self.currentBuyAmountInCryptoWithoutFee)
                print("TRNM - Amount to buy is above minimum possible ? %s" % bAmountIsAboveMinimumRequested)
                if (bAmountIsAboveMinimumRequested == True):
                    if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
                        # Real market: Send the Buy order
                        bOrderIsSuccessful = self.theGDAXControler.GDAX_SendBuyOrder(self.currentBuyAmountInCryptoWithoutFee)


                # Update display  ============================================================================
                self.buyTimeInTimeStamp = time.time()
                print("TRNM - === BUY %s Crypto at %s Fiat" % (self.currentBuyAmountInCryptoWithoutFee, self.currentBuyInitialPriceInEUR))
                buyTimeStr = datetime.fromtimestamp(int(self.buyTimeInTimeStamp)).strftime('%H:%M')
                if (bOrderIsSuccessful == True):
                    self.performBuyDisplayActions(False)
                else:
                    # Buy transaction failed, cancel
                    self.currentBuyAmountInCryptoWithoutFee = 0
                    self.currentBuyAmountInCryptoWithFee = 0
                    self.currentSoldAmountInCryptoViaLimitOrder = 0
                    self.averageSellPriceInFiat = 0
                    self.currentBuyInitialPriceInEUR = 0
                    if (bAmountIsAboveMinimumRequested == False):
                        self.theUIGraph.UIGR_updateInfoText("%s: Buy order error: amount is too low, increase your %s balance" % (buyTimeStr, self.theSettings.SETT_GetSettings()["strFiatType"]), True)
                    else:
                        self.theUIGraph.UIGR_updateInfoText("%s: Buy order error" % buyTimeStr, True)

                return bOrderIsSuccessful
            else:
                print("TRNM - Trying to buy but there's already a pending buy. Aborted.")
                return False
        else:
            print("TRNM - Trying to buy but GDAX Controler not operational. Aborted.")
            return False


    def TRNM_SellNow(self, isStopLossSell):
        if ((self.theGDAXControler.GDAX_IsConnectedAndOperational() == "True") or (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == False)):
            if (True):
                bOrderIsSuccessful = False

                # Refresh account balances =================================================================================
                self.FiatAccountBalance = self.theGDAXControler.GDAX_GetFiatAccountBalance()
                self.CryptoAccountBalance = self.theGDAXControler.GDAX_GetCryptoAccountBalance()

                print("TRNM - Sell Now (fiat balance is %s, crypto balance is %s)" % (self.FiatAccountBalance, self.CryptoAccountBalance))

                # Send the Sell order ======================================================================================
                if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
                    # Subtract quantum so that it compensate up roundings when retrieving balance that could be greater than actual crypto balance and cause an insufficient funds sell error
                    ratioOfCryptoCapabilityToBuy = float(self.theSettings.SETT_GetSettings()["investPercentage"]) * 0.01
                    bOrderIsSuccessful = self.theGDAXControler.GDAX_SendSellOrder((self.CryptoAccountBalance - theConfig.CONFIG_CRYPTO_PRICE_QUANTUM) * ratioOfCryptoCapabilityToBuy)
                    self.averageSellPriceInFiat = self.theGDAXControler.GDAX_GetRealTimePriceInEUR()
                else:
                    self.averageSellPriceInFiat = self.theMarketData.MRKT_GetLastRefPrice()

                # Compute profit estimation ================================================================================
                [profitEstimationInFiat, sellPriceWithFeeInFiat] = self.computeProfitEstimation(True, self.currentBuyAmountInCryptoWithFee)

                # If in simulation, simulate the sell amount of money going back to the FIAT account =======================
                if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == False):
                    #                                    FIAT balance already present      sell value (with GDAX fee) -> money that goes back into fiat
                    self.FIATAccountBalanceSimulated = self.FIATAccountBalanceSimulated + sellPriceWithFeeInFiat
                    self.cryptoAccountBalanceSimulated = 0
                    self.theUIGraph.UIGR_updateAccountsBalance(round(self.FIATAccountBalanceSimulated, 5), round(self.cryptoAccountBalanceSimulated, 5))
                    bOrderIsSuccessful = True

                # Update display
                sellTimeInTimestamp = time.time()
                sellTimeStr = datetime.fromtimestamp(int(sellTimeInTimestamp)).strftime('%Hh%M')

                if (bOrderIsSuccessful == True):
                    self.theoricalProfit = self.theoricalProfit + profitEstimationInFiat

                    if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
                        currentMidMarketPrice = self.theGDAXControler.GDAX_GetRealTimePriceInEUR()
                    else:
                        currentMidMarketPrice = self.theMarketData.MRKT_GetLastRefPrice()

                    print("=== SELL %s at %s USD. Profit made : %s" % (self.currentBuyAmountInCryptoWithFee, currentMidMarketPrice, profitEstimationInFiat))
                    self.performSellDisplayActions(False, isStopLossSell, currentMidMarketPrice, profitEstimationInFiat)
                    self.currentBuyAmountInCryptoWithoutFee = 0
                    self.currentBuyAmountInCryptoWithFee = 0
                    self.currentSoldAmountInCryptoViaLimitOrder = 0
                    self.averageSellPriceInFiat = 0
                    self.currentBuyInitialPriceInEUR = 0
                    self.buyTimeInTimeStamp = 0
                    self.TRNM_RefreshAccountBalancesAndProfit()
                else:
                    self.theUIGraph.UIGR_updateInfoText("%s: Sell order error" % sellTimeStr, True)

                return bOrderIsSuccessful
            else:
                print("TRNM - Trying to sell but no more BTC on the account. Aborted")
                return False
        else:
            print("TRNM - Trying to buy but GDAX Controler not operational. Aborted.")
            return False

    def TRNM_ResetBuyData(self):
        self.theUIGraph.UIGR_updateInfoText("Last Buy has probably been sold manually", False)
        self.currentBuyAmountInCryptoWithoutFee = 0
        self.currentBuyAmountInCryptoWithFee = 0
        self.currentBuyInitialPriceInEUR = 0
        self.currentSoldAmountInCryptoViaLimitOrder = 0
        self.averageSellPriceInFiat = 0

    def TRNM_GetCurrentBuyInitialPrice(self):

        self.threadOrderPlacingLock.acquire()

        currentBuyInitialPriceInEUR = self.currentBuyInitialPriceInEUR

        self.threadOrderPlacingLock.release()

        return self.currentBuyInitialPriceInEUR

    def TRNM_RefreshAccountBalancesAndProfit(self):
        print("TRNM - Refresh Account balances and profit")

        # Real calculation is only applicable on real market
        if (theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET == True):
            # Sleep before fetching account balance (let time to GDAXControler to retrieve the new balances)
            time.sleep(0.5)
            self.FiatAccountBalance = self.theGDAXControler.GDAX_GetFiatAccountBalance()
            # Update real profit only if nothing is spent in BTC
            if (self.currentBuyAmountInCryptoWithoutFee < theConfig.CONFIG_CRYPTO_PRICE_QUANTUM):
                print("TRNM - Nothing spent in Crypto, profit update  to %s - initial was %s" % (self.FiatAccountBalance, self.initialFiatAccountBalance))
                self.realProfit = self.FiatAccountBalance - self.initialFiatAccountBalance
                self.percentageProfit = ((self.realProfit + self.initialInvestedFiatAmount) / (self.initialInvestedFiatAmount) - 1) * 100
                if (self.pendingNotificationToSend != ""):
                    theNotifier.SendWhatsappMessage(self.pendingNotificationToSend + "\n*Total profit: %s %%*" % round(self.percentageProfit, 1) )
            else:
                print("TRNM - RefreshAccountBalancesAndProfit : currentBuyAmountInCryptoWithoutFee greater than quantum: don't update profit. currentBuyAmountInCryptoWithoutFee is %s" % self.currentBuyAmountInCryptoWithoutFee)

            self.CryptoAccountBalance = self.theGDAXControler.GDAX_GetCryptoAccountBalance()
            self.theUIGraph.UIGR_updateTotalProfit(round(self.realProfit, 7), round(self.theoricalProfit, 7), round(self.percentageProfit, 1), False)
        else:
            self.percentageProfit = ((self.theoricalProfit + self.initialInvestedFiatAmount) / (self.initialInvestedFiatAmount) - 1) * 100
            self.theUIGraph.UIGR_updateTotalProfit(0, round(self.theoricalProfit, 7), round(self.percentageProfit, 1), True)
            if (self.pendingNotificationToSend != ""):
                theNotifier.SendWhatsappMessage(self.pendingNotificationToSend + "\n*Total profit: %s %%*" % round(self.percentageProfit, 1) )

        self.pendingNotificationToSend = ""

    # /!\ TODO Check if UIGR calls are thread safe
    def performBuyDisplayActions(self, isLimitOrder):

        if (isLimitOrder):
            if (self.isOrderPlacingActive == False): # Order is totally filled
                sellTriggerInPercent = self.theSettings.SETT_GetSettings()["sellTrigger"]
                if (sellTriggerInPercent > 0.0):
                    sellThreshold = self.currentBuyInitialPriceInEUR * ((sellTriggerInPercent/100)+1)
                else:
                    sellThreshold = self.currentBuyInitialPriceInEUR * (theConfig.CONFIG_MIN_PRICE_ELEVATION_RATIO_TO_SELL + 2*self.platformTakerFeeInPercent) # Not the official one : for display only. Trader class manages this actual feature.
                self.theUIGraph.UIGR_updateInfoText("%s %s Bought @ %s %s via limit order - Waiting for a sell opportunity above %s %s" % (round(self.currentBuyAmountInCryptoWithoutFee, 5), self.theSettings.SETT_GetSettings()["strCryptoType"], round(self.currentBuyInitialPriceInEUR, 5), self.theSettings.SETT_GetSettings()["strFiatType"], round(sellThreshold, 5), self.theSettings.SETT_GetSettings()["strFiatType"]), False)
                theNotifier.SendWhatsappMessage("*BUY filled* %s %s @ %s %s via limit order - Waiting for a sell opportunity above %s %s" % (round(self.currentBuyAmountInCryptoWithoutFee, 5), self.theSettings.SETT_GetSettings()["strCryptoType"], round(self.currentBuyInitialPriceInEUR, 5), self.theSettings.SETT_GetSettings()["strFiatType"], round(sellThreshold, 5), self.theSettings.SETT_GetSettings()["strFiatType"]))

                # Order is totally filled, add marker
                # self.theUIGraph.UIGR_addMarker(1)
            else:
                self.theUIGraph.UIGR_updateInfoText("%s %s Partially bought @ %s %s. Still ongoing, waiting for next matches" % (round(self.currentBuyAmountInCryptoWithoutFee, 5), self.theSettings.SETT_GetSettings()["strCryptoType"], round(self.currentBuyInitialPriceInEUR, 5), self.theSettings.SETT_GetSettings()["strFiatType"]), False)
                theNotifier.SendWhatsappMessage("*BUY match* %s %s @ %s %s. Still ongoing, waiting for next matches" % (round(self.currentBuyAmountInCryptoWithoutFee, 5), self.theSettings.SETT_GetSettings()["strCryptoType"], round(self.currentBuyInitialPriceInEUR, 5), self.theSettings.SETT_GetSettings()["strFiatType"]))
        else:
            buyTimeStr = datetime.fromtimestamp(int(self.buyTimeInTimeStamp)).strftime('%H:%M')
            sellThreshold = self.currentBuyInitialPriceInEUR * (theConfig.CONFIG_MIN_PRICE_ELEVATION_RATIO_TO_SELL + 2*self.platformTakerFeeInPercent) # Not the official one : for display only. Trader class manages this actual feature.
            self.theUIGraph.UIGR_updateInfoText("%s - %s %s Bought @ %s %s - Waiting for a sell opportunity above %s %s" % (buyTimeStr, round(self.currentBuyAmountInCryptoWithoutFee, 5), self.theSettings.SETT_GetSettings()["strCryptoType"], round(self.currentBuyInitialPriceInEUR, 5), self.theSettings.SETT_GetSettings()["strFiatType"], round(sellThreshold, 5), self.theSettings.SETT_GetSettings()["strCryptoType"]), False)
            self.theGDAXControler.refreshAccounts()
            theNotifier.SendWhatsappMessage("*BUY* %s %s @ %s %s - Waiting for a sell opportunity above %s %s" % (round(self.currentBuyAmountInCryptoWithoutFee, 5), self.theSettings.SETT_GetSettings()["strCryptoType"], round(self.currentBuyInitialPriceInEUR, 5), self.theSettings.SETT_GetSettings()["strFiatType"], round(sellThreshold, 5), self.theSettings.SETT_GetSettings()["strFiatType"]))
            # self.theUIGraph.UIGR_addMarker(1)

    def performSellDisplayActions(self, isLimitOrder, isStopLossSell, sellPriceInFiat, profitEstimationInFiat):
        sellTimeInTimestamp = time.time()
        sellTimeStr = datetime.fromtimestamp(int(sellTimeInTimestamp)).strftime('%Hh%M')

        if (isLimitOrder):
            if (self.isOrderPlacingActive == False): # Order is totally filled
                self.theUIGraph.UIGR_updateInfoText("SELL filled at %s, profit was about %s USD. Waiting for next buy opportunity" % (sellTimeStr, round(profitEstimationInFiat, 5)), False)
                self.pendingNotificationToSend = ("*SELL filled* at %s %s, profit was about *%s USD*. " % (round(sellPriceInFiat, 5), self.theSettings.SETT_GetSettings()["strFiatType"], round(profitEstimationInFiat, 5)))
                # Order is totally filled, add marker
                # self.theUIGraph.UIGR_addMarker(2)
            else:
                self.theUIGraph.UIGR_updateInfoText("Partial sell at %s, profit was about %s USD. Still ongoing, waiting for next matches" % (sellTimeStr, round(profitEstimationInFiat, 5)), False)
                self.pendingNotificationToSend = ("*SELL match* at %s %s, profit was about *%s USD*. " % (round(sellPriceInFiat, 5), self.theSettings.SETT_GetSettings()["strFiatType"], round(profitEstimationInFiat, 5)))
        else:
            if (isStopLossSell == False):
                self.theUIGraph.UIGR_updateInfoText("Last sell at %s, profit was about %s USD. Waiting for next buy opportunity" % (sellTimeStr, round(profitEstimationInFiat, 5)), False)
                self.pendingNotificationToSend = ("*SELL* at %s %s, profit was about *%s USD*. " % (round(sellPriceInFiat, 5), self.theSettings.SETT_GetSettings()["strFiatType"], round(profitEstimationInFiat, 5)))
            else:
                self.theUIGraph.UIGR_updateInfoText("StopLoss-sell at %s, loss was about %s USD. Waiting for next buy opportunity" % (sellTimeStr, round(profitEstimationInFiat, 5)), True)
                self.pendingNotificationToSend = ("*STOPLOSS-SELL* at %s %s, loss was about *%s USD*. " % (round(sellPriceInFiat, 5), self.theSettings.SETT_GetSettings()["strFiatType"], round(profitEstimationInFiat, 5)))
            # Add marker
            # self.theUIGraph.UIGR_addMarker(2)