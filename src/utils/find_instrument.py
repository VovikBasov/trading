#!/usr/bin/env python3
"""
Утилита для поиска инструментов по тикеру.
"""
import sys
import os
import asyncio

# Добавляем корень проекта в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))  # src/utils
project_root = os.path.dirname(os.path.dirname(current_dir))  # tinvest-bot
sys.path.insert(0, project_root)

from src.config import config
# ИСПРАВЛЕНО: используем новый импорт t_tech вместо tinkoff
from t_tech.invest import AsyncClient

async def find_instrument_by_ticker(ticker: str):
    """Поиск инструмента по тикеру."""
    print(f"Поиск инструмента для тикера: '{ticker}'")
    print(f"Режим: {'ПЕСОЧНИЦА' if config.use_sandbox else 'ПРОДАКШЕН'}")

    async with AsyncClient(token=config.api_token, app_name=config.app_name) as client:
        response = await client.instruments.find_instrument(query=ticker)

        if not response.instruments:
            print(f"Инструменты с тикером '{ticker}' не найдены")
            return

        print(f"\nНайдено {len(response.instruments)} инструментов:\n")
        for i, instr in enumerate(response.instruments[:10], 1):
            print(f"{i}. {instr.ticker} - {instr.name}")
            print(f"   FIGI: {instr.figi}")
            print(f"   UID:  {instr.uid}")
            print(f"   Тип:  {instr.instrument_type}")
            print()

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SBER"
    try:
        asyncio.run(find_instrument_by_ticker(ticker))
    except KeyboardInterrupt:
        print("\nПоиск отменён")
    except Exception as e:
        print(f"\nОшибка: {e}")
