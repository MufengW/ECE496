import time
import logging
from binance.spot import Spot as Client
from binance.lib.utils import config_logging
from binance.error import ClientError

config_logging(logging, logging.DEBUG)

key = "5St8GRwYWckPOeWpp88FZQx87A5KRR6A9dDnV6BQVIOBSy2XGk2xRGpOPei2CgWk"
secret = "teQDw85j5jDk8EokZDd4aaBDfHP0p9HCOqpYVzb2MyzU3EDLGIBmjKcOUUTFmdYZ"
SYMBOL = "BTCUSDT"
params = {
    "symbol": SYMBOL,
    "side": "SELL",
    "type": "MARKET",
    # "timeInForce": "GTC",
    "quantity": 0.01,
    # "price": 0,
}

client = Client(key, secret, base_url="https://testnet.binance.vision")
initial_account_status = client.account()

last_ticker_book_price = client.book_ticker(SYMBOL)
wait_until_this_time = time.time() + 2
for i in range(100):
    while (time.time() < wait_until_this_time):
        ticker_book_price = client.book_ticker(SYMBOL)
    wait_until_this_time = time.time() + 2
    if ticker_book_price['bidPrice'] > last_ticker_book_price['askPrice']:
        params['side'] = "BUY"
        # params['price'] = ticker_book_price['askPrice']
        try:
            response = client.new_order(**params)
            logging.info(response)
        except ClientError as error:
            logging.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
        )
        print('transaction')
    elif ticker_book_price['askPrice'] < last_ticker_book_price['bidPrice']:
        params['side'] = "SELL"
        # params['price'] = ticker_book_price['bidPrice']
        try:
            response = client.new_order(**params)
            logging.info(response)
        except ClientError as error:
            logging.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
        print('transaction')
    last_ticker_book_price = ticker_book_price
final_account_status = client.account()
print(initial_account_status)
print(final_account_status)