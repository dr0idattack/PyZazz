import sounddevice as sd
import numpy as np
import threading
import time
from collections import deque
from typing import Optional
import librosa
import warnings

# Suppress librosa warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='librosa')

class AudioAnalyzer:
    def __init__(self,
                 sample_rate: int = 44100,
                 chunk_size: int = 128,
                 channels: int = 2,
                 # tunable knobs
                 blocksize: int | None = None,
                 energy_history_len: int = 48,
                 audio_data_maxlen: int = 32,
                 debug_latency: bool = False,
                 debug_log_interval: float = 5.0,
                 test_mode: bool = True,
                 ultra_low_latency: bool = True,
                 input_device: int | str | None = None):
        """Initialize AudioAnalyzer.

        blocksize overrides chunk_size when provided. debug_latency enables
        periodic latency logging (callback->process, callback->UI).
        """
        # Core params
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size if blocksize is None else blocksize
        self.channels = channels

        # Debug knobs
        self.debug_latency = debug_latency
        self._debug_log_interval = float(debug_log_interval)

        # Audio processing variables (store (timestamp, array) tuples)
        self.audio_data = deque(maxlen=audio_data_maxlen)
        self.current_level = 0.0
        self.beat_threshold = 0.05  # Reduced base threshold for better beat detection (was 0.06)
        self.last_beat_time = 0.0
        self.min_beat_interval = 0.30  # Reduced from 0.35s for faster beat detection (allows up to 200 BPM)
        
        # Reactivity-aware beat detection
        self.current_reactivity_mode = 'medium'  # Track current reactivity mode
        self.very_reactive_threshold = 0.025  # Much more sensitive threshold (was 0.035)

        # Enhanced analysis
        self.beat_history = deque(maxlen=50)  # Increased for better tempo accuracy
        self.energy_history = deque(maxlen=energy_history_len)
        self.current_tempo = 0
        self.tempo_history = deque(maxlen=10)  # For tempo smoothing
        self.energy_trend = 0.0
        self.song_intensity = 0.5
        
        # Improved beat detection parameters
        self.beat_energy_buffer = deque(maxlen=20)  # Track recent energy for comparison
        self.last_significant_level = 0.0
        self.beat_detection_enabled = True
        
        # Ultra-low latency and predictive features
        self.beat_predictor_enabled = True
        self.predicted_beat_time = 0.0
        self.beat_confidence = 0.0
        self.tempo_locked = False
        self.beat_prediction_buffer = deque(maxlen=8)  # Store recent beat intervals for prediction
        self.next_predicted_beat = 0.0

        # Test mode - disabled by default for real music detection
        self.test_mode = False  # Changed to False for real tempo detection
        self.simulated_tempo = 128
        self.last_simulated_beat = 0.0

        # Logging
        self.last_tempo_log = 0.0
        self.beat_count = 0
        self.last_spectrum_log = 0.0

        # Stream / threading
        self.stream = None
        self.is_recording = False
        self.processing_thread = None
        self._cleaned_up = False

        # Ultra-low latency mode: tighten internal buffers
        if ultra_low_latency:
            self.chunk_size = 32  # Even smaller chunks for lower latency
            self.energy_history = deque(maxlen=16)  # Smaller history
            self.audio_data = deque(maxlen=8)  # Minimal buffer
            self.min_beat_interval = 0.30  # 300ms minimum - prevents over-detection even in low latency mode
            self.beat_threshold = 0.04  # More sensitive threshold

        # Last callback timestamp (for latency measurements)
        self._last_callback_time = None

        # Selected input device (index or name). None means default device.
        self.input_device = input_device

        # Event to notify processing thread when new data arrives
        self._data_event = threading.Event()
        
        # Librosa-based BPM detection for improved accuracy
        self.librosa_buffer = deque(maxlen=int(sample_rate * 30))  # 30 seconds of audio at sample rate
        self.librosa_buffer_mono = deque(maxlen=int(sample_rate * 30))  # Mono version for librosa
        self.librosa_bpm_cache = None  # Cache BPM result
        self.librosa_last_analysis = 0.0  # Last time librosa analysis was run
        self.librosa_analysis_interval = 10.0  # Analyze every 10 seconds
        self.librosa_beats = []  # Store beat times from librosa
        self.librosa_tempo = None  # Store tempo from librosa

        # Start the audio stream and processing thread
        self._start_recording()
        
    def _start_recording(self):
        """Start audio input stream"""
        try:
            # List available input devices (helpful for macOS)
            self._list_audio_devices()
            
            # Try different device configurations
            devices_to_try = []
            
            # If we have a device name or ID specified, try to resolve it
            if self.input_device is not None and self.input_device != 'default':
                if isinstance(self.input_device, str):
                    # Try to find device by name
                    device_index = self._find_device_by_name(self.input_device)
                    if device_index is not None:
                        devices_to_try.append(device_index)
                    else:
                        # If name not found, try the string as-is (might be numeric)
                        devices_to_try.append(self.input_device)
                else:
                    # It's already a device index
                    devices_to_try.append(self.input_device)
            
            # Add fallback devices for macOS (prioritize MacBook Pro Microphone)
            macbook_mic = self._find_device_by_name("MacBook Pro Microphone")
            if macbook_mic is not None and macbook_mic not in devices_to_try:
                devices_to_try.append(macbook_mic)
                
            # Add other common working devices
            devices_to_try.extend([None, 1, 0])  # Default, then device 1 (usually mic), then device 0
            
            success = False
            for device in devices_to_try:
                # Try both 1 and 2 channels for each device
                for channels in [1, 2]:
                    try:
                        print(f"Trying audio device: {device} with {channels} channels")
                        
                        # Start the audio stream with callback - ultra-low latency settings
                        kwargs = dict(
                            samplerate=self.sample_rate,
                            channels=channels,
                            blocksize=self.chunk_size,
                            dtype=np.float32,
                            callback=self._audio_callback,
                            latency=0.005  # 5ms latency
                        )
                        if device is not None:
                            kwargs['device'] = device

                        self.stream = sd.InputStream(**kwargs)
                        self.stream.start()
                        self.is_recording = True
                        self.channels = channels  # Update actual channels used
                        
                        # Start processing thread
                        self.processing_thread = threading.Thread(target=self._process_audio, daemon=True)
                        self.processing_thread.start()
                        
                        print(f"✅ Audio recording started successfully with device: {device}, channels: {channels}")
                        success = True
                        break
                        
                    except Exception as device_error:
                        print(f"Device {device} with {channels} channels failed: {device_error}")
                        if hasattr(self, 'stream') and self.stream:
                            try:
                                self.stream.close()
                            except:
                                pass
                        continue
                
                if success:
                    break
            
            if not success:
                print("❌ Failed to start audio recording with any device")
                print("Note: On macOS, you may need to grant microphone permissions to your terminal/IDE")
                
        except Exception as e:
            print(f"Failed to start audio recording: {e}")
            print("Note: On macOS, you may need to grant microphone permissions to your terminal/IDE")
            
    def _list_audio_devices(self):
        """List available audio input devices (helpful for troubleshooting on macOS)"""
        print("Available audio input devices:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  {i}: {device['name']} ({device['hostapi']})")
    
    def _find_device_by_name(self, device_name: str) -> Optional[int]:
        """Find device index by name (case-insensitive partial match)"""
        if not device_name or device_name == 'default':
            return None
            
        try:
            devices = sd.query_devices()
            device_name_lower = device_name.lower()
            
            # First try exact match
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0 and device['name'].lower() == device_name_lower:
                    print(f"Found exact device match: {i}: {device['name']}")
                    return i
            
            # Then try partial match
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0 and device_name_lower in device['name'].lower():
                    print(f"Found partial device match: {i}: {device['name']}")
                    return i
                    
            print(f"Device '{device_name}' not found")
            return None
            
        except Exception as e:
            print(f"Error finding device by name: {e}")
            return None
                
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback function for audio input"""
        if status:
            print(f"Audio callback status: {status}")

        # Store audio data with timestamp (indata is already a numpy array)
        # use the time module (not the time_info param)
        ts = time.time()
        try:
            chunk = indata.flatten().copy()
        except Exception:
            # fallback if flatten not available
            chunk = np.array(indata).flatten()

        # Append tuple (timestamp, chunk)
        self.audio_data.append((ts, chunk))
        # remember last callback timestamp for quick access
        self._last_callback_time = ts
        # Wake processing thread immediately for lower latency
        try:
            self._data_event.set()
        except Exception:
            pass
        
    def _process_audio(self):
        """Background thread for processing audio data with ultra-low latency"""
        while self.is_recording:
            # Ultra-low latency: minimal wait time
            self._data_event.wait(timeout=0.0005)  # Reduced from 2ms to 0.5ms
            self._data_event.clear()

            if len(self.audio_data) == 0:
                # no data to process yet
                continue

            # Get the latest audio chunk and its timestamp
            try:
                latest_ts, latest_chunk = self.audio_data[-1]
            except Exception:
                # Backwards compatibility if older entries are raw arrays
                latest_ts = time.time()
                latest_chunk = self.audio_data[-1]

            # Calculate RMS (Root Mean Square) for volume level
            # Ensure we have valid audio data
            if len(latest_chunk) == 0:
                continue
                
            # Handle different data types and scales
            if latest_chunk.dtype == np.float32:
                # Data already normalized to [-1, 1] range
                rms = np.sqrt(np.mean(latest_chunk**2))
                # Scale for good sensitivity without clipping
                self.current_level = min(1.0, rms * 15)  # Reduced from 50 to 15 - less aggressive
            else:
                # Integer data (int16, int32) - normalize first
                if latest_chunk.dtype == np.int16:
                    normalized = latest_chunk.astype(np.float32) / 32768.0
                elif latest_chunk.dtype == np.int32:
                    normalized = latest_chunk.astype(np.float32) / 2147483648.0
                else:
                    normalized = latest_chunk.astype(np.float32)
                
                rms = np.sqrt(np.mean(normalized**2))
                self.current_level = min(1.0, rms * 15)
            
            # Debug logging for audio level troubleshooting - reduce frequency
            if hasattr(self, '_last_audio_debug') and time.time() - self._last_audio_debug > 5.0:  # Increased from 2s to 5s
                self._last_audio_debug = time.time()
                chunk_stats = f"chunk: len={len(latest_chunk)}, dtype={latest_chunk.dtype}, range=[{np.min(latest_chunk):.4f}, {np.max(latest_chunk):.4f}]"
                print(f"AUDIO DEBUG: RMS={rms:.4f}, level={self.current_level:.4f}, {chunk_stats}")
            elif not hasattr(self, '_last_audio_debug'):
                self._last_audio_debug = time.time()

            # Track energy history for trend analysis
            self.energy_history.append(self.current_level)
            self.beat_energy_buffer.append(self.current_level)
            
            # Feed audio data to librosa buffer for BPM analysis
            self._feed_librosa_buffer(latest_chunk)
            
            # Track significant level changes for better beat detection
            if self.current_level > self.last_significant_level * 1.5:
                self.last_significant_level = self.current_level
            elif self.current_level < self.last_significant_level * 0.5:
                self.last_significant_level = self.current_level

            # Update energy trend and song intensity
            self._update_energy_analysis()
            
            # Run librosa BPM analysis periodically
            self._update_librosa_bpm()

            # measure processing latency (time from callback -> processing)
            if getattr(self, 'debug_latency', False):
                proc_latency = time.time() - latest_ts
                # maintain a short history of processing latencies
                if not hasattr(self, '_proc_latency_history'):
                    self._proc_latency_history = deque(maxlen=200)
                    self._last_latency_log = 0
                self._proc_latency_history.append(proc_latency)
                # periodic logging
                if time.time() - self._last_latency_log > self._debug_log_interval:
                    avg = float(np.mean(self._proc_latency_history)) if len(self._proc_latency_history) else 0.0
                    print(f"[AudioAnalyzer] callback->process avg latency: {avg*1000:.1f} ms over {len(self._proc_latency_history)} samples")
                    self._last_latency_log = time.time()
                
            # Ultra-low latency: minimal sleep to avoid busy loop but maximize responsiveness  
            time.sleep(0.0001)  # Reduced from 0.2ms to 0.1ms
            
    def get_audio_level(self) -> float:
        """Get current audio level (0.0 to 1.0)"""
        return self.current_level
    
    def _check_predicted_beat(self, current_time: float) -> bool:
        """Check if we should trigger a predicted beat for ultra-low latency"""
        if not self.beat_predictor_enabled or not self.tempo_locked:
            return False
        
        # Check if we're close to a predicted beat time
        if hasattr(self, 'next_predicted_beat') and self.next_predicted_beat > 0:
            time_to_beat = self.next_predicted_beat - current_time
            # Trigger if we're within 50ms of predicted beat
            if abs(time_to_beat) <= 0.05:  
                self.predicted_beat_time = current_time
                self._update_beat_prediction(current_time)
                return True
        
        return False
    
    def _update_beat_prediction(self, current_time: float):
        """Update beat prediction based on established tempo"""
        if len(self.beat_prediction_buffer) >= 3:
            # Calculate average interval from recent beats
            avg_interval = np.mean(list(self.beat_prediction_buffer))
            # Predict next beat
            self.next_predicted_beat = current_time + avg_interval
            self.beat_confidence = min(1.0, len(self.beat_prediction_buffer) / 8.0)
            
        # Lock tempo when we have consistent predictions
        if len(self.beat_prediction_buffer) >= 5:
            intervals = list(self.beat_prediction_buffer)
            std_dev = np.std(intervals)
            if std_dev < 0.05:  # Low variation = stable tempo
                self.tempo_locked = True
        
    def detect_beat(self) -> bool:
        """Detect if a beat/spike in audio occurred with predictive capabilities"""
        current_time = time.time()
        
        # Check for predicted beat first (ultra-low latency response)
        predicted_beat = self._check_predicted_beat(current_time)
        
        # If debug mode, measure callback->UI latency using last callback timestamp
        if getattr(self, 'debug_latency', False):
            last_cb = getattr(self, '_last_callback_time', None)
            if last_cb is not None:
                ui_latency = current_time - last_cb
                # log occasionally to avoid flooding console
                try:
                    if not hasattr(self, '_last_ui_latency_log'):
                        self._last_ui_latency_log = 0
                    if current_time - self._last_ui_latency_log > self._debug_log_interval:
                        print(f"[AudioAnalyzer] callback->UI latency: {ui_latency*1000:.1f} ms")
                        self._last_ui_latency_log = current_time
                except Exception:
                    pass
        
        # Test mode: simulate beats at the specified tempo for better testing
        if self.test_mode and self.current_level > 0.05:  # Only when there's some audio
            beat_interval = 60.0 / self.simulated_tempo  # Convert BPM to seconds
            if current_time - self.last_simulated_beat >= beat_interval:
                self.last_simulated_beat = current_time
                self.last_beat_time = current_time
                self.beat_history.append(current_time)
                old_tempo = self.current_tempo
                self.current_tempo = self.simulated_tempo  # Set tempo directly in test mode
                self.beat_count += 1
                
                # Log tempo changes and periodic beat info
                if old_tempo != self.simulated_tempo or current_time - self.last_tempo_log > 15.0:
                    # print(f"BEAT #{self.beat_count}: Tempo {old_tempo}->{self.simulated_tempo} BPM | Energy: {self.current_level:.3f} | Test Mode")
                    self.last_tempo_log = current_time
                
                # Vary tempo slightly for more realistic testing
                import random
                self.simulated_tempo = max(60, min(200, self.simulated_tempo + random.randint(-5, 5)))
                return True
        
        # Check if enough time has passed since last beat (adjust for reactivity mode)
        if self.current_reactivity_mode == 'very_reactive':
            min_interval = 0.20  # Ultra-fast 200ms for very reactive (up to 300 BPM)
        elif self.current_reactivity_mode == 'medium':
            min_interval = 0.25  # Faster 250ms for medium mode (up to 240 BPM)
        else:
            min_interval = self.min_beat_interval  # Default for easy mode
        if current_time - self.last_beat_time < min_interval:
            return False
        
        # Only detect beats if we have sufficient audio level (made more sensitive)
        if self.current_level < 0.015:  # Lower threshold - more sensitive to quiet audio
            return False
            
        # Use reactivity-aware threshold for beat detection
        if self.current_reactivity_mode == 'very_reactive':
            active_threshold = self.very_reactive_threshold  # Ultra-sensitive for very reactive
        elif self.current_reactivity_mode == 'medium':
            active_threshold = 0.04  # More sensitive threshold for medium mode (between base and very reactive)
        else:
            active_threshold = self.beat_threshold  # Standard threshold for easy mode
        
        # Improved beat detection with better filtering
        if self.current_level > active_threshold and len(self.beat_energy_buffer) >= 10:
            
            # Use energy buffer for more stable analysis
            recent_levels = list(self.beat_energy_buffer)[-10:]
            older_levels = list(self.beat_energy_buffer)[-20:-10] if len(self.beat_energy_buffer) >= 20 else recent_levels[:5]
            
            if not recent_levels:
                return False
                
            recent_avg = np.mean(recent_levels)
            older_avg = np.mean(older_levels) if older_levels else recent_avg
            max_recent = np.max(recent_levels)
            
            # Require significant energy increase for beat detection
            energy_increase_ratio = recent_avg / older_avg if older_avg > 0 else 1.0
            current_spike_ratio = self.current_level / recent_avg if recent_avg > 0 else 1.0
            
            # Beat detection criteria - adjust based on reactivity mode
            if self.current_reactivity_mode == 'very_reactive':
                beat_conditions = {
                    'absolute_threshold': self.current_level > max(active_threshold, 0.06),  # Much lower threshold for very reactive
                    'spike_ratio': current_spike_ratio > 1.2,  # More sensitive spike detection
                    'energy_building': energy_increase_ratio > 1.02 or self.current_level > max_recent * 0.5,  # More lenient
                    'minimum_level': self.current_level > 0.025  # Much lower minimum level
                }
            elif self.current_reactivity_mode == 'medium':
                beat_conditions = {
                    'absolute_threshold': self.current_level > max(active_threshold, 0.08),  # Lower threshold than before
                    'spike_ratio': current_spike_ratio > 1.3,  # More sensitive spike detection
                    'energy_building': energy_increase_ratio > 1.05 or self.current_level > max_recent * 0.6,  # More responsive
                    'minimum_level': self.current_level > 0.03  # Lower minimum level
                }
            else:  # easy mode
                beat_conditions = {
                    'absolute_threshold': self.current_level > max(active_threshold, 0.10),  # Lower threshold
                    'spike_ratio': current_spike_ratio > 1.4,  # More sensitive spike detection
                    'energy_building': energy_increase_ratio > 1.08 or self.current_level > max_recent * 0.65,  # More responsive
                    'minimum_level': self.current_level > 0.04  # Lower minimum level
                }
            
            # Debug beat detection less frequently to reduce log spam
            if hasattr(self, '_last_beat_debug') and time.time() - self._last_beat_debug > 8.0:  # Increased from 3s to 8s
                self._last_beat_debug = time.time()
                passed_conditions = [name for name, passed in beat_conditions.items() if passed]
                failed_conditions = [name for name, passed in beat_conditions.items() if not passed]
                print(f"BEAT DEBUG: Level={self.current_level:.3f}, Spike={current_spike_ratio:.2f}x, Energy={energy_increase_ratio:.2f}x")
                print(f"  Passed: {passed_conditions}")
                print(f"  Failed: {failed_conditions}")
                print(f"  Thresholds: abs={max(self.beat_threshold, 0.12):.3f}, spike=1.5x, energy=1.1x, min=0.05")
            elif not hasattr(self, '_last_beat_debug'):
                self._last_beat_debug = time.time()
            
            if all(beat_conditions.values()):
                
                self.last_beat_time = current_time
                self.beat_history.append(current_time)
                old_tempo = self.current_tempo
                self._update_tempo()
                self.beat_count += 1
                
                # Update beat prediction system
                if len(self.beat_history) >= 2:
                    recent_beats = list(self.beat_history)[-2:]
                    interval = recent_beats[1] - recent_beats[0]
                    self.beat_prediction_buffer.append(interval)
                    self._update_beat_prediction(current_time)
                
                # Enhanced debug logging for BPM troubleshooting
                if self.beat_count % 8 == 0:  # More frequent logging
                    recent_intervals = []
                    beats = list(self.beat_history)[-5:]  # Last 5 beats
                    for i in range(1, len(beats)):
                        recent_intervals.append(beats[i] - beats[i-1])
                    avg_interval = np.mean(recent_intervals) if recent_intervals else 0
                    raw_bpm = int(60.0 / avg_interval) if avg_interval > 0 else 0
                    print(f"BEAT #{self.beat_count}: Raw BPM={raw_bpm} | Final BPM={self.current_tempo} | Energy: {self.current_level:.3f} | Spike: {current_spike_ratio:.2f}x | Avg Interval: {avg_interval:.3f}s")
                
                return True
        
        # Fallback: Simple beat detection if advanced method doesn't trigger
        # This catches cases where audio is present but doesn't meet complex criteria
        if (len(self.beat_energy_buffer) >= 5 and 
            self.current_level > self.beat_threshold and 
            self.current_level > 0.05 and
            len(self.beat_history) == 0):  # Only if no beats detected yet
            
            recent_5 = list(self.beat_energy_buffer)[-5:]
            if self.current_level > np.mean(recent_5) * 1.5:  # Simple spike detection
                self.last_beat_time = current_time
                self.beat_history.append(current_time)
                self.beat_count += 1
                print(f"🔄 FALLBACK BEAT #{self.beat_count}: Level={self.current_level:.3f} (simple spike detection)")
                
                # Update beat prediction system
                if len(self.beat_history) >= 2:
                    recent_beats = list(self.beat_history)[-2:]
                    interval = recent_beats[1] - recent_beats[0]
                    self.beat_prediction_buffer.append(interval)
                    self._update_beat_prediction(current_time)
                
                return True
        
        # Return predicted beat if no real beat detected
        return predicted_beat

    def get_last_callback_age(self) -> float | None:
        """Return seconds since last audio callback (or None if unknown)"""
        last = getattr(self, '_last_callback_time', None)
        if last is None:
            return None
        return time.time() - last
        
    def get_frequency_spectrum(self) -> Optional[np.ndarray]:
        """Get frequency spectrum using FFT"""
        if len(self.audio_data) == 0:
            return None

        # Get latest audio chunk (handle tuple entries)
        item = self.audio_data[-1]
        latest_chunk = item[1] if isinstance(item, tuple) else item

        # Apply FFT
        fft = np.fft.fft(latest_chunk)
        magnitude = np.abs(fft[:len(fft)//2])  # Only positive frequencies

        return magnitude
        
    def get_frequency_bands(self, num_bands: int = 8):
        """Get audio level for different frequency bands"""
        spectrum = self.get_frequency_spectrum()
        if spectrum is None:
            return {'bass': 0.0, 'mid': 0.0, 'treble': 0.0}
            
        # Divide spectrum into bands
        band_size = len(spectrum) // num_bands
        bands = []
        
        # Normalize by the maximum band energy to preserve relative levels
        max_val = float(np.max(spectrum)) if len(spectrum) > 0 else 1.0
        if max_val <= 0:
            max_val = 1.0
        for i in range(num_bands):
            start_idx = i * band_size
            end_idx = (i + 1) * band_size
            band_energy = float(np.mean(spectrum[start_idx:end_idx])) if end_idx > start_idx else 0.0
            bands.append(min(1.0, band_energy / max_val))
        
        # Return as dictionary with expected keys
        if len(bands) >= 3:
            return {
                'bass': bands[0],  # Low frequencies
                'mid': np.mean(bands[1:len(bands)//2+1]) if len(bands) > 2 else bands[1] if len(bands) > 1 else 0.0,  # Mid frequencies
                'treble': np.mean(bands[len(bands)//2:]) if len(bands) > 2 else 0.0  # High frequencies
            }
        else:
            return {'bass': 0.0, 'mid': 0.0, 'treble': 0.0}
        
    def set_beat_threshold(self, threshold: float):
        """Set the threshold for beat detection (0.0 to 1.0)"""
        self.beat_threshold = max(0.0, min(1.0, threshold))
        
    def set_reactivity_mode(self, mode: str):
        """Set reactivity mode for adaptive beat detection"""
        self.current_reactivity_mode = mode
        
    def _feed_librosa_buffer(self, audio_chunk):
        """Feed audio data to librosa buffer for BPM analysis"""
        try:
            # Convert to mono for librosa (if stereo, average channels)
            if len(audio_chunk.shape) > 1 and audio_chunk.shape[1] > 1:
                # Stereo -> mono
                mono_chunk = np.mean(audio_chunk, axis=1)
            else:
                mono_chunk = audio_chunk.flatten()
                
            # Normalize to [-1, 1] range if not already
            if mono_chunk.dtype != np.float32:
                if mono_chunk.dtype == np.int16:
                    mono_chunk = mono_chunk.astype(np.float32) / 32768.0
                elif mono_chunk.dtype == np.int32:
                    mono_chunk = mono_chunk.astype(np.float32) / 2147483648.0
                else:
                    mono_chunk = mono_chunk.astype(np.float32)
            
            # Add to circular buffer
            self.librosa_buffer_mono.extend(mono_chunk)
            
        except Exception as e:
            print(f"Error feeding librosa buffer: {e}")
    
    def _update_librosa_bpm(self):
        """Update BPM using librosa analysis on accumulated audio buffer"""
        current_time = time.time()
        
        # Only run analysis periodically to avoid performance impact
        if current_time - self.librosa_last_analysis < self.librosa_analysis_interval:
            return
        
        # Need sufficient audio data for analysis (at least 10 seconds)
        min_samples = int(self.sample_rate * 10)
        if len(self.librosa_buffer_mono) < min_samples:
            return
        
        try:
            # Convert deque to numpy array for librosa
            audio_data = np.array(list(self.librosa_buffer_mono))
            
            # Run librosa tempo analysis
            tempo, beat_frames = librosa.beat.beat_track(
                y=audio_data, 
                sr=self.sample_rate,
                hop_length=512,
                start_bpm=120,
                tightness=100  # Higher tightness for more accurate tempo
            )
            
            # Convert beat frames to times
            beat_times = librosa.frames_to_time(beat_frames, sr=self.sample_rate)
            
            # Store results
            self.librosa_tempo = tempo
            self.librosa_beats = beat_times
            self.librosa_bpm_cache = int(tempo)
            self.librosa_last_analysis = current_time
            
            # Update the main tempo with librosa result
            if self.librosa_bpm_cache and 60 <= self.librosa_bpm_cache <= 200:
                old_tempo = self.current_tempo
                self.current_tempo = self.librosa_bpm_cache
                if old_tempo != self.current_tempo:
                    print(f"LIBROSA BPM: {self.current_tempo} (was {old_tempo})")
            
        except Exception as e:
            if hasattr(self, '_librosa_error_logged') and current_time - self._librosa_error_logged < 60:
                return  # Don't spam errors
            print(f"Librosa BPM analysis error: {e}")
            self._librosa_error_logged = current_time
        
    def _update_tempo(self):
        """Update current tempo based on beat history with improved accuracy"""
        if len(self.beat_history) < 4:  # Require fewer beats to start showing tempo
            return
            
        # Calculate intervals between recent beats (last 10 beats for stability)
        beats = list(self.beat_history)[-10:]  # Use fewer recent beats for more responsive tempo
        intervals = []
        
        for i in range(1, len(beats)):
            interval = beats[i] - beats[i-1]
            intervals.append(interval)
            
        if not intervals:
            return
            
        # Filter out outliers for musical tempo ranges
        # Most music is between 60-200 BPM (1.0-0.3 second intervals)
        valid_intervals = [i for i in intervals if 0.3 <= i <= 1.0]  # Focus on common tempo ranges
        
        # If we don't have enough valid intervals in common range, expand slightly
        if len(valid_intervals) < 2:
            valid_intervals = [i for i in intervals if 0.25 <= i <= 1.5]
        
        if len(valid_intervals) >= 2:
            # Use median to reduce outlier impact
            median_interval = np.median(valid_intervals)
            calculated_tempo = int(60.0 / median_interval)
            
            # Less aggressive tempo corrections - trust the detection more
            # Only correct if tempo seems clearly wrong
            if calculated_tempo > 200:  # Very fast - likely double detection
                corrected_tempo = calculated_tempo // 2
                if 60 <= corrected_tempo <= 180:  # Reasonable range
                    calculated_tempo = corrected_tempo
                    print(f"🎵 Halved excessive BPM: {calculated_tempo} (was {calculated_tempo * 2})")
            
            elif calculated_tempo < 50:  # Very slow - likely missing beats
                corrected_tempo = calculated_tempo * 2
                if 60 <= corrected_tempo <= 180:  # Reasonable range
                    calculated_tempo = corrected_tempo
                    print(f"🎵 Doubled low BPM: {calculated_tempo} (was {calculated_tempo // 2})")
            
            # Simpler tempo smoothing - less aggressive
            if hasattr(self, 'last_stable_tempo') and self.current_tempo > 0:
                # Don't allow tempo to change too dramatically at once
                max_change = max(10, self.current_tempo * 0.2)  # Max 20% change or 10 BPM
                if abs(calculated_tempo - self.current_tempo) > max_change:
                    # Blend towards new tempo gradually
                    if calculated_tempo > self.current_tempo:
                        calculated_tempo = self.current_tempo + max_change
                    else:
                        calculated_tempo = self.current_tempo - max_change
            
            self.current_tempo = calculated_tempo
            self.last_stable_tempo = calculated_tempo
                
            # Clamp to reasonable musical range
            self.current_tempo = max(50, min(200, self.current_tempo))
            
    def _update_energy_analysis(self):
        """Update energy trend and song intensity"""
        if len(self.energy_history) < 20:
            return
            
        recent_energy = list(self.energy_history)
        
        # Calculate energy trend (slope of recent energy)
        if len(recent_energy) >= 20:
            x = np.arange(len(recent_energy[-20:]))
            y = recent_energy[-20:]
            slope = np.polyfit(x, y, 1)[0]
            self.energy_trend = np.clip(slope * 100, -1.0, 1.0)  # Scale to -1 to 1
            
        # Update overall song intensity (moving average)
        if len(recent_energy) >= 50:
            self.song_intensity = np.mean(recent_energy[-50:])
            
    def get_tempo(self) -> int:
        """Get current tempo in BPM"""
        return self.current_tempo
        
    def get_energy_trend(self) -> float:
        """Get energy trend (-1.0 = falling, 0.0 = stable, 1.0 = rising)"""
        return self.energy_trend
        
    def get_song_intensity(self) -> float:
        """Get overall song intensity (0.0 to 1.0)"""
        return self.song_intensity
        
    def is_music_active(self) -> bool:
        """Check if music is actively playing (not silence)"""
        return self.current_level > 0.05 or self.song_intensity > 0.1
        
    def get_music_characteristics(self) -> dict:
        """Get comprehensive music analysis"""
        current_time = time.time()
        
        # Periodic frequency spectrum logging
        if current_time - self.last_spectrum_log > 20.0:  # Every 20 seconds
            self.last_spectrum_log = current_time
            freq_bands = self.get_frequency_bands()
            if freq_bands:
                bass = freq_bands.get('bass', 0)
                mid = freq_bands.get('mid', 0)
                treble = freq_bands.get('treble', 0)
                print(f"FREQUENCY ANALYSIS: Bass={bass:.3f} | Mid={mid:.3f} | Treble={treble:.3f} | Overall={self.current_level:.3f}")
        
        return {
            'tempo': self.get_tempo(),
            'energy_trend': self.get_energy_trend(),
            'song_intensity': self.get_song_intensity(),
            'current_level': self.get_audio_level(),
            'is_active': self.is_music_active(),
            'beat_detected': self.detect_beat(),
            'frequency_bands': self.get_frequency_bands(),
            'is_fast_tempo': self.current_tempo > 120,
            'is_building': self.energy_trend > 0.3,
            'is_quiet': self.current_level < 0.1
        }
        
    def stop(self):
        """Stop audio recording and cleanup"""
        if not self._cleaned_up:
            self.is_recording = False
            
            if self.stream:
                self.stream.stop()
                self.stream.close()
                
            if self.processing_thread:
                self.processing_thread.join(timeout=1.0)
                
            self._cleaned_up = True
            print(f"Audio recording stopped (instance {id(self)})")
        
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop()

    def set_input_device(self, device: int | str | None):
        """Change the input device and restart the stream.

        device may be an integer device index, a device name string, or None/'default'.
        This will stop the current stream and restart recording with the new device.
        """
        try:
            # Stop current capture
            self.stop()
        except Exception:
            pass

        # Reset cleaned flag and set new device
        self._cleaned_up = False
        self.input_device = device

        # Start recording again with the new device
        try:
            self._start_recording()
        except Exception as e:
            print(f"Failed to restart audio with device={device}: {e}")