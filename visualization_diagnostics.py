#!/usr/bin/env python3
"""
Visualization Diagnostics Tool
Helps troubleshoot visualization startup issues
"""

import tkinter as tk
import sys
import os
from pathlib import Path

def run_display_diagnostics():
    """Run comprehensive display diagnostics"""
    print("🔍 DMX Light Show - Visualization Diagnostics")
    print("=" * 60)
    
    results = {
        'tkinter': False,
        'displays': [],
        'window_creation': False,
        'canvas_creation': False,
        'fullscreen': False,
        'geometry': False
    }
    
    # Test 1: Tkinter availability
    print("\n1️⃣ Testing Tkinter availability...")
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        print("✅ Tkinter is available")
        results['tkinter'] = True
    except Exception as e:
        print(f"❌ Tkinter error: {e}")
        return results
    
    # Test 2: Display detection
    print("\n2️⃣ Detecting displays...")
    try:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        print(f"✅ Primary display: {screen_width}x{screen_height}")
        results['displays'].append(f"Primary: {screen_width}x{screen_height}")
        
        # Try to detect external displays by testing positions
        test_positions = [(3024, 0), (2560, 0), (1920, 0), (1680, 0), (1440, 0)]
        
        for x, y in test_positions:
            try:
                test_win = tk.Toplevel(root)
                test_win.withdraw()
                test_win.geometry(f"100x100+{x}+{y}")
                test_win.update_idletasks()
                
                actual_x = test_win.winfo_x()
                if actual_x >= x - 50:  # Position worked
                    print(f"✅ External display detected at position ({x}, {y})")
                    results['displays'].append(f"External: position {x},{y}")
                
                test_win.destroy()
                
            except Exception as e:
                print(f"⚠️ Position {x},{y} test failed: {e}")
                
    except Exception as e:
        print(f"❌ Display detection error: {e}")
    
    # Test 3: Window creation
    print("\n3️⃣ Testing window creation...")
    try:
        test_window = tk.Toplevel(root)
        test_window.title("Diagnostic Test Window")
        test_window.configure(bg='black')
        test_window.geometry("800x600+100+100")
        test_window.update_idletasks()
        
        if test_window.winfo_exists():
            print("✅ Window creation successful")
            results['window_creation'] = True
            
            # Test 4: Canvas creation
            print("\n4️⃣ Testing canvas creation...")
            try:
                test_canvas = tk.Canvas(test_window, 
                                      width=400, height=300,
                                      bg='black', highlightthickness=0)
                test_canvas.pack()
                
                # Test drawing
                test_canvas.create_rectangle(10, 10, 50, 50, fill='red')
                test_canvas.update_idletasks()
                
                print("✅ Canvas creation and drawing successful")
                results['canvas_creation'] = True
                
            except Exception as e:
                print(f"❌ Canvas creation error: {e}")
            
            # Test 5: Fullscreen mode
            print("\n5️⃣ Testing fullscreen mode...")
            try:
                test_window.attributes('-fullscreen', True)
                test_window.update_idletasks()
                print("✅ Fullscreen mode successful")
                results['fullscreen'] = True
                
                # Exit fullscreen
                test_window.attributes('-fullscreen', False)
                
            except Exception as e:
                print(f"❌ Fullscreen mode error: {e}")
            
            # Test 6: Geometry changes
            print("\n6️⃣ Testing geometry changes...")
            try:
                test_window.geometry("600x400+200+200")
                test_window.update_idletasks()
                
                actual_width = test_window.winfo_width()
                actual_height = test_window.winfo_height()
                
                if actual_width > 0 and actual_height > 0:
                    print(f"✅ Geometry changes successful: {actual_width}x{actual_height}")
                    results['geometry'] = True
                else:
                    print(f"⚠️ Geometry change resulted in zero dimensions")
                
            except Exception as e:
                print(f"❌ Geometry change error: {e}")
            
            test_window.destroy()
            
        else:
            print("❌ Window creation failed - window doesn't exist")
            
    except Exception as e:
        print(f"❌ Window creation error: {e}")
    
    # Test 7: System information
    print("\n7️⃣ System information...")
    try:
        print(f"✅ Python version: {sys.version.split()[0]}")
        print(f"✅ Platform: {sys.platform}")
        print(f"✅ Tkinter version: {tk.TkVersion}")
        if hasattr(tk, 'TclVersion'):
            print(f"✅ Tcl version: {tk.TclVersion}")
    except Exception as e:
        print(f"⚠️ System info error: {e}")
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 30)
    
    total_tests = len([k for k in results.keys() if k != 'displays'])
    passed_tests = sum(1 for k, v in results.items() if k != 'displays' and v)
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Displays found: {len(results['displays'])}")
    
    if passed_tests == total_tests and len(results['displays']) > 0:
        print("🎉 ALL TESTS PASSED - Visualization should work!")
    elif passed_tests >= total_tests - 1:
        print("⚠️ MOSTLY WORKING - Visualization might have minor issues")
    else:
        print("❌ ISSUES DETECTED - Visualization may fail to start")
        print("\n🛠️ TROUBLESHOOTING SUGGESTIONS:")
        
        if not results['tkinter']:
            print("• Install or repair Python tkinter package")
        if not results['window_creation']:
            print("• Check display permissions and window manager")
        if not results['canvas_creation']:
            print("• Graphics driver or tkinter canvas issues")
        if not results['fullscreen']:
            print("• Fullscreen mode not supported or restricted")
        if len(results['displays']) == 0:
            print("• No displays detected - check connections")
    
    # Cleanup
    try:
        root.destroy()
    except:
        pass
    
    return results

def test_pil_availability():
    """Test if PIL is available for logo functionality"""
    print("\n🖼️ Testing PIL (logo support)...")
    try:
        from PIL import Image, ImageTk
        print("✅ PIL is available - logo overlay will work")
        return True
    except ImportError:
        print("⚠️ PIL not available - logo overlay will use fallback text")
        return False

def test_audio_system():
    """Test audio system availability"""
    print("\n🎵 Testing audio system...")
    try:
        import sounddevice as sd
        print("✅ SoundDevice is available")
        
        # List audio devices
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        print(f"✅ Found {len(input_devices)} input devices")
        
        return True
    except ImportError:
        print("❌ SoundDevice not available - audio reactive features won't work")
        return False
    except Exception as e:
        print(f"⚠️ Audio system error: {e}")
        return False

def main():
    """Run all diagnostics"""
    # Run display diagnostics
    display_results = run_display_diagnostics()
    
    # Run additional system tests
    pil_available = test_pil_availability()
    audio_available = test_audio_system()
    
    print("\n🎯 FINAL RECOMMENDATIONS")
    print("=" * 40)
    
    if display_results.get('window_creation') and display_results.get('canvas_creation'):
        print("✅ Visualizations should work properly")
        
        if len(display_results.get('displays', [])) > 1:
            print("✅ External display detected - fullscreen visualizations available")
        else:
            print("ℹ️ Only primary display detected - visualizations will use main screen")
            
        if not display_results.get('fullscreen'):
            print("⚠️ Fullscreen mode issues detected - visualizations may appear windowed")
            
    else:
        print("❌ Core visualization features may not work")
        print("   Consider checking system requirements and permissions")
    
    if not pil_available:
        print("ℹ️ Install Pillow (pip install pillow) for logo image support")
    
    if not audio_available:
        print("⚠️ Audio reactive features require sounddevice (pip install sounddevice)")
    
    print(f"\n📋 Save this diagnostic report if you need support!")

if __name__ == "__main__":
    main()