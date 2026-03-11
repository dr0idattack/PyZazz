#!/usr/bin/env python3
"""
Quick tempo test - 10 seconds
"""

import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from audio_analyzer import AudioAnalyzer

def quick_test():
    print("Quick Tempo Test (10 seconds)")
    print("   Clap at a steady rhythm...")
    
    analyzer = AudioAnalyzer(ultra_low_latency=True)
    start_time = time.time()
    beats = 0
    last_tempo = 0
    
    while time.time() - start_time < 10.0:
        if analyzer.detect_beat():
            beats += 1
            tempo = analyzer.get_tempo()
            if tempo != last_tempo and tempo > 0:
                print(f"Beat #{beats}: {tempo} BPM")
                last_tempo = tempo
        
        time.sleep(0.05)
    
    analyzer.stop()
    print(f"\nDetected {beats} beats, final tempo: {last_tempo} BPM")

if __name__ == "__main__":
    quick_test()
