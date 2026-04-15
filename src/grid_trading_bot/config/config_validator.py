import logging
from typing import Any

from grid_trading_bot.core.domain.spacing_type import SpacingType
from grid_trading_bot.core.domain.strategy_type import StrategyType

from .exceptions import ConfigValidationError
from .trading_mode import TradingMode


class ConfigValidator:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate(self, config: dict[str, Any]) -> None:
        missing_fields: list[str] = []
        invalid_fields: list[str] = []
        missing_fields += self._validate_required_fields(config)
        invalid_fields += self._validate_exchange(config)
        missing_fields += self._validate_pair(config)
        missing_trading_settings, invalid_trading_settings = self._validate_trading_settings(config)
        missing_fields += missing_trading_settings
        invalid_fields += invalid_trading_settings
        missing_grid_settings, invalid_grid_settings = self._validate_grid_strategy(config)
        missing_fields += missing_grid_settings
        invalid_fields += invalid_grid_settings
        invalid_fields += self._validate_risk_management(config)
        missing_logging_settings, invalid_logging_settings = self._validate_logging(config)
        missing_fields += missing_logging_settings
        invalid_fields += invalid_logging_settings

        if "execution" in config:
            invalid_fields += self._validate_execution(config)

        if missing_fields or invalid_fields:
            raise ConfigValidationError(missing_fields=missing_fields, invalid_fields=invalid_fields)

    def _validate_required_fields(self, config: dict[str, Any]) -> list[str]:
        required_fields = ["exchange", "pair", "trading_settings", "grid_strategy", "risk_management", "logging"]
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            self.logger.error(f"Missing required fields: {missing_fields}")
        return missing_fields

    def _validate_exchange(self, config: dict[str, Any]) -> list[str]:
        invalid_fields: list[str] = []
        exchange = config.get("exchange", {})

        if not exchange.get("name"):
            self.logger.error("Exchange name is missing.")
            invalid_fields.append("exchange.name")

        trading_fee = exchange.get("trading_fee")
        if trading_fee is None or not isinstance(trading_fee, float | int) or trading_fee < 0:
            self.logger.error("Invalid or missing trading fee.")
            invalid_fields.append("exchange.trading_fee")

        trading_mode_str = exchange.get("trading_mode")
        if not trading_mode_str:
            invalid_fields.append("exchange.trading_mode")
        else:
            try:
                TradingMode.from_string(trading_mode_str)
            except ValueError:
                invalid_fields.append("exchange.trading_mode")

        return invalid_fields

    def _validate_pair(self, config: dict[str, Any]) -> list[str]:
        missing_fields: list[str] = []
        pair = config.get("pair", {})

        if not pair.get("base_currency"):
            missing_fields.append("pair.base_currency")
        if not pair.get("quote_currency"):
            missing_fields.append("pair.quote_currency")

        if missing_fields:
            self.logger.error(f"Missing pair configuration fields: {missing_fields}")

        return missing_fields

    def _validate_trading_settings(self, config: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing_fields: list[str] = []
        invalid_fields: list[str] = []
        trading_settings = config.get("trading_settings", {})

        if not trading_settings.get("initial_balance"):
            missing_fields.append("trading_settings.initial_balance")

        # Validate timeframe
        timeframe = trading_settings.get("timeframe")
        valid_timeframes = ["1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "6h", "12h", "1d", "1w", "1M"]
        if timeframe not in valid_timeframes:
            self.logger.error(f"Invalid timeframe: {timeframe}. Must be one of {valid_timeframes}.")
            invalid_fields.append("trading_settings.timeframe")

        # Validate period
        period = trading_settings.get("period", {})
        start_date = period.get("start_date")
        end_date = period.get("end_date")

        if not start_date:
            missing_fields.append("trading_settings.period.start_date")
        if not end_date:
            missing_fields.append("trading_settings.period.end_date")

        return missing_fields, invalid_fields

    def _validate_grid_strategy(self, config: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing_fields: list[str] = []
        invalid_fields: list[str] = []
        grid = config.get("grid_strategy", {})

        grid_type = grid.get("type")
        if grid_type is None:
            missing_fields.append("grid_strategy.type")
        else:
            try:
                StrategyType.from_string(grid_type)

            except ValueError as e:
                self.logger.error(str(e))
                invalid_fields.append("grid_strategy.type")

        spacing = grid.get("spacing")
        if spacing is None:
            missing_fields.append("grid_strategy.spacing")
        else:
            try:
                SpacingType.from_string(spacing)

            except ValueError as e:
                self.logger.error(str(e))
                invalid_fields.append("grid_strategy.spacing")

        num_grids = grid.get("num_grids")
        if num_grids is None:
            missing_fields.append("grid_strategy.num_grids")
        elif not isinstance(num_grids, int) or num_grids <= 0:
            self.logger.error("Grid strategy 'num_grids' must be a positive integer.")
            invalid_fields.append("grid_strategy.num_grids")

        range_ = grid.get("range", {})
        top = range_.get("top")
        bottom = range_.get("bottom")
        if top is None:
            missing_fields.append("grid_strategy.range.top")
        if bottom is None:
            missing_fields.append("grid_strategy.range.bottom")

        if top is not None and bottom is not None:
            if not isinstance(top, int | float) or not isinstance(bottom, int | float):
                self.logger.error("'top' and 'bottom' in 'grid_strategy.range' must be numbers.")
                invalid_fields.append("grid_strategy.range.top")
                invalid_fields.append("grid_strategy.range.bottom")
            elif bottom >= top:
                self.logger.error("'grid_strategy.range.bottom' must be less than 'grid_strategy.range.top'.")
                invalid_fields.append("grid_strategy.range.top")
                invalid_fields.append("grid_strategy.range.bottom")

        for ratio_field in ("buy_ratio", "sell_ratio"):
            value = grid.get(ratio_field)
            if value is not None and (not isinstance(value, int | float) or value <= 0 or value > 1.0):
                self.logger.error(
                    f"grid_strategy.{ratio_field} must be a number between 0 (exclusive) and 1.0 (inclusive)."
                )
                invalid_fields.append(f"grid_strategy.{ratio_field}")

        return missing_fields, invalid_fields

    def _validate_risk_management(self, config: dict[str, Any]) -> list[str]:
        invalid_fields: list[str] = []
        limits = config.get("risk_management", {})
        take_profit = limits.get("take_profit", {})
        stop_loss = limits.get("stop_loss", {})

        # Validate take profit
        if not isinstance(take_profit.get("enabled"), bool):
            self.logger.error("Take profit enabled flag must be a boolean.")
            invalid_fields.append("risk_management.take_profit.enabled")

        if take_profit.get("threshold") is None or not isinstance(take_profit.get("threshold"), float | int):
            self.logger.error("Invalid or missing take profit threshold.")
            invalid_fields.append("risk_management.take_profit.threshold")

        # Validate stop loss
        if not isinstance(stop_loss.get("enabled"), bool):
            self.logger.error("Stop loss enabled flag must be a boolean.")
            invalid_fields.append("risk_management.stop_loss.enabled")

        if stop_loss.get("threshold") is None or not isinstance(stop_loss.get("threshold"), float | int):
            self.logger.error("Invalid or missing stop loss threshold.")
            invalid_fields.append("risk_management.stop_loss.threshold")

        invalid_fields += self._validate_position_sizing(config)
        invalid_fields += self._validate_risk_safety_checks(config, take_profit, stop_loss)
        return invalid_fields

    def _validate_position_sizing(self, config: dict[str, Any]) -> list[str]:
        invalid_fields: list[str] = []
        ps = config.get("risk_management", {}).get("position_sizing")
        if ps is None:
            return invalid_fields
        if not isinstance(ps, dict):
            self.logger.error("risk_management.position_sizing must be an object.")
            invalid_fields.append("risk_management.position_sizing")
            return invalid_fields

        max_frac = ps.get("max_portfolio_fraction", 1.0)
        max_frac_valid = isinstance(max_frac, int | float) and 0 < max_frac <= 1
        if not max_frac_valid:
            self.logger.error("max_portfolio_fraction must be a number in (0, 1].")
            invalid_fields.append("risk_management.position_sizing.max_portfolio_fraction")

        min_quote = ps.get("min_quote_notional_per_grid")
        if min_quote is not None:
            if not isinstance(min_quote, int | float) or min_quote <= 0:
                self.logger.error("min_quote_notional_per_grid must be a positive number when set.")
                invalid_fields.append("risk_management.position_sizing.min_quote_notional_per_grid")
            elif max_frac_valid:
                trading = config.get("trading_settings", {})
                grid = config.get("grid_strategy", {})
                initial = trading.get("initial_balance")
                num_grids = grid.get("num_grids")
                if isinstance(initial, int | float) and isinstance(num_grids, int) and num_grids > 0:
                    quote_per_grid = float(initial) * float(max_frac) / num_grids
                    if quote_per_grid < float(min_quote):
                        self.logger.error(
                            "initial_balance * max_portfolio_fraction / num_grids must be >= "
                            "min_quote_notional_per_grid.",
                        )
                        invalid_fields.append("risk_management.position_sizing.min_quote_notional_per_grid")

        return invalid_fields

    def _validate_risk_safety_checks(
        self,
        config: dict[str, Any],
        take_profit: dict[str, Any],
        stop_loss: dict[str, Any],
    ) -> list[str]:
        invalid_fields: list[str] = []
        safety = config.get("risk_management", {}).get("safety")

        tp_on = take_profit.get("enabled") is True
        sl_on = stop_loss.get("enabled") is True
        tp_th = take_profit.get("threshold")
        sl_th = stop_loss.get("threshold")

        if tp_on and sl_on and isinstance(tp_th, int | float) and isinstance(sl_th, int | float):
            if sl_th >= tp_th:
                self.logger.error(
                    "When both take-profit and stop-loss are enabled, stop_loss.threshold must be "
                    "strictly less than take_profit.threshold.",
                )
                invalid_fields.append("risk_management.stop_loss.threshold")
                invalid_fields.append("risk_management.take_profit.threshold")

        if safety is not None and not isinstance(safety, dict):
            self.logger.error("risk_management.safety must be an object.")
            invalid_fields.append("risk_management.safety")
            return invalid_fields

        enforce_grid = bool(safety.get("enforce_tp_sl_vs_grid_range")) if isinstance(safety, dict) else False

        if enforce_grid:
            grid = config.get("grid_strategy", {})
            range_ = grid.get("range", {})
            top = range_.get("top")
            bottom = range_.get("bottom")
            if isinstance(top, int | float) and isinstance(bottom, int | float):
                if tp_on and isinstance(tp_th, int | float) and tp_th <= top:
                    self.logger.error(
                        "safety.enforce_tp_sl_vs_grid_range requires take_profit.threshold > "
                        "grid_strategy.range.top.",
                    )
                    invalid_fields.append("risk_management.take_profit.threshold")
                if sl_on and isinstance(sl_th, int | float) and sl_th >= bottom:
                    self.logger.error(
                        "safety.enforce_tp_sl_vs_grid_range requires stop_loss.threshold < "
                        "grid_strategy.range.bottom.",
                    )
                    invalid_fields.append("risk_management.stop_loss.threshold")

        if isinstance(safety, dict):
            flag = safety.get("enforce_tp_sl_vs_grid_range")
            if flag is not None and not isinstance(flag, bool):
                self.logger.error("enforce_tp_sl_vs_grid_range must be a boolean.")
                invalid_fields.append("risk_management.safety.enforce_tp_sl_vs_grid_range")

        return invalid_fields

    def _validate_execution(self, config: dict[str, Any]) -> list[str]:
        invalid_fields: list[str] = []
        execution = config.get("execution", {})

        int_fields = {
            "max_retries": (1, 20),
            "websocket_max_retries": (1, 50),
            "websocket_retry_base_delay": (1, 120),
            "health_check_interval": (10, 3600),
            "circuit_breaker_failure_threshold": (1, 50),
            "circuit_breaker_half_open_max_calls": (1, 10),
        }
        float_fields = {
            "retry_delay": (0.1, 60.0),
            "max_slippage": (0.0001, 0.1),
            "order_polling_interval": (1.0, 300.0),
            "circuit_breaker_recovery_timeout": (1.0, 600.0),
            "backtest_slippage": (0.0, 0.1),
        }

        for field, (min_val, max_val) in int_fields.items():
            value = execution.get(field)
            if value is not None and (not isinstance(value, int) or value < min_val or value > max_val):
                self.logger.error(f"execution.{field} must be an integer between {min_val} and {max_val}.")
                invalid_fields.append(f"execution.{field}")

        for field, (min_val, max_val) in float_fields.items():
            value = execution.get(field)
            if value is not None and (not isinstance(value, int | float) or value < min_val or value > max_val):
                self.logger.error(f"execution.{field} must be a number between {min_val} and {max_val}.")
                invalid_fields.append(f"execution.{field}")

        return invalid_fields

    def _validate_logging(self, config: dict[str, Any]) -> tuple[list[str], list[str]]:
        missing_fields: list[str] = []
        invalid_fields: list[str] = []
        logging_settings = config.get("logging", {})

        # Validate log level
        log_level = logging_settings.get("log_level")
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level is None:
            missing_fields.append("logging.log_level")
        elif log_level.upper() not in valid_log_levels:
            self.logger.error(f"Invalid log level: {log_level}. Must be one of {valid_log_levels}.")
            invalid_fields.append("logging.log_level")

        # Validate log to file
        if not isinstance(logging_settings.get("log_to_file"), bool):
            self.logger.error("log_to_file must be a boolean.")
            invalid_fields.append("logging.log_to_file")

        if missing_fields:
            self.logger.error(f"Missing logging fields: {missing_fields}")

        return missing_fields, invalid_fields
