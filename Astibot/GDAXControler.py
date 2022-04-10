import logging
from binance.spot import Spot as Client
from binance.websocket.spot.websocket_client import SpotWebsocketClient as WBClient
from binance.error import ClientError, ServerError

import time
import threading
from json import dumps, loads
import TradingBotConfig as theConfig
from datetime import datetime
import pytz
from tzlocal import get_localzone
from requests.exceptions import ConnectionError
from GDAXCurrencies import GDAXCurrencies
import math  # truncate
import numpy as np

# This module is actually a Coinbase Pro handler
# Murphy TODO : update all GDAX references to CbPro
class GDAXControler():
    '''
    classdocs
    '''
    GDAX_MAX_HISTORIC_PRICES_ELEMENTS = 300
    GDAX_HISTORIC_DATA_MIN_GRANULARITY_IN_SEC = 60
    GDAX_HISTORIC_DATA_SUBSCHEDULING_FACTOR = GDAX_HISTORIC_DATA_MIN_GRANULARITY_IN_SEC / (
                theConfig.CONFIG_TIME_BETWEEN_RETRIEVED_SAMPLES_IN_MS / 1000)

    def __init__(self, UIGraph, Settings):

        super(GDAXControler, self).__init__()

        self.products = None
        self.clientAuth = None
        self.webSocketClient = None
        self._sequence = None
        self.api_key = None
        self.api_secret = None
        self.base_url = None
        self.theUIGraph = UIGraph
        # Application settings data instance
        self.theSettings = Settings

        self.webSocketIsOpened = False
        self.isRunning = True
        self.requestAccountsBalanceUpdate = True
        self.backgroundOperationsCounter = 0

        self.account = None
        self.tickBestBidPrice = 0
        self.tickBestAskPrice = 0
        self.liveBestBidPrice = 0
        self.liveBestAskPrice = 0
        self.midMarketPrice = 0
        self.currentOrderId = 0
        self.currentOrderState = "NONE"  # SUBMITTED / OPENED / FILLED / NONE
        self.currentOrderInitialSizeInCrypto = 0
        self.currentOrderFilledSizeInCrypto = 0
        self.currentOrderAverageFilledPriceInFiat = 0

        self.productStr = self.theSettings.SETT_GetSettings()["strTradingPair"]
        self.productFiatStr = self.theSettings.SETT_GetSettings()["strFiatType"]
        self.productCryptoStr = self.theSettings.SETT_GetSettings()["strCryptoType"]
        self.accountExist = False
        self.CryptoAccount = {}
        self.FiatAccount = {}

        self.transactionHistory = None
        self.HistoricData = []
        self.HistoricDataReadIndex = 0
        self.HistoricDataSubSchedulingIndex = 0

        self.IsConnectedAndOperational = "False"

        self.clientPublic = Client(self.base_url)
        # Start background thread
        threadRefreshPrice = threading.Timer(1, self.updateRealTimePriceInBackground)
        threadRefreshPrice.start()

        self.matchOrderProcessedSequenceId = None

        # WebSocket thread
        # Websocket thread is launched by parent classes
        self.webSocketLock = threading.Lock()

        print("GDAX - GDAX Controller Initialization");

    def GDAX_IsConnectedAndOperational(self):
        return self.IsConnectedAndOperational

    # Function asynchrone
    def GDAX_InitializeGDAXConnection(self):
        self.theUIGraph.UIGR_updateInfoText("Trying to connect...", False)
        self.IsConnectedAndOperational = "Requested"
        print("GDAX - Connection requested")

        if self.webSocketIsOpened:
            print("GDAX - Closing Websocket...")
            self.close()
            print("GDAX - Resetting Order book...")
            self.reset_book()
            # Orderbook class does not reset sequence number when changing product:
            # set it to -1 will force orderbook to refresh
            # the sequence number and retrieve the last full order book
            self._sequence = -1

            self.liveBestBidPrice = 0
            self.liveBestAskPrice = 0

    def startWebSocketFeed(self):
        self.webSocketClient = WBClient(stream_url="wss://testnet.binance.vision")
        self.webSocketClient.start()
        response = self.clientAuth.new_listen_key()
        self.webSocketClient.user_data(
            listen_key=response["listenKey"],
            id=1,
            callback=self.message_handler,
        )

    def PerformConnectionInitializationAttempt(self):
        print("GDAX - Performing connection initialization attempt...")

        self.accountExist = False

        # Real Market keys =========================================
        self.api_key = self.theSettings.SETT_GetSettings()["strAPIKey"]
        self.api_secret = self.theSettings.SETT_GetSettings()["strSecretKey"]
        self.base_url = self.theSettings.SETT_GetSettings()["baseURL"]

        try:
            self.clientAuth = Client(self.api_key, self.api_secret, base_url=self.base_url)
        except ClientError as e:
            print("GDAX - Client connection error")
            print("GDAX - Exception : " + str(e))
        except ServerError as e:
            print("GDAX - Server connection error")
            print("GDAX - Exception : " + str(e))

        # Refresh account in order to see if auth was successful
        try:
            self.account = self.clientAuth.account()
            time.sleep(0.05)
            print("GDAX - Init, Accounts retrieving: %s" % self.account)
            self.startWebSocketFeed()
            self.accountExist = True
            self.refreshAccounts()
            # MURPHY TODO: check retrieving account for real accounts
        except ClientError as e:
            print("GDAX - Client connection error")
            print("GDAX - Exception : " + str(e))
            self.theUIGraph.UIGR_updateInfoText(
                "Connection to Coinbase Pro server failed. GDAX - Exception : " + str(e), True)

        # If both accounts corresponding to the trading pair exist, init is successful
        if self.accountExist:
            print("GDAX - Initialization of GDAX connection successful")
            self.IsConnectedAndOperational = "True"
            self.theUIGraph.UIGR_updateInfoText("Authentication successful", False)
            self.refreshTransactionHistory()
            self.theUIGraph.UIGR_updateTransactionHistory(self.GDAX_GetTransactionHistory())
        else:
            print("GDAX - Initialization of GDAX connection failed")
            self.IsConnectedAndOperational = "False"
            # Display error message
            self.theUIGraph.UIGR_updateInfoText(
                "Connection to Coinbase Pro server failed. Check your internet connection.", True)
    #     DEBUG !!! Test order placing
        params = {
            "symbol": 'BTCUSDT',
            "side": "SELL",
            "type": "MARKET",
            # "timeInForce": "GTC",
            "quantity": 0.01,
            # "price": 0,
        }
        for i in range(3):
            rand_num = int(time.time()) % 2
            if rand_num:
                params["side"] = "SELL"
            else:
                params["side"] = "BUY"
            self.clientAuth.new_order(**params)
            print(self.transactionHistory)
            time.sleep(0.1)

    def GDAX_NotifyThatTradingPairHasChanged(self):
        self.productStr = self.theSettings.SETT_GetSettings()["strTradingPair"]
        self.productFiatStr = self.theSettings.SETT_GetSettings()["strFiatType"]
        self.productCryptoStr = self.theSettings.SETT_GetSettings()["strCryptoType"]
        self.HistoricData = []
        self.HistoricDataReadIndex = 0

    def GDAX_GetTransactionHistory(self):
        print("GDAX - GetTransactionHistory")
        if self.accountExist:
            try:
                rawHistory = self.transactionHistory
                processed_history = []
                local_tz = get_localzone()
                i = 0
                for line in rawHistory:
                    if i > 6:
                        break
                    time = line['time']
                    ISO_time = datetime.fromtimestamp(time/1000, local_tz).isoformat()
                    time_short = datetime.fromtimestamp(time/1000, local_tz).strftime("%b %d, %H:%M")
                    if float(line['price']) == 0:
                        response = self.clientAuth.agg_trades(symbol=line['symbol'], limit=1, startTime=line['time']-100, endTime=line['time']+100)
                        line['price'] = response[0]['p']
                    hist = {'symbol': line['symbol'], 'side': line['side'], 'price': str(float(line['price'])), 'quantity' : str(float(line['executedQty'])), 'time': time_short}
                    processed_history.append(hist)
                    self.theUIGraph.UIGR_addMarker(hist['side'], line['time'], line['price'])
                    i += 1
                return processed_history
            except BaseException as e:
                print("error", e)
                print("GDAX - Error retrieving transaction history")
                return 0
        else:
            print("GDAX - Does not exist")
            return []

    # Returns the Available fiat balance (ie. money that can be used and that is not held for any pending order)
    def GDAX_GetFiatAccountBalance(self):
        print("GDAX - GetFiatAccountBalance")
        if self.accountExist:
            try:
                # print(self.FiatAccount)
                balanceToReturn = (round(float(self.FiatAccount['free']), 8))
                return balanceToReturn
            except BaseException as e:
                print("error", e)
                print("GDAX - Error retrieving fiat account balance. Inconsistent data in fiat account object.")
                return 0
        else:
            print("GDAX - Does not exist")
            return 0

    def GDAX_GetFiatAccountBalanceHeld(self):
        print("GDAX - GetFiatAccountBalance")
        if self.accountExist:
            print("GDAX - account exists")
            try:
                balanceToReturn = round(float(self.FiatAccount['locked']), 8)
                return balanceToReturn
            except BaseException as e:
                print("GDAX - Error retrieving fiat hold account balance. Inconsistent data in fiat account object.")
                return 0
        else:
            print("GDAX - Does not exist")
            return 0

    # Returns the Available crypto balance (ie. money that can be used and that is not held for any pending order)
    def GDAX_GetCryptoAccountBalance(self):
        if self.accountExist:
            try:
                balanceToReturn = round(float(self.CryptoAccount['free']), 8)
                return balanceToReturn
            except BaseException as e:
                print("GDAX - Error retrieving crypto account balance. Inconsistent data in crypto account object.")
                return 0
        else:
            print("GDAX - Error retrieving crypto account balance. Crypto account does not exist")
            return 0

    def GDAX_GetCryptoAccountBalanceHeld(self):
        if self.accountExist:
            try:
                balanceToReturn = round(float(self.CryptoAccount['locked']), 8)
                print("GDAX - Returned held balance %s for %s" % (balanceToReturn, self.productCryptoStr))
                return balanceToReturn
            except BaseException as e:
                print("GDAX - Error retrieving crypto hold account balance. Inconsistent data in crypto account object.")
                return 0
        else:
            print("GDAX - Error retrieving crypto account balance. Crypto account does not exist")
            return 0

    # Returns the Available BTC balance (ie. money that can be used and that is not held for any pending order)
    # Useful for payment system
    def GDAX_GetBTCAccountBalance(self):
        try:
            for currentAccount in self.account['balances']:
                if currentAccount['asset'] == 'BTC':
                    balanceToReturn = round(float(currentAccount['free']), 7)
                    return balanceToReturn
            return 0
        except BaseException as e:
            print("GDAX - Error retrieving crypto account balance. Inconsistent data in crypto account object.")
            return 0

    def refreshAccounts(self):
        try:
            # self.account is a list of dictionary of assets and balance
            self.account = self.clientAuth.account()
            # Refresh individual accounts

            for currentAccount in self.account['balances']:
                if currentAccount['asset'] == self.productCryptoStr:
                    self.CryptoAccount = currentAccount
                if currentAccount['asset'] == self.productFiatStr:
                    self.FiatAccount = currentAccount

            if theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET:
                self.theUIGraph.UIGR_updateAccountsBalance(self.GDAX_GetFiatAccountBalance(),
                                                           self.GDAX_GetCryptoAccountBalance())
            else:
                pass  # In simulated market, accounts are refreshed by the Simulation manager
        except BaseException as e:
            print(e)
            print("GDAX - Error in refreshAccounts")

    def refreshTransactionHistory(self):
        try:
             self.transactionHistory = self.clientAuth.get_orders(self.productStr)
        except BaseException as e:
            print(e)
            print("GDAX - Error in refreshTransactionHistory")

    def GDAX_RefreshAccountsDisplayOnly(self):
        if theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET:
            self.theUIGraph.UIGR_updateAccountsBalance(self.GDAX_GetFiatAccountBalance(),
                                                       self.GDAX_GetCryptoAccountBalance())
        else:
            pass  # TRNM takes care of the price update

    # WebSocket callback - On connection opening
    def on_open(self):
        print("GDAX - WebSocket connection opened (callback) on %s" % self.productStr)
        self.products = [self.productStr]
        self.webSocketIsOpened = True
        self.count = 0
        self.matchOrderProcessedSequenceId = 0

    def on_message(self, message):
        super(GDAXControler, self).on_message(message)

        self.webSocketLock.acquire()

        # Listen for user orders
        if 'orderId' in message:
            if message['order_id'] == self.currentOrderId:
                print("GDAX - Current order msg: %s" % message)
                order_type = message['type']
                if order_type == 'open':
                    self.currentOrderState = "OPENED"
                    print("GDAX - on_message: current order state updated to OPENED")
                elif order_type == 'done':
                    if message['reason'] == 'canceled':
                        self.currentOrderId = 0
                        self.currentOrderState = "NONE"
                        self.currentOrderInitialSizeInCrypto = 0
                        self.currentOrderFilledSizeInCrypto = 0
                        self.currentOrderAverageFilledPriceInFiat = 0
                        print("GDAX - on_message: current order canceled")
                    elif float(message['remaining_size']) < theConfig.CONFIG_CRYPTO_PRICE_QUANTUM:
                        self.currentOrderState = "FILLED"
                        print("GDAX - on_message: current order totally filled (to check). Refresh accounts now")
                        self.refreshAccounts()

        # Match messages do not have an "order_id" field but a maker/taker_order_id field
        if 'maker_order_id' in message:
            if message['maker_order_id'] == self.currentOrderId:
                print("GDAX - Current order msg: %s" % message)
                if (message['type'] == 'match') and ('size' in message):
                    # To preserve buy price calculation integrity,
                    # matched order must be processed once (but it appears both in user and full channels)
                    # If this matched message is not processed yet
                    if self.matchOrderProcessedSequenceId != message['sequence']:
                        print("GDAX - on_message: current order has been matched")
                        newFillAverageInFiat = (self.currentOrderAverageFilledPriceInFiat * self.currentOrderFilledSizeInCrypto
                                                + float(message['size']) * float(message['price'])) / \
                                               (self.currentOrderFilledSizeInCrypto + float(message['size']))
                        self.currentOrderFilledSizeInCrypto += float(message['size'])
                        print("GDAX - on_message: average order fill price updated from %s to %s"
                              % (self.currentOrderAverageFilledPriceInFiat, newFillAverageInFiat))
                        print("GDAX - on_message: current order total fill quantity updated to %s"
                              % self.currentOrderFilledSizeInCrypto)
                        self.currentOrderAverageFilledPriceInFiat = newFillAverageInFiat
                        self.matchOrderProcessedSequenceId = message['sequence']
                        self.currentOrderState = "MATCHED"

        # Order book has been updated, retrieve best bid and ask
        self.liveBestBidPrice = self.get_bid()
        # print("Bid %s" % self.liveBestBidPrice)
        self.liveBestAskPrice = self.get_ask()
        # print("Ask %s" % self.liveBestAskPrice)

        self.webSocketLock.release()
    def message_handler(self, message):
        # super(GDAXControler, self).message_handler(message)

        self.webSocketLock.acquire()
        # TODO: Use on_message as an example to finish this function
        # Listen for user orders
        # print("GDAX - Current order msg: %s" % message)

        # TODO: should refresh undeer some cases
        # self.refreshAccounts()
        self.refreshTransactionHistory()
        self.theUIGraph.UIGR_updateTransactionHistory(self.GDAX_GetTransactionHistory())
        self.webSocketLock.release()

    def on_close(self):
        print("GDAX - WebSocket connection closed (callback)")
        self.webSocketIsOpened = False

        if self.isRunning:  # If we are not exiting app
            if (self.IsConnectedAndOperational != "Requested"
                    and self.IsConnectedAndOperational != "Ongoing"):
                # If we are not re-initializing connection (like settings apply)
                print("GDAX - Unexpected close of websocket. Trying to restart.")
                while self.isRunning and not self.webSocketIsOpened:
                    print("GDAX - Restarting Websocket in 10 seconds...")
                    time.sleep(10)
                    self.startWebSocketFeed()
        print("GDAX - End of on_close()")

    def GDAX_GetLiveBestBidPrice(self):
        self.webSocketLock.acquire()
        liveBestBidPriceToReturn = self.liveBestBidPrice
        self.webSocketLock.release()

        return liveBestBidPriceToReturn

    def GDAX_GetLiveBestAskPrice(self):
        self.webSocketLock.acquire()
        liveBestAskPriceToReturn = self.liveBestAskPrice
        self.webSocketLock.release()

        return liveBestAskPriceToReturn

    def updateRealTimePriceInBackground(self):

        while self.isRunning:

            # Attempt a GDAX Initialization if requested
            if self.IsConnectedAndOperational == "Requested":
                self.IsConnectedAndOperational = "Ongoing"
                self.PerformConnectionInitializationAttempt()
                time.sleep(1)  # Don't poll GDAX API too much

            self.backgroundOperationsCounter = self.backgroundOperationsCounter + 1

            # Get Middle Market Price ==========================================================
            # Order book level 1 : Just the highest bid and lowest sell proposal
            try:
                result = ""
                result = self.clientPublic.book_ticker(self.productStr)
                self.tickBestBidPrice = float(result['bidPrice'])
                self.tickBestAskPrice = float(result['askPrice'])
                self.midMarketPrice = (self.tickBestBidPrice + self.tickBestAskPrice) / 2

                # DEBUG
                # print("GDAX - Highest Bid: %s" % self.tickBestBidPrice)
                # print("GDAX - Lowest Ask: %s" % self.tickBestAskPrice)

                self.PriceSpread = self.tickBestBidPrice - self.tickBestAskPrice
                self.theUIGraph.UIGR_updateConnectionText("Price data received from Coinbase Pro server")

                # Refresh account balances
                # Only do it if GDAX controler is OK in authenticated mode
                if self.IsConnectedAndOperational == "True":
                    if self.backgroundOperationsCounter % 20 == 0\
                            or self.requestAccountsBalanceUpdate:
                        self.requestAccountsBalanceUpdate = False
                        if self.IsConnectedAndOperational == "True":
                            self.refreshAccounts()

            except BaseException as e:
                print("GDAX - Error retrieving level 1 order book or account data")
                print("GDAX - Exception : " + str(e))
                print(result)
                self.requestAccountsBalanceUpdate = False

            # Get current Orders ===============================================================

            for x in range(0, 5):
                if not self.requestAccountsBalanceUpdate:
                    time.sleep(0.1)

            self.theUIGraph.UIGR_resetConnectionText()

            for x in range(0, 15):
                if not self.requestAccountsBalanceUpdate:
                    time.sleep(0.1)

    def GDAX_closeBackgroundOperations(self):

        self.isRunning = False

        if self.webSocketIsOpened:
            print("GDAX - Closing Websocket...")
            self.close()

    def GDAX_GetRealTimePriceInEUR(self):
        return self.midMarketPrice

    def GDAX_GetCurrentLimitOrderState(self):
        self.webSocketLock.acquire()
        currentState = self.currentOrderState

        if currentState == "FILLED":
            self.currentOrderState = "NONE"

        self.webSocketLock.release()

        return currentState

    def GDAX_GetAveragePriceInFiatAndSizeFilledInCrypto(self):
        print("GDAX - GDAX_GetAveragePriceInFiatAndSizeFilledInCrypto : "
              "AverageFilledPrice = %s, currentOrderFilledSizeInCrypo = %s"
              % (self.currentOrderAverageFilledPriceInFiat, self.currentOrderFilledSizeInCrypto))
        return [self.currentOrderAverageFilledPriceInFiat, self.currentOrderFilledSizeInCrypto]

    def GDAX_PlaceLimitBuyOrder(self, amountToBuyInCrypto, buyPriceInFiat):

        self.webSocketLock.acquire()

        if theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET:

            print("GDAX - GDAX_PlaceLimitBuyOrder")

            # First, cancel ongoing order if any
            if self.currentOrderState != "NONE":
                self.INTERNAL_CancelOngoingLimitOrder()

            # Send Limit order
            amountToBuyInCrypto = round(amountToBuyInCrypto, 8)

            # Don't use round because order could be placed on the other side of the spread -> rejected
            # Prix exprimé en BTC, arrondi variable
            if self.productFiatStr == "BTC":
                if self.productCryptoStr == "LTC":
                    buyPriceInFiat = math.floor(buyPriceInFiat * 1000000) / 1000000  # Floor à 0.000001
                else:
                    buyPriceInFiat = math.floor(buyPriceInFiat * 100000) / 100000  # Floor à 0.00001
            else:  # Prix exprimé en Fiat, arrondi à 0.01
                buyPriceInFiat = math.floor(buyPriceInFiat * 100) / 100

            buyRequestReturn = self.clientAuth.buy(price=str(buyPriceInFiat), size=str(amountToBuyInCrypto),
                                                   product_id=self.productStr, order_type='limit',
                                                   post_only=True)  # with Post Only
            print("GDAX - Actual buy sent with LIMIT order set to %s. Amount is %s Crypto"
                  % (buyPriceInFiat, amountToBuyInCrypto))
            print("GDAX - Limit order placing sent. Request return is: %s" % buyRequestReturn)
            if 'id' in buyRequestReturn:
                if not 'reject_reason' not in buyRequestReturn:
                    self.currentOrderId = buyRequestReturn['id']
                    self.currentOrderState = "SUBMITTED"
                    self.currentOrderInitialSizeInCrypto = amountToBuyInCrypto
                    self.currentOrderFilledSizeInCrypto = 0
                    self.currentOrderAverageFilledPriceInFiat = 0
                    print("GDAX - Limit order state set to SUBMITTED")

                    self.webSocketLock.release()
                    return True
                else:
                    print("GDAX - Buy limit order has been interpreted as rejected. Reason: %s" % buyRequestReturn[
                        'reject_reason'])

                    self.webSocketLock.release()
                    return False
            else:
                print("GDAX - Buy limit order has been interpreted as rejected")

                self.webSocketLock.release()
                return False
        else:
            # Simulation mode: simulate immediate order fill
            self.currentOrderId = -1
            self.currentOrderFilledSizeInCrypto = float(amountToBuyInCrypto)
            self.currentOrderAverageFilledPriceInFiat = float(buyPriceInFiat)
            print("GDAX - Limit buy simulated, buy price: %s, amountToBuyInCrypto: %s"
                  % round(float(buyPriceInFiat), 2), float(amountToBuyInCrypto))
            self.currentOrderState = "FILLED"

            self.webSocketLock.release()
            return True

    def GDAX_PlaceLimitSellOrder(self, amountToSellInCrypto, sellPriceInFiat):

        if theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET:

            self.webSocketLock.acquire()

            # First, cancel ongoing order if any
            if self.currentOrderState != "NONE":
                self.INTERNAL_CancelOngoingLimitOrder()

                # Send Limit order
            amountToSellInCrypto = round(amountToSellInCrypto, 8)

            # Don't use round because order could be placed on the other side of the spread -> rejected
            # Prix exprimé en BTC, arrondi variable
            if self.productFiatStr == "BTC":
                if self.productCryptoStr == "LTC":
                    sellPriceInFiat = math.floor(sellPriceInFiat * 1000000) / 1000000  # Floor à 0.000001
                else:
                    sellPriceInFiat = math.floor(sellPriceInFiat * 100000) / 100000  # Floor à 0.00001
            else:  # Prix exprimé en Fiat, arrondi à 0.01
                sellPriceInFiat = math.floor(sellPriceInFiat * 100) / 100

            sellRequestReturn = self.clientAuth.sell(price=str(sellPriceInFiat), size=str(amountToSellInCrypto),
                                                     product_id=self.productStr, order_type='limit',
                                                     post_only=True)  # with Post Only
            print("GDAX - Actual sell sent with LIMIT order set to %s. Amount is %s Crypto"
                  % (sellPriceInFiat, amountToSellInCrypto))
            print("GDAX - Limit order placing sent. Request return is: %s"
                  % sellRequestReturn)
            if 'id' in sellRequestReturn:
                self.currentOrderId = sellRequestReturn['id']
                self.currentOrderState = "SUBMITTED"
                self.currentOrderInitialSizeInCrypto = amountToSellInCrypto
                self.currentOrderFilledSizeInCrypto = 0
                self.currentOrderAverageFilledPriceInFiat = 0

                self.webSocketLock.release()
                return True
            else:
                print("GDAX - Sell limit order has been interpreted as rejected")

                self.webSocketLock.release()
                return False
        else:
            # Simulation mode: simulate immediate order fill
            self.currentOrderFilledSizeInCrypto = amountToSellInCrypto
            self.currentOrderAverageFilledPriceInFiat = sellPriceInFiat
            self.currentOrderState = "FILLED"

            self.webSocketLock.release()
            return True

    # Include thread safe protection: shall be called from outside
    def GDAX_CancelOngoingLimitOrder(self):
        self.webSocketLock.acquire()
        if self.currentOrderId != 0:
            self.currentOrderId = 0  # So that websocket won't get the cancel notification
            self.currentOrderState = "NONE"
            self.currentOrderInitialSizeInCrypto = 0
            self.currentOrderFilledSizeInCrypto = 0
            self.currentOrderAverageFilledPriceInFiat = 0
            cancelAllReturn = self.clientAuth.cancel_all(self.productStr)
            print("GDAX - GDAX_CancelOngoingLimitOrder: Ongoing order canceled. Request return is: %s"
                  % cancelAllReturn)
        else:
            print("GDAX - GDAX_CancelOngoingLimitOrder: No order to cancel! Just filled?")
        self.webSocketLock.release()

    # Does not include thread safe protection: shall not be called from outside
    def INTERNAL_CancelOngoingLimitOrder(self):

        if self.currentOrderId != 0:
            self.currentOrderId = 0  # So that websocket won't get the cancel notification
            self.currentOrderState = "NONE"
            self.currentOrderInitialSizeInCrypto = 0
            self.currentOrderFilledSizeInCrypto = 0
            self.currentOrderAverageFilledPriceInFiat = 0
            cancelAllReturn = self.clientAuth.cancel_all(self.productStr)
            print("GDAX - INTERNAL_CancelOngoingLimitOrder: Ongoing order canceled. Request return is: %s"
                  % cancelAllReturn)
        else:
            print("GDAX - INTERNAL_CancelOngoingLimitOrder: No order to cancel! Just filled?")

    def GDAX_SendBuyOrder(self, amountToBuyInBTC):
        if theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET:
            if theConfig.CONFIG_ENABLE_REAL_TRANSACTIONS:
                # Prepare the right amount to buy precision. Smallest GDAX unit is 0.00000001
                amountToBuyInBTC = round(amountToBuyInBTC, 8)

                # Send Market order
                buyRequestReturn = self.clientAuth.buy(size=amountToBuyInBTC, product_id=self.productStr,
                                                       order_type='market')
                print("GDAX - Actual buy sent with MARKET order. Amount is %s BTC"
                      % amountToBuyInBTC)

                print("GDAX - Buy Request return is : \n %s \nGDAX - End of Request Return"
                      % buyRequestReturn)

                self.requestAccountsBalanceUpdate = True

                # Check if order was successful or not depending on existence of an order ID in the request response
                if 'id' in buyRequestReturn:
                    print("GDAX - Buy order has been interpreted as successful")
                    return True
                else:
                    print("GDAX - Buy order has been interpreted as failed")
                    return False
            else:
                return False
        else:
            return False

    def GDAX_SendSellOrder(self, amountToSellInBTC):
        if theConfig.CONFIG_INPUT_MODE_IS_REAL_MARKET:
            if theConfig.CONFIG_ENABLE_REAL_TRANSACTIONS:
                # Prepare the right amount to sell precision. Smallest GDAX unit is 0.00000001
                amountToSellInBTC = round(amountToSellInBTC, 8)

                # Send Market order
                sellRequestReturn = self.clientAuth.sell(size=amountToSellInBTC, product_id=self.productStr,
                                                         order_type='market')
                print("Actual sell sent with MARKET order. Amount is %s" % amountToSellInBTC)

                print("GDAX - Sell Request return is : \n %s \nGDAX - End of Request Return"
                      % sellRequestReturn)
                time.sleep(0.1)
                self.refreshAccounts()
                time.sleep(0.1)
                self.requestAccountsBalanceUpdate = True

                # Check if order was successful or not depending on existence of an order ID in the request response
                if 'id' in sellRequestReturn:
                    print("GDAX - Sell order has been interpreted as successful")
                    return True
                else:
                    print("GDAX - Sell order has been interpreted as failed")
                    return False
            else:
                return False
        else:
            return False

    def GDAX_IsAmountToBuyAboveMinimum(self, amountOfCryptoToBuy):
        if self.theSettings.SETT_GetSettings()["strCryptoType"] == "BTC":
            return amountOfCryptoToBuy > 0.001

        if self.theSettings.SETT_GetSettings()["strCryptoType"] == "BCH":
            return amountOfCryptoToBuy > 0.01

        if self.theSettings.SETT_GetSettings()["strCryptoType"] == "LTC":
            return amountOfCryptoToBuy > 0.1

        if self.theSettings.SETT_GetSettings()["strCryptoType"] == "ETH":
            return amountOfCryptoToBuy > 0.01

        if self.theSettings.SETT_GetSettings()["strCryptoType"] == "ETC":
            return amountOfCryptoToBuy > 0.1

        return True

    def GDAX_WithdrawBTC(self, destinationAddress, amountToWithdrawInBTC):
        print("GDAX - Withdraw BTC")

        if not theConfig.CONFIG_DEBUG_ENABLE_DUMMY_WITHDRAWALS:
            withdrawRequestReturn = self.clientAuth.crypto_withdraw(amountToWithdrawInBTC, 'BTC', destinationAddress)

            print("GDAX - Withdraw request return: %s" % withdrawRequestReturn)
            # Check if withdraw was successful or not depending on existence of an order ID in the request response
            if 'id' in withdrawRequestReturn:
                print("GDAX - Withdraw has been interpreted as successful")
                return withdrawRequestReturn['id']
            else:
                print("GDAX - Withdraw has failed")
                return "Error"
        else:
            return "Dummy Withdraw"

    def GDAX_RequestAccountsBalancesUpdate(self):
        self.requestAccountsBalanceUpdate = True

    def GDAX_LoadHistoricData(self, startTimestamp, stopTimestamp):

        print("Init to retrieve Historic Data from %s to %s" % (
        datetime.fromtimestamp(startTimestamp).isoformat(), datetime.fromtimestamp(stopTimestamp).isoformat()))
        print("---------")
        # Reset read index are we will overwrite the buffer
        self.HistoricDataReadIndex = 0

        local_tz = get_localzone()
        print("GDAX - Local timezone found: %s" % local_tz)
        tz = pytz.timezone(str(local_tz))

        stopSlice = 0
        startSlice = startTimestamp
        self.HistoricDataRaw = []
        self.HistoricData = []

        # Progression measurement
        granularityInSec = round(self.GDAX_HISTORIC_DATA_MIN_GRANULARITY_IN_SEC)
        nbIterationsToRetrieveEverything = ((stopTimestamp - startTimestamp) /
                                            (round(self.GDAX_HISTORIC_DATA_MIN_GRANULARITY_IN_SEC))) \
                                           / round(self.GDAX_MAX_HISTORIC_PRICES_ELEMENTS)
        print("GDAX - Nb Max iterations to retrieve everything: %s"
              % nbIterationsToRetrieveEverything)
        nbLoopIterations = 0

        while stopSlice < stopTimestamp:

            stopSlice = startSlice + self.GDAX_MAX_HISTORIC_PRICES_ELEMENTS * granularityInSec
            if stopSlice > stopTimestamp:
                stopSlice = stopTimestamp
            print("GDAX - Start TS : %s  stop TS : %s" % (startSlice, stopSlice))

            startTimestampSliceInISO = datetime.fromtimestamp(startSlice, tz)
            stopTimestampSliceInISO = datetime.fromtimestamp(stopSlice, tz)
            print("GDAX - Retrieving Historic Data from %s to %s"
                  % (startTimestampSliceInISO, stopTimestampSliceInISO))
            if self.IsConnectedAndOperational == "True":
                print("GDAX - Using public client to retrieve historic prices")
                # MURPHY TODO: hardcode productstr
                HistoricDataSlice = self.clientPublic.klines("BTCUSDT",interval="1m",
                                                             endTime=round(stopTimestamp * 1000))

                # Only sleep if reloop condition is met
                if stopSlice < stopTimestamp:
                    time.sleep(0.350)
                print("GDAX - Using private client to retrieve historic prices")
            else:
                # MURPHY TODO: hardcode productstr
                HistoricDataSlice = self.clientPublic.klines("BTCUSDT", interval="1m",
                                                             endTime=round(stopTimestamp * 1000), limit=600)

                # Only sleep if reloop condition is met
                if stopSlice < stopTimestamp:
                    time.sleep(0.250)
                print("GDAX - Using public client to retrieve historic prices")

            print("GDAX - Size of HistoricDataSlice: %s" % len(HistoricDataSlice))

            try:  # parfois le reversed crash. Pas de data dans la slice ?
                for slice in HistoricDataSlice:
                    # slice - [OpenTime, open, high, low, close, volume, close time,
                    # QuoteAssetVolume, numOfTrade, TakerBuyBaseAssetVolume, TakerBuyQuoteAssetVolume, Ignore]

                    # new slice [OpenTime, low, high, open, close, volume, close time,
                    # QuoteAssetVolume, numOfTrade, TakerBuyBaseAssetVolume, TakerBuyQuoteAssetVolume, Ignore]
                    new_slice = np.asarray(slice).astype(np.float64)
                    new_slice[0] = new_slice[0] / 1000
                    open = new_slice[1]
                    low = new_slice[3]
                    new_slice[1] = low
                    new_slice[3] = open

                    self.HistoricDataRaw.append(new_slice)
            except BaseException as e:
                print("GDAX - Exception when reversing historic data slice")

            startSlice = stopSlice  # Prepare next iteration

            # Progress report
            nbLoopIterations = nbLoopIterations + 1
            percentage = round(nbLoopIterations * 100 / nbIterationsToRetrieveEverything)
            if percentage > 100:
                percentage = 100
            self.theUIGraph.UIGR_updateLoadingDataProgress(str(percentage))

        # Clean buffer so that only data in the chronological order remains
        print("GDAX - LoadHistoricData - Cleaning buffer. Nb elements before cleaning : %s"
              % len(self.HistoricDataRaw))
        tempIterationIndex = 0
        currentBrowsedTimestamp = 0
        while tempIterationIndex < len(self.HistoricDataRaw):
            if self.HistoricDataRaw[tempIterationIndex][0] <= currentBrowsedTimestamp + 1:
                # Useless data : do not copy into final buffer
                pass
            else:
                currentBrowsedTimestamp = self.HistoricDataRaw[tempIterationIndex][0]
                self.HistoricData.append(self.HistoricDataRaw[tempIterationIndex])

            # print(self.HistoricData[tempIterationIndex][0])
            tempIterationIndex = tempIterationIndex + 1

        print("GDAX - %s Historical samples have been retrieved (after cleaning)"
              % len(self.HistoricData))

    # Returns a price data sample CONFIG_TIME_BETWEEN_RETRIEVED_SAMPLES_IN_MS seconds after the last call
    # even if GDAX historic sample period is longer
    def GDAX_GetNextHistoricDataSample(self):
        # print("GDAX - Full Historic data list length is %s" % len(self.HistoricData))

        endOfList = False
        self.HistoricDataReadIndex = self.HistoricDataReadIndex + 1
        if self.HistoricDataReadIndex + 1 >= len(self.HistoricData):
            # We've read as many samples as they are in the list
            endOfList = True
            print("GDAX - Historic Data - End of list reached")

        # Fifth element (index 4) is the closure price
        # print("Historic Data", self.HistoricData)
        # print("2", self.HistoricDataReadIndex)
        # print("end of list", endOfList)
        return [self.HistoricData[self.HistoricDataReadIndex][0], self.HistoricData[self.HistoricDataReadIndex][4],
                endOfList]

    def GDAX_SetReadIndexFromPos(self, positionTimeStamp):
        tempIterationIndex = 0
        bReadIndexFound = False
        print("GDAX - SetReadIndexFromPos : %d" % positionTimeStamp)
        print("GDAX - Historic data length is %s" % len(self.HistoricData))

        while tempIterationIndex < len(self.HistoricData) and not bReadIndexFound:
            if self.HistoricData[tempIterationIndex][0] > positionTimeStamp:
                self.HistoricDataReadIndex = tempIterationIndex
                bReadIndexFound = True
            tempIterationIndex = tempIterationIndex + 1

        if bReadIndexFound:
            print("GDAX - SetReadIndexFromPos : index found: %s"
                  % self.HistoricDataReadIndex)
            return True
        else:
            print("GDAX - SetReadIndexFromPos : index not found")
            return False

    # Return the number of samples that can be read starting from the current readIndex position,
    # until the end of the buffer
    def GDAX_GetNumberOfSamplesLeftToRead(self):
        nbOfSamplesLeftToRead = len(self.HistoricData) - self.HistoricDataReadIndex
        print("GDAX - Number of samples left to read is %s" % nbOfSamplesLeftToRead)
        return nbOfSamplesLeftToRead

    def GDAX_GetHistoricDataSubSchedulingFactor(self):
        return self.GDAX_HISTORIC_DATA_SUBSCHEDULING_FACTOR

    def GDAX_GetLoadedDataStartTimeStamp(self):
        if len(self.HistoricData) > 2:
            return self.HistoricData[0][0]
        else:
            return 99999999999

    def GDAX_GetLoadedDataStopTimeStamp(self):
        if len(self.HistoricData) > 2:
            return self.HistoricData[-1][0]
        else:
            return 0

    def GDAX_ListAccountWithdrawals(self):
        print(self.clientAuth.get_account_history(self.CryptoAccount['id']))
