import os

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "truth-seeker-suite"))
print(f"Frontend dir: {frontend_dir}")
print(f"Exists: {os.path.exists(frontend_dir)}")

# Check playground.tsx
pg_path = os.path.join(frontend_dir, "src", "routes", "playground.tsx")
if os.path.exists(pg_path):
    with open(pg_path, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"playground.tsx length: {len(content)}")
    print("playground.tsx sample lines 30-60:")
    lines = content.splitlines()
    for i, line in enumerate(lines[25:65], start=26):
        print(f"{i}: {line}")
