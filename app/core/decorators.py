import functools
import time
import traceback
from typing import Callable, Awaitable, TypeVar, ParamSpec

from fastapi import HTTPException, status

from app.core.logger_config import logger
from app.core.config import get_settings

settings = get_settings()

P = ParamSpec("P")
R = TypeVar("R")


def log_and_catch(debug: bool = settings.DEBUG_HTTP) -> Callable[
    [Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Определяем контекст для лога (имя функции и базовые параметры)
            func_name = func.__name__
            # Пытаемся угадать 'метод' и 'url' из kwargs, если это HTTP-запрос
            method = kwargs.get("method", "FUNC")  # Используем FUNC как дефолт, если не HTTP
            url = kwargs.get("url", func_name)  # Используем имя функции, если URL не передан

            # Лог до вызова функции
            if debug:
                log_prefix = f"[{method}] {url}"  # Формируем префикс
                logger.debug(f"{log_prefix} — start")
                # Логируем основные аргументы/параметры, если они есть
                args_preview = str(args)[:300] if args else ""
                kwargs_preview = str({k: v for k, v in kwargs.items() if k != 'http_service' and k != 'cookies'})[
                                 :500]  # Исключаем большие объекты
                if args_preview: logger.debug(f"{log_prefix} Args: {args_preview}...")
                if kwargs_preview and kwargs_preview != '{}': logger.debug(f"{log_prefix} Kwargs: {kwargs_preview}...")
                # Дополнительное логирование для HTTPX (если есть)
                if method != "FUNC":
                    if "params" in kwargs: logger.debug(f"{log_prefix} Params: {str(kwargs['params'])[:300]}...")
                    if "data" in kwargs: logger.debug(f"{log_prefix} Data: {str(kwargs['data'])[:300]}...")
                    if "cookies" in kwargs:
                        cookies_preview = {k: v[:10] + "..." if isinstance(v, str) and len(v) > 10 else v for k, v in
                                           kwargs['cookies'].items()}
                        logger.debug(f"{log_prefix} Cookies: {cookies_preview}")

            # Засекаем время выполнения
            start_time = time.perf_counter()

            try:
                # Выполняем обернутую функцию
                result = await func(*args, **kwargs)
                duration = round(time.perf_counter() - start_time, 2)

                # Логирование успешного выполнения
                if debug:
                    log_prefix = f"[{method}] {url}"  # Префикс для лога
                    logger.debug(f"{log_prefix} — success for {duration}s")
                    try:
                        log_msg = f"{log_prefix} Response: "
                        if isinstance(result, dict):
                            # Если это результат от HTTPXClient.fetch
                            if 'status_code' in result and 'json' in result:
                                json_data = result.get('json')
                                preview = str(json_data)[:500] if json_data is not None else 'None'
                                log_msg += f"HTTP Status: {result['status_code']}, JSON Preview: {preview}"
                                if len(str(json_data)) > 500: log_msg += "..."
                            # Если это другой словарь (например, от process_getting_code)
                            else:
                                preview = str(result)[:500]
                                log_msg += f"Dict Preview: {preview}"
                                if len(str(result)) > 500: log_msg += "..."
                        # Если результат - строка (например, от get_fias_api_token)
                        elif isinstance(result, str):
                            preview = result[:500]
                            log_msg += f"String Preview: '{preview}'"
                            if len(result) > 500: log_msg += "..."
                        # Если результат - None
                        elif result is None:
                            log_msg += "None"
                        # Другие типы
                        else:
                            preview = str(result)[:500]
                            log_msg += f"{type(result).__name__} Preview: {preview}"
                            if len(str(result)) > 500: log_msg += "..."

                        logger.debug(log_msg)

                    except Exception as log_ex:
                        logger.warning(f"{log_prefix} Failed to log result: {log_ex}")

                return result

            except HTTPException as e:
                # Логируем HTTP-ошибки и пробрасываем дальше
                logger.warning(f"[HTTPX] {method} {url} — HTTP error: {e.status_code} - {e.detail}")
                raise

            except Exception as e:
                # Обработка непредвиденных ошибок
                duration = round(time.perf_counter() - start_time, 2)

                # Вытаскиваем строку, где упало
                tb = traceback.extract_tb(e.__traceback__)
                last_frame = tb[-1] if tb else None
                lineno = last_frame.lineno if last_frame else "?"

                logger.error(
                    f"[HTTPX] ❌ Error in '{func_name}' (line '{lineno}') — {method} {url} for {duration}s: {e}"
                )

                if debug:
                    logger.debug("Trace:\n" + "".join(traceback.format_tb(e.__traceback__)))

                # Пробрасываем ошибку как HTTPException
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error in '{func_name}' (line '{lineno}') with request {method} {url}: {str(e)}"
                )

        return wrapper

    return decorator
