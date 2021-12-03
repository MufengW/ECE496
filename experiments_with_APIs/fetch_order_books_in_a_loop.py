#!/usr/bin/env python

import logging
import time
from binance.spot import Spot as Client
from binance.lib.utils import config_logging

config_logging(logging, logging.DEBUG)

spot_client = Client(base_url="https://testnet.binance.vision")
MAX_FETCH_TIME = 0.5
NUM_ITERATIONS = 100
IGNORE_START_ITERS = 10
SYMBOL = "BTCUSDT"


def orderbook_valid(orderbook):
    """
    Return a bool

    check if each field of the order book exists and makes sense
    """
    try:
        if orderbook['symbol'] != SYMBOL:
            return False
        if float(orderbook['bidPrice']) <= 0 or float(orderbook['bidQty']) <= 0 \
                or float(orderbook['askPrice']) <= 0 or float(orderbook['askQty']) <= 0:
            return False
    except:
        return False
    return True

for i in range(5):
    logging.info(spot_client.book_ticker(SYMBOL))
    time.sleep(1)

num_of_failure = 0
num_of_expiration = 0
for i in range(NUM_ITERATIONS):
    begin = time.time()
    order_book = spot_client.book_ticker(SYMBOL)
    fetch_time = time.time() - begin
    # when the connection just started, fetch time is slightly higher, ignore this period
    if i < IGNORE_START_ITERS:
        continue
    if fetch_time > MAX_FETCH_TIME:
        num_of_expiration += 1
        print("the {}th experiment exceeds the maximum required time. It took {} seconds".format(i, fetch_time))
    if not orderbook_valid(order_book):
        num_of_failure += 1
        print("the {}th experiment fails".format(i))

start_time = time.time()
for i in range(NUM_ITERATIONS):
    order_book = spot_client.book_ticker(SYMBOL)
total_time = time.time() - start_time

print('total failure of fetching: {}, total expiration: {} in {} fetches'.format(num_of_failure, num_of_expiration, NUM_ITERATIONS))
print("It takes {} seconds to fetch orderbooks {} times".format(total_time, NUM_ITERATIONS))
