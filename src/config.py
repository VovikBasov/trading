"""
Конфигурация для Tinkoff Invest API.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class TinkoffConfig:
    """Базовый класс конфигурации Tinkoff Invest API"""
    
    @property
    def api_token(self) -> str:
        """Токен API Tinkoff Invest"""
        token = os.getenv('TINKOFF_API_TOKEN')
        if not token:
            raise ValueError(
                "TINKOFF_API_TOKEN не найден в переменных окружения. "
                "Добавьте его в файл .env"
            )
        return token
    
    @property
    def use_sandbox(self) -> bool:
        """Использовать песочницу для тестирования"""
        sandbox_value = os.getenv('USE_SANDBOX', 'false').lower()
        # Преобразуем строку в булево значение
        return sandbox_value in ('true', '1', 'yes', 'y')
    
    @property
    def app_name(self) -> str:
        """Имя приложения для идентификации в API"""
        return os.getenv('APP_NAME', 'tinvest-bot')

# Создаем глобальный экземпляр конфигурации
config = TinkoffConfig()

# Вывод текущих настроек для отладки
if __name__ == "__main__":
    print(f"Токен загружен: {'*' * min(10, len(config.api_token))}...")
    print(f"Режим песочницы: {config.use_sandbox}")
    print(f"Имя приложения: {config.app_name}")
