import os
import re

def fix_file(path):
    with open(path, 'r') as f:
        content = f.read()

    # The error was caused by replacing `</` with `<Icon/`.
    content = content.replace('<Icon/', '</')

    with open(path, 'w') as f:
        f.write(content)

for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.tsx'):
            fix_file(os.path.join(root, file))

print("Syntax errors fixed!")
