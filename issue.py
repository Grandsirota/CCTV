#!/usr/bin/env python3
"""
debug_camera_issues.py - Debug camera display and streaming issues

This script helps diagnose why some cameras show black screens or don't display properly
"""

import cv2
import requests
import time
import threading
import subprocess
from datetime import datetime
import os

class CameraDebugger:
    def __init__(self):
        # RTSP camera URLs (update with your actual URLs)
        self.rtsp_cameras = {
            "Front Gate Camera": "rtsp://rsrc2:rsrc1234@7dd608e038a9.sn.mynetname.net/chID=9&streamType=sub",
            "Main Entrance": "rtsp://rsrc2:rsrc1234@7dd608e038a9.sn.mynetname.net/chID=2&streamType=sub", 
            "Parking Area": "rtsp://rsrc2:rsrc1234@608905d16e93.sn.mynetname.net/chID=1&streamType=sub",
            "Lobby Camera": "rtsp://rsrc2:rsrc1234@608905d16e93.sn.mynetname.net/chID=2&streamType=sub"
        }
        
        self.flask_url = "http://127.0.0.1:5000"
        self.results = {}
    
    def test_rtsp_connection(self, camera_name, rtsp_url, timeout=10):
        """Test direct RTSP connection"""
        print(f"\n🔍 Testing RTSP connection: {camera_name}")
        print(f"URL: {rtsp_url}")
        
        try:
            # Test with OpenCV
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_TIMEOUT, timeout * 1000)  # ms
            
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                
                if ret and frame is not None:
                    print(f"✅ {camera_name}: Connection successful, frame captured")
                    return True, "Connection OK"
                else:
                    print(f"❌ {camera_name}: Connected but no frame received")
                    return False, "No frame"
            else:
                print(f"❌ {camera_name}: Cannot open RTSP stream")
                return False, "Cannot open"
                
        except Exception as e:
            print(f"❌ {camera_name}: Error - {e}")
            return False, str(e)
    
    def test_ffmpeg_connection(self, camera_name, rtsp_url):
        """Test RTSP with FFmpeg"""
        print(f"\n🎬 Testing FFmpeg connection: {camera_name}")
        
        try:
            cmd = [
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-i', rtsp_url,
                '-t', '3',  # 3 seconds test
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print(f"✅ {camera_name}: FFmpeg connection successful")
                return True, "FFmpeg OK"
            else:
                print(f"❌ {camera_name}: FFmpeg failed")
                print(f"Error: {result.stderr}")
                return False, "FFmpeg failed"
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {camera_name}: FFmpeg timeout")
            return False, "Timeout"
        except Exception as e:
            print(f"❌ {camera_name}: FFmpeg error - {e}")
            return False, str(e)
    
    def test_flask_endpoints(self):
        """Test Flask video feed endpoints"""
        print(f"\n🌐 Testing Flask endpoints...")
        
        endpoints = [
            "/",
            "/get_system_stats",
            "/get_all_detections"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.flask_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {endpoint}: OK")
                else:
                    print(f"❌ {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint}: Error - {e}")
    
    def test_video_feed_endpoints(self):
        """Test video feed endpoints for each camera"""
        print(f"\n📹 Testing video feed endpoints...")
        
        for camera_name in self.rtsp_cameras.keys():
            try:
                url = f"{self.flask_url}/video_feed?camera_id={camera_name}"
                
                # Test with HEAD request first
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ {camera_name}: Video feed endpoint responding")
                else:
                    print(f"❌ {camera_name}: Video feed HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {camera_name}: Video feed error - {e}")
    
    def check_javascript_errors(self):
        """Check for common JavaScript issues"""
        print(f"\n📝 Checking JavaScript/Frontend issues...")
        
        # Check if main.js exists
        js_files = [
            "static/js/main.js",
            "templates/index.html"
        ]
        
        for file_path in js_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path}: File exists")
                
                # Check file size
                size = os.path.getsize(file_path)
                if size > 0:
                    print(f"   File size: {size} bytes")
                else:
                    print(f"❌ {file_path}: File is empty!")
            else:
                print(f"❌ {file_path}: File not found!")
    
    def test_camera_switching(self):
        """Test camera switching API"""
        print(f"\n🔄 Testing camera switching...")
        
        for camera_name in self.rtsp_cameras.keys():
            try:
                url = f"{self.flask_url}/switch_camera/{camera_name}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        print(f"✅ {camera_name}: Switch successful")
                    else:
                        print(f"❌ {camera_name}: Switch failed - {data}")
                else:
                    print(f"❌ {camera_name}: Switch HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {camera_name}: Switch error - {e}")
    
    def check_network_connectivity(self):
        """Check network connectivity to camera IPs"""
        print(f"\n🌐 Testing network connectivity...")
        
        # Extract IPs from RTSP URLs
        camera_ips = set()
        for url in self.rtsp_cameras.values():
            try:
                # Extract IP from RTSP URL
                ip_part = url.split('@')[1].split('.sn.mynetname.net')[0]
                if ip_part:
                    camera_ips.add(f"{ip_part}.sn.mynetname.net")
            except:
                pass
        
        for ip in camera_ips:
            try:
                # Test ping
                result = subprocess.run(['ping', '-c', '1', '-W', '3', ip], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ {ip}: Ping successful")
                else:
                    print(f"❌ {ip}: Ping failed")
                    
            except Exception as e:
                print(f"❌ {ip}: Ping error - {e}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print(f"\n📊 CAMERA DIAGNOSTIC REPORT")
        print(f"=" * 50)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"=" * 50)
        
        # Test network connectivity
        self.check_network_connectivity()
        
        # Test RTSP connections
        rtsp_results = {}
        for camera_name, rtsp_url in self.rtsp_cameras.items():
            success, message = self.test_rtsp_connection(camera_name, rtsp_url)
            rtsp_results[camera_name] = {'rtsp': success, 'message': message}
            
            # Also test with FFmpeg
            ff_success, ff_message = self.test_ffmpeg_connection(camera_name, rtsp_url)
            rtsp_results[camera_name]['ffmpeg'] = ff_success
            rtsp_results[camera_name]['ffmpeg_message'] = ff_message
        
        # Test Flask endpoints
        self.test_flask_endpoints()
        self.test_video_feed_endpoints()
        self.test_camera_switching()
        self.check_javascript_errors()
        
        # Summary
        print(f"\n📋 SUMMARY")
        print(f"=" * 30)
        
        working_cameras = []
        problem_cameras = []
        
        for camera_name, results in rtsp_results.items():
            if results['rtsp'] and results['ffmpeg']:
                working_cameras.append(camera_name)
                print(f"✅ {camera_name}: Working")
            else:
                problem_cameras.append(camera_name)
                print(f"❌ {camera_name}: Issues detected")
                print(f"   RTSP: {results['message']}")
                print(f"   FFmpeg: {results['ffmpeg_message']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print(f"=" * 30)
        
        if problem_cameras:
            print(f"🔧 Cameras with issues: {', '.join(problem_cameras)}")
            print(f"📝 Suggested fixes:")
            print(f"   1. Check RTSP URL credentials")
            print(f"   2. Verify camera is online and accessible")
            print(f"   3. Check network connectivity")
            print(f"   4. Try using main stream instead of sub stream")
            print(f"   5. Restart camera system or cameras")
            
            # Generate fixed URLs
            print(f"\n🔄 Try these alternative URLs:")
            for camera_name in problem_cameras:
                original_url = self.rtsp_cameras[camera_name]
                # Try main stream
                main_url = original_url.replace('streamType=sub', 'streamType=main')
                print(f"   {camera_name}: {main_url}")
        
        if working_cameras:
            print(f"✅ Working cameras: {', '.join(working_cameras)}")
        
        # JavaScript check
        print(f"\n🔍 Frontend issues check:")
        print(f"   1. Open browser Developer Tools (F12)")
        print(f"   2. Check Console tab for JavaScript errors")
        print(f"   3. Check Network tab for failed requests")
        print(f"   4. Verify video_feed requests are successful")
        
        return rtsp_results
    
    def create_fix_script(self, problem_cameras):
        """Create automatic fix script"""
        fix_script = f'''#!/bin/bash
# auto_fix_cameras.sh - Automatic camera fix script
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🔧 NT Telecom Camera Fix Script"
echo "==============================="

# Check if Flask app is running
if ! curl -s http://127.0.0.1:5000 > /dev/null; then
    echo "❌ Flask app is not running!"
    echo "Start with: python app.py"
    exit 1
fi

echo "✅ Flask app is running"

# Test each problematic camera
'''
        
        for camera_name in problem_cameras:
            camera_safe = camera_name.replace(' ', '_')
            fix_script += f'''
echo "🔍 Testing {camera_name}..."
curl -s "http://127.0.0.1:5000/switch_camera/{camera_name}" | grep -q "success"
if [ $? -eq 0 ]; then
    echo "✅ {camera_name}: Switch successful"
else
    echo "❌ {camera_name}: Switch failed"
fi
'''
        
        fix_script += '''
echo "🎯 If issues persist:"
echo "1. Check camera power and network"
echo "2. Verify RTSP credentials"
echo "3. Try restarting the application"
echo "4. Check browser console for JavaScript errors"
'''
        
        with open('auto_fix_cameras.sh', 'w') as f:
            f.write(fix_script)
        
        os.chmod('auto_fix_cameras.sh', 0o755)
        print(f"\n💾 Fix script created: auto_fix_cameras.sh")

def main():
    """Main diagnostic function"""
    debugger = CameraDebugger()
    
    print("🔍 NT TELECOM CAMERA DIAGNOSTIC TOOL")
    print("=" * 50)
    
    try:
        # Run comprehensive test
        results = debugger.generate_test_report()
        
        # Find problem cameras
        problem_cameras = [
            name for name, data in results.items() 
            if not (data.get('rtsp', False) and data.get('ffmpeg', False))
        ]
        
        if problem_cameras:
            debugger.create_fix_script(problem_cameras)
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Fix any network/RTSP issues identified")
        print(f"2. Check browser console (F12) for JavaScript errors")
        print(f"3. Restart Flask application if needed")
        print(f"4. Test video feeds in browser")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")

if __name__ == "__main__":
    main()