import os

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "truth-seeker-suite"))

files = [
    "src/lib/api-client.ts",
    "src/lib/auth-context.tsx",
    "src/lib/cashfree.ts",
    "src/components/AuthDialog.tsx",
    "src/components/Navbar.tsx",
    "src/routes/__root.tsx",
    "src/routes/index.tsx"
]

for rel_path in files:
    full_path = os.path.join(frontend_dir, rel_path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"=== {rel_path} (len: {len(content)}) ===")
        # check for potential corrupted lines or syntax
        first_few = content[:200].replace("\n", " \\n ")
        print(f"Preview: {first_few}")
    else:
        print(f"MISSING: {rel_path}")
