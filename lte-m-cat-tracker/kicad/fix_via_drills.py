"""Fix all undersized via drills to JLCPCB minimum 0.3mm (pad 0.6mm)."""
import re, shutil, os

PCB = "kicad/lte-m-cat-tracker.kicad_pcb"
shutil.copy(PCB, PCB + ".bak_via_drills")

with open(PCB) as f:
    content = f.read()

def fix_via(m):
    at    = m.group(1)
    size  = float(m.group(2))
    drill = float(m.group(3))
    rest  = m.group(4)

    if drill < 0.3:
        new_drill = 0.3
        # Maintain annular ring: pad = drill + 0.3mm minimum
        new_size = max(size, new_drill + 0.3)
        # Round to 2 decimal places
        new_size = round(new_size, 2)
        return f"(via\n\t\t(at {at})\n\t\t(size {new_size})\n\t\t(drill {new_drill}){rest}"
    return m.group(0)

pattern = re.compile(
    r'\(via\s*\n\s*\(at ([^)]+)\)\s*\n\s*\(size ([\d.]+)\)\s*\n\s*\(drill ([\d.]+)\)(.*?)\)',
    re.DOTALL
)

new_content = pattern.sub(fix_via, content)

changed = sum(1 for a, b in zip(content.split('\n'), new_content.split('\n')) if a != b)
print(f"Lines changed: {changed}")

with open(PCB, 'w') as f:
    f.write(new_content)

# Verify
matches = pattern.findall(new_content)
from collections import Counter
drills = Counter(float(m[2]) for m in matches)
print("Drill sizes after fix:", dict(drills))
