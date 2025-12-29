#!/usr/bin/env python3
"""
Скрипт для создания монолитного бэкапа всего кода проекта.
Собирает все файлы, игнорируя всё, что указано в .gitignore.
Результат: единый текстовый файл с сохранением структуры проекта.
"""

import os
import sys
import fnmatch
from pathlib import Path
from datetime import datetime

def load_gitignore_patterns(project_root):
    """Загружает и парсит шаблоны из .gitignore"""
    gitignore_path = project_root / '.gitignore'
    patterns = []
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue
                
                # Преобразуем шаблоны .gitignore в fnmatch
                pattern = line
                if pattern.startswith('/'):
                    pattern = pattern[1:]
                if pattern.endswith('/'):
                    pattern = pattern[:-1]
                
                patterns.append(pattern)
    
    # Добавляем стандартные игнорируемые папки Python
    default_patterns = [
        '__pycache__', '*.pyc', '*.pyo', '*.pyd',
        '.Python', 'pip-log.txt', 'pip-delete-this-directory.txt',
        'htmlcov', '.tox', '.nox', '.coverage', '.cache',
        '.pytest_cache', '.hypothesis',
        '.env', '.venv', 'venv/', 'env/', 'ENV/', 
        '.vscode', '.idea', '*.swp', '*.swo',
        '.DS_Store', 'Thumbs.db'
    ]
    
    patterns.extend(default_patterns)
    return patterns

def should_ignore(path, patterns, project_root):
    """Проверяет, должен ли файл/директория быть проигнорирован"""
    rel_path = str(path.relative_to(project_root))
    
    for pattern in patterns:
        # Проверка на точное совпадение директории
        if pattern in rel_path.split(os.sep):
            return True
        
        # Проверка с использованием fnmatch
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path, f'*/{pattern}'):
            return True
        
        # Проверка для директорий
        if pattern.endswith('*'):
            if rel_path.startswith(pattern[:-1]):
                return True
    
    # Игнорируем саму папку с бэкапом
    if 'code_backup_' in rel_path:
        return True
    
    return False

def is_text_file(filepath):
    """Пытается определить, является ли файл текстовым"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except:
        return False

def create_backup(project_root):
    """Основная функция создания бэкапа"""
    print(f"Создание бэкапа проекта: {project_root}")
    
    # Загружаем шаблоны из .gitignore
    patterns = load_gitignore_patterns(project_root)
    print(f"Загружено {len(patterns)} шаблонов исключения")
    
    # Создаем имя файла бэкапа с временной меткой
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = project_root / f'code_backup_{timestamp}.txt'
    
    # Собираем все файлы проекта
    all_files = []
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        
        # Фильтруем директории
        dirs[:] = [d for d in dirs if not should_ignore(root_path / d, patterns, project_root)]
        
        # Фильтруем файлы
        for file in files:
            file_path = root_path / file
            if not should_ignore(file_path, patterns, project_root) and is_text_file(file_path):
                all_files.append(file_path)
    
    print(f"Найдено {len(all_files)} файлов для включения в бэкап")
    
    # Сортируем файлы по пути для последовательного вывода
    all_files.sort()
    
    # Записываем все в единый файл
    with open(backup_filename, 'w', encoding='utf-8') as backup_file:
        # Заголовок
        backup_file.write(f"=== МОНТИРОВАННЫЙ БЭКАП ПРОЕКТА ===\n")
        backup_file.write(f"Проект: {project_root.name}\n")
        backup_file.write(f"Время создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        backup_file.write(f"Всего файлов: {len(all_files)}\n")
        backup_file.write("=" * 60 + "\n\n")
        
        # Записываем каждый файл
        for i, file_path in enumerate(all_files, 1):
            rel_path = file_path.relative_to(project_root)
            
            # Разделитель файла
            backup_file.write(f"\n{'=' * 80}\n")
            backup_file.write(f"ФАЙЛ {i}: {rel_path}\n")
            backup_file.write(f"{'=' * 80}\n\n")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Добавляем содержимое файла
                backup_file.write(content)
                
                # Добавляем пустую строку в конце файла, если её нет
                if content and not content.endswith('\n'):
                    backup_file.write('\n')
                    
            except Exception as e:
                backup_file.write(f"[ОШИБКА ЧТЕНИЯ ФАЙЛА: {e}]\n")
    
    print(f"Бэкап успешно создан: {backup_filename}")
    print(f"Размер файла: {backup_filename.stat().st_size / 1024:.2f} KB")
    
    # Показываем структуру проекта в конце
    with open(backup_filename, 'a', encoding='utf-8') as backup_file:
        backup_file.write(f"\n\n{'=' * 80}\n")
        backup_file.write("СТРУКТУРА ПРОЕКТА:\n")
        backup_file.write(f"{'=' * 80}\n\n")
        
        for root, dirs, files in os.walk(project_root):
            root_path = Path(root)
            if should_ignore(root_path, patterns, project_root):
                continue
                
            level = len(root_path.relative_to(project_root).parts)
            indent = "  " * level
            backup_file.write(f"{indent}{root_path.name}/\n")
            
            subindent = "  " * (level + 1)
            for file in files:
                file_path = root_path / file
                if not should_ignore(file_path, patterns, project_root):
                    backup_file.write(f"{subindent}{file}\n")
    
    return backup_filename

def main():
    """Точка входа скрипта"""
    try:
        # Определяем корень проекта (где лежит этот скрипт)
        project_root = Path(__file__).parent
        
        print("=" * 60)
        print("СКРИПТ СОЗДАНИЯ МОНОЛИТНОГО БЭКАПА ПРОЕКТА")
        print("=" * 60)
        
        # Создаем бэкап
        backup_file = create_backup(project_root)
        
        print("\n" + "=" * 60)
        print(f"БЭКАП УСПЕШНО СОЗДАН!")
        print(f"Файл: {backup_file}")
        print("=" * 60)
        
        # Краткая инструкция
        print("\nИнструкция:")
        print("1. Этот файл содержит ВЕСЬ код проекта в читаемом виде")
        print("2. Каждый файл отделен разделителями")
        print("3. Игнорируются файлы из .gitignore и бинарные файлы")
        print("4. Можно отправлять этот файл для анализа кода")
        
    except Exception as e:
        print(f"Ошибка при создании бэкапа: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
