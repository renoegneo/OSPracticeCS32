#!/usr/bin/env python3
"""ПР-2, вариант B: читает файл и печатает его размер в байтах."""
import sys

if len(sys.argv) != 2:
    print(f"Использование: {sys.argv[0]} <файл>", file=sys.stderr)
    sys.exit(1)

path = sys.argv[1]
with open(path, "rb") as f:      # "rb" = читаем сырые байты, без декодирования
    data = f.read()              # читаем файл целиком
print(f"{path}: {len(data)} байт")
