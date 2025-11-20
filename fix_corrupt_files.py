import os

# File yang corrupt dan perlu di-recreate
corrupt_files = [
    r"backend\src\app\api\v1\chat.py",
    r"backend\src\app\crud\crud_chat.py", 
    r"backend\src\app\models\chat.py",
    r"backend\src\app\schemas\chat.py"
]

for file_path in corrupt_files:
    try:
        # Try to remove if exists
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✓ Removed: {file_path}")
    except Exception as e:
        print(f"✗ Error removing {file_path}: {e}")
    
    try:
        # Recreate with placeholder content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Placeholder - file was corrupted\n")
        print(f"✓ Recreated: {file_path}")
    except Exception as e:
        print(f"✗ Error creating {file_path}: {e}")

print("\n✓ Done! Now you can remove these files with: git rm backend/src/app/api/v1/chat.py etc.")
