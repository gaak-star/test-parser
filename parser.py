#!/usr/bin/env python3
import re
import argparse
import sys
from collections import defaultdict

# Регулярное выражение для парсинга стандартного лога PostgreSQL
# Захватываем дату, пользователя, БД, время выполнения и сам запрос
LOG_PATTERN = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?'
    r'user=(?P<user>[^,]+),db=(?P<db>[^\s]+)\s+LOG:\s+'
    r'duration:\s+(?P<duration>\d+\.\d+)\s+ms\s+'
    r'statement:\s+(?P<query>.+)'
)

def parse_logs(file_path, threshold_ms):
    """
    Читает лог-файл и возвращает список словарей с медленными запросами.
    """
    slow_queries = []
    total_queries = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                total_queries += 1
                match = LOG_PATTERN.search(line)
                if match:
                    data = match.groupdict()
                    duration = float(data['duration'])
                    
                    if duration >= threshold_ms:
                        slow_queries.append({
                            'time': data['timestamp'],
                            'user': data['user'],
                            'db': data['db'],
                            'duration': duration,
                            'query': data['query'].strip()
                        })
    except FileNotFoundError:
        print(f"[-] Ошибка: Файл {file_path} не найден.", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"[-] Ошибка: Нет прав на чтение файла {file_path}.", file=sys.stderr)
        sys.exit(1)
        
    return slow_queries, total_queries

def generate_report(slow_queries, total_queries, threshold_ms):
    """
    Генерирует текстовый отчет в консоли.
    """
    print("=" * 60)
    print(" ОТЧЕТ: Анализ медленных запросов PostgreSQL")
    print("=" * 60)
    print(f"Всего строк в логе: {total_queries}")
    print(f"Порог медленного запроса: {threshold_ms} ms")
    print(f"Найдено медленных запросов: {len(slow_queries)}\n")

    if not slow_queries:
        print("[+] Отлично! Медленных запросов не найдено.")
        return

    # Сортируем по длительности (от самых долгих)
    slow_queries.sort(key=lambda x: x['duration'], reverse=True)

    # Группируем по БД для статистики
    db_stats = defaultdict(int)
    for q in slow_queries:
        db_stats[q['db']] += 1

    print("--- Статистика по базам данных ---")
    for db, count in db_stats.items():
        print(f"  {db}: {count} медленных запросов")
    print("\n--- Топ медленных запросов ---")

    for i, q in enumerate(slow_queries, 1):
        print(f"\n{i}. Время: {q['duration']} ms | БД: {q['db']} | Юзер: {q['user']}")
        print(f"   Дата: {q['time']}")
        # Обрезаем слишком длинные запросы для читаемости
        query_display = q['query'] if len(q['query']) < 100 else q['query'][:100] + "..."
        print(f"   SQL:  {query_display}")

    print("\n" + "=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Парсер логов PostgreSQL для поиска медленных запросов.")
    parser.add_argument("logfile", help="Путь к файлу лога PostgreSQL")
    parser.add_argument(
        "-t", "--threshold", 
        type=float, 
        default=100.0, 
        help="Порог медленного запроса в миллисекундах (по умолчанию: 100)"
    )
    
    args = parser.parse_args()

    print(f"[*] Читаю лог-файл: {args.logfile}...")
    slow_queries, total = parse_logs(args.logfile, args.threshold)
    generate_report(slow_queries, total, args.threshold)

if __name__ == "__main__":
    main()