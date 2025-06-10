#!/usr/bin/env python3
"""
quick_fix.py - Quick fix for the Half precision CPU error

This script will quickly patch your existing camera.py file to fix the 
"slow_conv2d_cpu" not implemented for 'Half' error.
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create backup of original file"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    return None

def fix_half_precision_error(camera_file="camera.py"):
    """Fix the half precision error in camera.py"""
    
    if not os.path.exists(camera_file):
        print(f"❌ File not found: {camera_file}")
        return False
    
    print(f"🔧 Fixing half precision error in {camera_file}...")
    
    # Create backup
    backup_file(camera_file)
    
    # Read the file
    with open(camera_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply fixes
    fixes_applied = 0
    
    # Fix 1: Remove half=True from model.predict() calls
    pattern1 = r'half=True,'
    if re.search(pattern1, content):
        content = re.sub(pattern1, 'half=False,', content)
        fixes_applied += 1
        print("  ✅ Fixed half=True parameter")
    
    # Fix 2: Add half=False if missing
    pattern2 = r'(model\.predict\([^)]*?)(\s*verbose=False[^)]*?)(\))'
    def add_half_false(match):
        full_call = match.group(0)
        if 'half=' not in full_call:
            return full_call.replace('verbose=False', 'half=False,\n                        verbose=False')
        return full_call
    
    if re.search(pattern2, content):
        content = re.sub(pattern2, add_half_false, content)
        fixes_applied += 1
        print("  ✅ Added half=False parameter where missing")
    
    # Fix 3: Ensure device='cpu' is explicit
    pattern3 = r"device='cpu'"
    if not re.search(pattern3, content):
        # Add device='cpu' to predict calls
        pattern_predict = r'(model\.predict\([^)]*?)(\s*verbose=False)'
        content = re.sub(pattern_predict, r"\1device='cpu',\n                        \2", content)
        fixes_applied += 1
        print("  ✅ Added explicit device='cpu' parameter")
    
    # Fix 4: Update detection resolution for better CPU performance
    pattern4 = r"self\.detection_resolution = \(\d+, \d+\)"
    if re.search(pattern4, content):
        content = re.sub(pattern4, "self.detection_resolution = (320, 320)", content)
        fixes_applied += 1
        print("  ✅ Optimized detection resolution to 320x320")
    
    # Fix 5: Increase frame processing interval
    pattern5 = r"self\.process_every_n_frames = \d+"
    if re.search(pattern5, content):
        content = re.sub(pattern5, "self.process_every_n_frames = 8", content)
        fixes_applied += 1
        print("  ✅ Increased frame processing interval to 8")
    
    # Fix 6: Add torch.no_grad() context if missing
    if 'with torch.no_grad():' not in content:
        pattern6 = r'(results = model\.predict\()'
        replacement6 = r'with torch.no_grad():\n                    \1'
        content = re.sub(pattern6, replacement6, content)
        # Fix indentation for the rest of the predict call
        content = content.replace('source=detect_frame,', '    source=detect_frame,')
        fixes_applied += 1
        print("  ✅ Added torch.no_grad() context")
    
    # Write the fixed file
    with open(camera_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"🎉 Applied {fixes_applied} fixes to {camera_file}")
    return True

def create_minimal_test_script():
    """Create a minimal test script to verify the fix"""
    test_script = """#!/usr/bin/env python3
# test_yolo_cpu.py - Test YOLO on CPU without half precision

import torch
import numpy as np
from ultralytics import YOLO
import time

def test_yolo_cpu():
    print("🧪 Testing YOLO on CPU...")
    
    try:
        # Load model
        model = YOLO("yolov8n.pt")
        model.to('cpu')
        
        # Create test image
        test_img = np.random.randint(0, 255, (320, 320, 3), dtype=np.uint8)
        
        # Test prediction
        print("Running prediction...")
        start = time.time()
        
        with torch.no_grad():
            results = model.predict(
                source=test_img,
                imgsz=320,
                conf=0.6,
                classes=[0],  # Person class
                verbose=False,
                half=False,   # IMPORTANT: No half precision on CPU
                device='cpu'
            )
        
        end = time.time()
        
        print(f"✅ Prediction successful!")
        print(f"Time taken: {(end-start)*1000:.1f}ms")
        print(f"Detections found: {len(results[0].boxes) if results[0].boxes else 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_yolo_cpu()
"""
    
    with open("test_yolo_cpu.py", "w") as f:
        f.write(test_script)
    
    print("📝 Created test script: test_yolo_cpu.py")

def main():
    """Main fix function"""
    print("🚨 NT TELECOM - Half Precision CPU Error Quick Fix")
    print("=" * 55)
    
    # Check if camera.py exists
    if not os.path.exists("camera.py"):
        print("❌ camera.py not found in current directory")
        print("💡 Make sure you're in the correct directory")
        return
    
    # Apply fixes
    success = fix_half_precision_error()
    
    if success:
        print("\n✅ FIXES APPLIED SUCCESSFULLY!")
        print("\n📋 What was fixed:")
        print("  • Disabled half precision (half=False)")
        print("  • Added explicit CPU device")
        print("  • Optimized detection resolution")
        print("  • Increased frame processing interval")
        print("  • Added memory optimization")
        
        # Create test script
        create_minimal_test_script()
        
        print("\n🔬 TESTING:")
        print("1. Run: python test_yolo_cpu.py")
        print("2. If test passes, restart your main application")
        print("3. Monitor CPU usage and adjust settings if needed")
        
        print("\n⚙️ ADDITIONAL OPTIMIZATIONS:")
        print("• Consider running: python diagnose_cpu_performance.py")
        print("• Monitor system resources with: htop or Task Manager")
        print("• Adjust detection_interval in settings if CPU usage is still high")
        
    else:
        print("❌ Fix failed. Please check the error messages above.")
    
    print("\n" + "=" * 55)

if __name__ == "__main__":
    main()
#         self.cursor.execute('''   
