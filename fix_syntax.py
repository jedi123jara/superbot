with open('bot.py', encoding='utf-8') as f:
    content = f.read()

fixes = [
    # Fix 1: Comilla extra antes del primer comentario (SyntaxError critico)
    ('    " # Los 10 Titanes (Indispensables)', '    # Los 10 Titanes (Indispensables)'),
    # Fix 2: 'Cloud' no es un ticker valido
    ('"SNOW", "PLTR", "Cloud",', '"SNOW", "PLTR",'),
    # Fix 3-11: Commas faltantes al final de cada seccion
    ('"ARKK"\n # Industriales',          '"ARKK",\n    # Industriales'),
    ('"TMO", "A"\n # Bienes',            '"TMO", "A",\n    # Bienes'),
    ('"CCS", "WLK"\n# Lujo',             '"CCS", "WLK",\n    # Lujo'),
    ('"SONY"  # Biotecnolog\u00eda',         '"SONY",\n    # Biotecnolog\u00eda'),
    ('"LAC", "MP"  # Infraestructura',   '"LAC", "MP",\n    # Infraestructura'),
    ('"KDP", "STZ"\n # Software',        '"KDP", "STZ",\n    # Software'),
    ('"SEM", "EHC"\n   # Energ\u00eda',     '"SEM", "EHC",\n    # Energ\u00eda'),
    ('"GLW", "STX"   \n # Defensa',      '"GLW", "STX",\n    # Defensa'),
    ('"MSI", "TEL"\n# Especialidades',   '"MSI", "TEL",\n    # Especialidades'),
]

for old, new in fixes:
    if old in content:
        content = content.replace(old, new)
        print(f"Fixed: {repr(old[:40])}")
    else:
        print(f"NOT FOUND: {repr(old[:40])}")

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone. Verifying syntax...")
import ast
try:
    ast.parse(content)
    print("Syntax OK!")
except SyntaxError as e:
    print(f"Still has error: {e}")
