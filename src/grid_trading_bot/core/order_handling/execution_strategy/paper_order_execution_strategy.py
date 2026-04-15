import time

from ..order import Order, OrderSide, OrderStatus, OrderType
from .order_execution_strategy_interface import OrderExecutionStrategyInterface


class PaperOrderExecutionStrategy(OrderExecutionStrategyInterface):
    """
    Simulated execution for paper trading.

    Uses live market data for decisioning, but never calls private exchange
    order endpoints.
    """

    def __init__(self, slippage: float = 0.0) -> None:
        self.slippage = slippage
        self._orders: dict[str, Order] = {}

    async def execute_market_order(
        self,
        order_side: OrderSide,
        pair: str,
        quantity: float,
        price: float,
    ) -> Order | None:
        timestamp = int(time.time() * 1000)
        order_id = f"paper-{timestamp}"
        average = self._apply_slippage(price, order_side)

        order = Order(
            identifier=order_id,
            status=OrderStatus.CLOSED,
            order_type=OrderType.MARKET,
            side=order_side,
            price=price,
            average=average,
            amount=quantity,
            filled=quantity,
            remaining=0.0,
            timestamp=timestamp,
            datetime="",
            last_trade_timestamp=timestamp,
            symbol=pair,
            time_in_force="IOC",
        )
        self._orders[order_id] = order
        return order

    async def execute_limit_order(
        self,
        order_side: OrderSide,
        pair: str,
        quantity: float,
        price: float,
    ) -> Order | None:
        timestamp = int(time.time() * 1000)
        order_id = f"paper-{timestamp}"
        order = Order(
            identifier=order_id,
            status=OrderStatus.OPEN,
            order_type=OrderType.LIMIT,
            side=order_side,
            price=price,
            average=price,
            amount=quantity,
            filled=0.0,
            remaining=quantity,
            timestamp=timestamp,
            datetime="",
            last_trade_timestamp=timestamp,
            symbol=pair,
            time_in_force="GTC",
        )
        self._orders[order_id] = order
        return order

    async def get_order(
        self,
        order_id: str,
        pair: str,
    ) -> Order | None:
        return self._orders.get(order_id)

    def _apply_slippage(self, price: float, order_side: OrderSide) -> float:
        if not self.slippage:
            return price
        return price * (1 + self.slippage) if order_side == OrderSide.BUY else price * (1 - self.slippage)
