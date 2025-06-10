#!/usr/bin/env python3
"""
diagnose_cpu_performance.py - CPU Performance Diagnostic Tool for YOLO Detection

This script helps diagnose and optimize CPU performance for YOLO person detection
"""

import time
import torch
import cv2
import numpy as np
from ultralytics import YOLO
import psutil
import threading
import gc
from concurrent.futures import ThreadPoolExecutor

class CPUPerformanceDiagnostic:
    def __init__(self):
        self.models = {}
        self.test_results = {}
        
    def check_system_specs(self):
        """Check system specifications"""
        print("🖥️ SYSTEM SPECIFICATIONS")
        print("=" * 50)
        
        # CPU Info
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        print(f"CPU Cores (Physical): {cpu_count}")
        print(f"CPU Cores (Logical): {cpu_count_logical}")
        if cpu_freq:
            print(f"CPU Frequency: {cpu_freq.current:.0f} MHz (Max: {cpu_freq.max:.0f} MHz)")
        
        # Memory Info
        memory = psutil.virtual_memory()
        print(f"Total RAM: {memory.total / (1024**3):.1f} GB")
        print(f"Available RAM: {memory.available / (1024**3):.1f} GB")
        print(f"Memory Usage: {memory.percent}%")
        
        # PyTorch Info
        print(f"\nPyTorch Version: {torch.__version__}")
        print(f"CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
        
        print("\n" + "=" * 50)
        
        return {
            'cpu_cores': cpu_count,
            'cpu_logical': cpu_count_logical,
            'memory_gb': memory.total / (1024**3),
            'cuda_available': torch.cuda.is_available()
        }
    
    def create_test_images(self):
        """Create test images for performance testing"""
        test_images = {}
        
        # Small resolution (typical for detection)
        small_img = np.random.randint(0, 255, (320, 320, 3), dtype=np.uint8)
        test_images['320x320'] = small_img
        
        # Medium resolution
        medium_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        test_images['640x640'] = medium_img
        
        # Large resolution (typical camera feed)
        large_img = np.random.randint(0, 255, (1280, 720, 3), dtype=np.uint8)
        test_images['1280x720'] = large_img
        
        # Add a simple person-like shape for better testing
        for name, img in test_images.items():
            h, w = img.shape[:2]
            # Draw simple person shape
            cv2.rectangle(img, (w//3, h//4), (2*w//3, 3*h//4), (255, 255, 255), -1)
            cv2.circle(img, (w//2, h//5), h//10, (255, 255, 255), -1)
        
        return test_images
    
    def test_model_cpu_performance(self, model_name, test_images, num_tests=10):
        """Test model performance on CPU"""
        print(f"\n🧪 Testing {model_name} on CPU...")
        
        try:
            # Load model
            model = YOLO(model_name)
            model.to('cpu')
            model.model.eval()
            
            results = {}
            
            for img_size, test_img in test_images.items():
                print(f"  Testing resolution: {img_size}")
                
                # Warmup
                for _ in range(3):
                    with torch.no_grad():
                        _ = model.predict(
                            source=test_img,
                            verbose=False,
                            half=False,  # CPU doesn't support half precision
                            device='cpu',
                            conf=0.6,
                            classes=[0]  # Person class only
                        )
                
                # Actual test
                start_time = time.time()
                cpu_before = psutil.cpu_percent(interval=None)
                memory_before = psutil.virtual_memory().percent
                
                for _ in range(num_tests):
                    with torch.no_grad():
                        detections = model.predict(
                            source=test_img,
                            verbose=False,
                            half=False,
                            device='cpu',
                            conf=0.6,
                            classes=[0]
                        )
                
                end_time = time.time()
                cpu_after = psutil.cpu_percent(interval=0.1)
                memory_after = psutil.virtual_memory().percent
                
                avg_time = (end_time - start_time) / num_tests
                detection_count = len(detections[0].boxes) if detections[0].boxes is not None else 0
                
                results[img_size] = {
                    'avg_inference_time': avg_time * 1000,  # ms
                    'fps': 1.0 / avg_time if avg_time > 0 else 0,
                    'detections': detection_count,
                    'cpu_usage_increase': max(0, cpu_after - cpu_before),
                    'memory_usage_increase': memory_after - memory_before
                }
                
                print(f"    Inference time: {avg_time*1000:.1f}ms")
                print(f"    FPS: {1.0/avg_time:.1f}")
                print(f"    Detections: {detection_count}")
                
                # Cleanup
                gc.collect()
            
            return results
            
        except Exception as e:
            print(f"  ❌ Error testing {model_name}: {e}")
            return None
    
    def test_concurrent_cameras(self, model_name, num_cameras=4):
        """Test multiple camera simulation"""
        print(f"\n🎥 Testing {num_cameras} concurrent cameras with {model_name}...")
        
        try:
            # Create test image
            test_img = np.random.randint(0, 255, (320, 320, 3), dtype=np.uint8)
            
            # Load model
            model = YOLO(model_name)
            model.to('cpu')
            
            def simulate_camera(camera_id):
                """Simulate one camera processing"""
                times = []
                for _ in range(5):  # 5 detections per camera
                    start = time.time()
                    with torch.no_grad():
                        _ = model.predict(
                            source=test_img,
                            verbose=False,
                            half=False,
                            device='cpu',
                            conf=0.6,
                            classes=[0]
                        )
                    times.append(time.time() - start)
                    time.sleep(0.1)  # Simulate frame interval
                return camera_id, times
            
            # Monitor system resources
            cpu_before = psutil.cpu_percent(interval=None)
            memory_before = psutil.virtual_memory().percent
            
            start_time = time.time()
            
            # Run concurrent cameras
            with ThreadPoolExecutor(max_workers=num_cameras) as executor:
                futures = [executor.submit(simulate_camera, i) for i in range(num_cameras)]
                results = [future.result() for future in futures]
            
            end_time = time.time()
            cpu_after = psutil.cpu_percent(interval=0.1)
            memory_after = psutil.virtual_memory().percent
            
            # Calculate statistics
            all_times = []
            for camera_id, times in results:
                all_times.extend(times)
            
            avg_time = np.mean(all_times) * 1000
            max_time = np.max(all_times) * 1000
            total_time = end_time - start_time
            
            print(f"  Average inference time: {avg_time:.1f}ms")
            print(f"  Max inference time: {max_time:.1f}ms")
            print(f"  Total test time: {total_time:.1f}s")
            print(f"  CPU usage: {cpu_after:.1f}% (increase: {cpu_after-cpu_before:.1f}%)")
            print(f"  Memory usage: {memory_after:.1f}% (increase: {memory_after-memory_before:.1f}%)")
            
            return {
                'avg_inference_time': avg_time,
                'max_inference_time': max_time,
                'cpu_usage': cpu_after,
                'memory_usage': memory_after,
                'cpu_increase': cpu_after - cpu_before,
                'memory_increase': memory_after - memory_before
            }
            
        except Exception as e:
            print(f"  ❌ Error in concurrent test: {e}")
            return None
    
    def recommend_settings(self, system_specs, test_results):
        """Recommend optimal settings based on test results"""
        print("\n💡 OPTIMIZATION RECOMMENDATIONS")
        print("=" * 50)
        
        cpu_cores = system_specs['cpu_cores']
        memory_gb = system_specs['memory_gb']
        
        # Find best performing model
        best_model = None
        best_fps = 0
        
        for model, results in test_results.items():
            if results and '320x320' in results:
                fps = results['320x320']['fps']
                if fps > best_fps:
                    best_fps = fps
                    best_model = model
        
        print(f"🏆 Recommended Model: {best_model}")
        print(f"   Expected FPS: {best_fps:.1f}")
        
        # Camera recommendations
        if best_fps > 10:
            max_cameras = min(4, cpu_cores)
            detection_interval = 120  # 2 minutes
        elif best_fps > 5:
            max_cameras = min(2, cpu_cores // 2)
            detection_interval = 180  # 3 minutes
        else:
            max_cameras = 1
            detection_interval = 300  # 5 minutes
        
        print(f"\n📹 Camera Settings:")
        print(f"   Max concurrent cameras: {max_cameras}")
        print(f"   Detection interval: {detection_interval} seconds")
        print(f"   Recommended resolution: 320x320 for detection")
        print(f"   Process every N frames: {max(6, int(30/best_fps))}")
        
        # Memory recommendations
        if memory_gb < 8:
            print(f"\n💾 Memory Optimization (Low RAM: {memory_gb:.1f}GB):")
            print(f"   - Use smaller batch sizes")
            print(f"   - Enable aggressive garbage collection")
            print(f"   - Limit detection queue size to 2")
            print(f"   - Use JPEG quality 60-70%")
        elif memory_gb < 16:
            print(f"\n💾 Memory Optimization (Medium RAM: {memory_gb:.1f}GB):")
            print(f"   - Standard settings should work")
            print(f"   - Monitor memory usage periodically")
        else:
            print(f"\n💾 Memory Optimization (High RAM: {memory_gb:.1f}GB):")
            print(f"   - Can use higher quality settings")
            print(f"   - Support more concurrent cameras")
        
        # CPU recommendations
        if cpu_cores < 4:
            print(f"\n🖥️ CPU Optimization (Low cores: {cpu_cores}):")
            print(f"   - Single camera only")
            print(f"   - Process every 8-10 frames")
            print(f"   - Use lowest resolution (320x320)")
        elif cpu_cores < 8:
            print(f"\n🖥️ CPU Optimization (Medium cores: {cpu_cores}):")
            print(f"   - 2-3 cameras maximum")
            print(f"   - Process every 6 frames")
            print(f"   - Balance quality vs performance")
        else:
            print(f"\n🖥️ CPU Optimization (High cores: {cpu_cores}):")
            print(f"   - Can handle 4+ cameras")
            print(f"   - Process every 4-6 frames")
            print(f"   - Higher quality settings possible")
        
        # Generate config
        config = {
            'recommended_model': best_model,
            'max_cameras': max_cameras,
            'detection_interval': detection_interval,
            'process_every_n_frames': max(6, int(30/best_fps)),
            'detection_resolution': 320,
            'confidence_threshold': 0.65,
            'jpeg_quality': 70 if memory_gb < 8 else 80,
            'queue_size': 2 if memory_gb < 8 else 3
        }
        
        print(f"\n⚙️ Generated Configuration:")
        for key, value in config.items():
            print(f"   {key}: {value}")
        
        return config
    
    def save_config_file(self, config, filename="optimized_config.py"):
        """Save configuration to file"""
        config_content = f'''# Auto-generated optimized configuration
# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}

# Model Configuration
RECOMMENDED_MODEL = "{config['recommended_model']}"

# Camera Settings
MAX_CONCURRENT_CAMERAS = {config['max_cameras']}
DETECTION_INTERVAL = {config['detection_interval']}  # seconds
PROCESS_EVERY_N_FRAMES = {config['process_every_n_frames']}

# Detection Settings
DETECTION_RESOLUTION = {config['detection_resolution']}  # pixels
CONFIDENCE_THRESHOLD = {config['confidence_threshold']}
JPEG_QUALITY = {config['jpeg_quality']}
DETECTION_QUEUE_SIZE = {config['queue_size']}

# Additional CPU Optimizations
USE_HALF_PRECISION = False  # Always False for CPU
ENABLE_GARBAGE_COLLECTION = True
PERIODIC_CLEANUP_INTERVAL = 600  # seconds

# Flask Settings
FLASK_THREADED = True
FLASK_DEBUG = False
API_TIMEOUT = 5  # seconds
MAX_CONCURRENT_REQUESTS = 2

# Telegram Settings (adjust based on performance)
NOTIFICATION_COOLDOWN = 60  # seconds
MAX_NOTIFICATIONS_PER_HOUR = 20

print("🚀 Optimized configuration loaded!")
print(f"📊 Expected performance: ~{1000/({config['process_every_n_frames']} * 33.33):.1f} detections/second per camera")
'''
        
        with open(filename, 'w') as f:
            f.write(config_content)
        
        print(f"\n💾 Configuration saved to: {filename}")
        return filename
    
    def run_full_diagnostic(self):
        """Run complete diagnostic"""
        print("🔍 NT TELECOM CPU PERFORMANCE DIAGNOSTIC")
        print("=" * 60)
        
        # Check system
        system_specs = self.check_system_specs()
        
        # Create test images
        test_images = self.create_test_images()
        print(f"\n📸 Created test images: {list(test_images.keys())}")
        
        # Test models
        models_to_test = ["yolov8n.pt", "yolov5n.pt", "yolov5s.pt"]
        test_results = {}
        
        for model_name in models_to_test:
            try:
                results = self.test_model_cpu_performance(model_name, test_images)
                if results:
                    test_results[model_name] = results
            except Exception as e:
                print(f"❌ Failed to test {model_name}: {e}")
        
        if not test_results:
            print("❌ No models could be tested successfully!")
            return
        
        # Test concurrent performance
        best_model = max(test_results.keys(), 
                        key=lambda x: test_results[x]['320x320']['fps'] if '320x320' in test_results[x] else 0)
        
        concurrent_results = self.test_concurrent_cameras(best_model, 4)
        
        # Generate recommendations
        config = self.recommend_settings(system_specs, test_results)
        
        # Save configuration
        config_file = self.save_config_file(config)
        
        # Final summary
        print("\n" + "=" * 60)
        print("📋 DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        print(f"✅ System CPU cores: {system_specs['cpu_cores']}")
        print(f"✅ System RAM: {system_specs['memory_gb']:.1f}GB")
        print(f"✅ Best model: {config['recommended_model']}")
        print(f"✅ Max cameras: {config['max_cameras']}")
        print(f"✅ Expected CPU usage: ~{concurrent_results['cpu_usage']:.0f}% with {config['max_cameras']} cameras")
        
        if concurrent_results and concurrent_results['cpu_usage'] > 85:
            print("⚠️  WARNING: High CPU usage detected!")
            print("   Consider reducing number of cameras or detection frequency")
        elif concurrent_results and concurrent_results['cpu_usage'] < 60:
            print("✅ Good CPU performance - system can handle the load")
        
        print(f"\n📁 Configuration saved to: {config_file}")
        print("🔧 Apply this configuration to your camera.py and app.py files")
        
        return config

def main():
    """Main diagnostic function"""
    diagnostic = CPUPerformanceDiagnostic()
    
    try:
        config = diagnostic.run_full_diagnostic()
        
        print("\n🎯 NEXT STEPS:")
        print("1. Apply the generated configuration to your code")
        print("2. Test with one camera first")
        print("3. Gradually add more cameras while monitoring CPU")
        print("4. Adjust settings based on real-world performance")
        
        return config
        
    except KeyboardInterrupt:
        print("\n🛑 Diagnostic interrupted by user")
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        print("Check your YOLO installation and try again")

if __name__ == "__main__":
    main()