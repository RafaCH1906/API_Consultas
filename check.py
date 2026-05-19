import os
import time

filepath = "padron_reducido_ruc.txt"
found = False

print(f"Buscando '10608190363' en {filepath}...")
with open(filepath, 'r', encoding='ISO-8859-1') as f:
    for i, line in enumerate(f):
        if "10608190363" in line:
            print(f"ENCONTRADO en línea {i}:", line.strip())
            found = True
            break

