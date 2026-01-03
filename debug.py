# debug.py
import os

print("--- DIAGNOSTIC REPORT ---")

# 1. Where are we right now?
current_dir = os.getcwd()
print(f"Current Working Directory: {current_dir}")

# 2. What files are in the main folder?
print("\nFiles in 'QuantCore':")
try:
    files = os.listdir(current_dir)
    for f in files:
        print(f" - {f}")
except Exception as e:
    print(f"Error reading directory: {e}")

# 3. What is inside the 'src' folder?
print("\nFiles in 'QuantCore/src':")
src_path = os.path.join(current_dir, "src")
if os.path.exists(src_path):
    try:
        src_files = os.listdir(src_path)
        for f in src_files:
            print(f" - {f}")
    except Exception as e:
        print(f"Error reading src folder: {e}")
else:
    print("CRITICAL: 'src' folder does NOT exist!")

print("-------------------------")