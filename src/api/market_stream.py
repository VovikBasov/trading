import asyncio
import logging
from typing import Callable, Any

from t_tech.invest import (
    AsyncClient,
    MarketDataRequest,
    SubscribeOrderBookRequest,
    SubscriptionAction,
    OrderBookInstrument,
    OrderBook
)

from src.config import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderBookStream:
    def __init__(self):
        self.token = config.api_token
        self.use_sandbox = config.use_sandbox
        self.client = None
        self._stop_event = asyncio.Event()
        self._request_iterator = None

        mode = "ПРОДАКШЕН (боевой режим)" if not self.use_sandbox else "ПЕСОЧНИЦА (тестовый режим)"
        logger.info(f"Инициализация стрима. Режим: {mode}")

    async def _request_generator(self, instrument_id: str, depth: int):
        """Асинхронный генератор, который отправляет запрос на подписку."""
        # Первым сообщением отправляем запрос на подписку
        yield MarketDataRequest(
            subscribe_order_book_request=SubscribeOrderBookRequest(
                subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                instruments=[
                    OrderBookInstrument(
                        instrument_id=instrument_id,
                        depth=depth
                    )
                ]
            )
        )

        # Далее генератор должен работать, чтобы поток не закрывался
        # Отправляем пустые сообщения для поддержания соединения
        while not self._stop_event.is_set():
            await asyncio.sleep(1)  # Просто ждем, не отправляя новых данных
            # Можно yield None или просто продолжать цикл
            # yield None  # Некоторые реализации требуют периодического yield

    async def subscribe_to_orderbook(
        self,
        instrument_id: str,
        depth: int = 10,
        callback: Callable[[OrderBook], Any] = None
    ) -> None:
        try:
            async with AsyncClient(
                token=self.token,
                app_name=config.app_name
            ) as client:
                self.client = client
                logger.info(f"Клиент подключен к {'боевому API' if not self.use_sandbox else 'песочнице'}")

                # 1. Создаем генератор запросов
                self._request_iterator = self._request_generator(instrument_id, depth)

                # 2. Получаем стрим, передав ему итератор запросов (ключевое исправление!)
                stream = client.market_data_stream.market_data_stream(self._request_iterator)

                logger.info(f"Подписка на стакан отправлена. FIGI: {instrument_id}, глубина: {depth}")

                # 3. Обрабатываем входящие сообщения из потока
                async for market_data in stream:
                    if self._stop_event.is_set():
                        logger.info("Получен сигнал остановки")
                        break

                    # Обрабатываем данные стакана
                    if market_data.orderbook:
                        orderbook = market_data.orderbook

                        if callback:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(orderbook)
                                else:
                                    callback(orderbook)
                            except Exception as e:
                                logger.error(f"Ошибка в callback: {e}")

                    # Обрабатываем ответ на подписку
                    elif market_data.subscribe_order_book_response:
                        response = market_data.subscribe_order_book_response
                        for subscription in response.order_book_subscriptions:
                            status = subscription.subscription_status
                            uid = subscription.instrument_uid or instrument_id
                            logger.info(f"Статус подписки для {uid}: {status}")
                            if status != "SUBSCRIPTION_STATUS_SUCCESS":
                                logger.warning(f"Проблема с подпиской на {uid}: {status}")

        except Exception as e:
            logger.error(f"Ошибка в стриме: {e}", exc_info=True)
            raise
        finally:
            logger.info("Стрим полностью остановлен")

    def stop(self):
        """Подает сигнал для остановки стрима извне."""
        self._stop_event.set()
        logger.info("Сигнал остановки отправлен")


# Пример callback-функции
async def print_orderbook_snapshot(orderbook: OrderBook):
    if orderbook.bids and orderbook.asks:
        best_bid = orderbook.bids[0]
        best_ask = orderbook.asks[0]
        bid_price = f"{best_bid.price.units}.{best_bid.price.nano:09d}"
        ask_price = f"{best_ask.price.units}.{best_ask.price.nano:09d}"
        bid_price = bid_price.rstrip('0').rstrip('.') if '.' in bid_price else bid_price
        ask_price = ask_price.rstrip('0').rstrip('.') if '.' in ask_price else ask_price
        print(f"[{orderbook.figi}] "
              f"Bid: {bid_price} x{best_bid.quantity} | "
              f"Ask: {ask_price} x{best_ask.quantity} | "
              f"Время: {orderbook.time}")


# Главная функция для запуска
# Вставьте этот код в конец существующего файла src/api/market_stream.py
# (ЗАМЕНИТЕ старую функцию main, начиная со строки "async def main():")

async def main():
    """Точка входа для запуска стрима с аккуратной обработкой завершения."""
    test_instrument_id = "BBG004730N88"
    stream = OrderBookStream()

    try:
        logger.info(f"Запуск стрима для FIGI: {test_instrument_id}")
        await stream.subscribe_to_orderbook(
            instrument_id=test_instrument_id,
            depth=10,
            callback=print_orderbook_snapshot
        )
    except asyncio.exceptions.CancelledError:
        # Ловим внутреннее исключение отмены задачи
        logger.info("Задача стрима отменена.")
        raise  # Пробрасываем дальше для стандартной обработки
    except KeyboardInterrupt:
        # Ловим прямое прерывание от пользователя (Ctrl+C)
        logger.info("Получен сигнал прерывания от пользователя (Ctrl+C). Корректная остановка...")
        stream.stop()
        # Даем короткую паузу на отправку финальных логов
        await asyncio.sleep(0.2)
        logger.info("Стрим остановлен по запросу пользователя.")
    except Exception as e:
        logger.error(f"Критическая ошибка в работе стрима: {e}")
    finally:
        # Гарантируем, что сигнал остановки установлен
        stream.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Финализируем, если прерывание произошло на верхнем уровне
        print("\n\n[ВНИМАНИЕ] Работа бота завершена пользователем. Все соединения закрыты.")
