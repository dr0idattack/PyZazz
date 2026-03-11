import os
import subprocess
import time
import signal
from typing import Optional

class VideoController:
    def __init__(self):
        self.video_process = None
        self.current_video = None
        self._cleaned_up = False
         
            
    def play_video(self, video_path: str, fullscreen_display: int = 2) -> bool:
        """Play a video file using ffplay with optimized startup"""
        start_time = time.time()
        print(f"VIDEO: Attempting to play video: {video_path}")
        print(f"VIDEO: Fullscreen display: {fullscreen_display}")
        
        if not video_path or not os.path.exists(video_path):
            print(f"VIDEO: File not found: {video_path}")
            return False
            
        # Quick validation of video file (optimized - skip size check for speed)
        if not self._is_valid_video_file_fast(video_path):
            print(f"VIDEO: Invalid video file format: {video_path}")
            return False
        
        validation_time = time.time()
        print(f"VIDEO TIMING: File validation took {validation_time - start_time:.3f}s")
        
        # Stop any existing video first - but do it asynchronously
        self._stop_async()
            
        try:
            print(f"VIDEO: Starting ffplay: {os.path.basename(video_path)}")
            
            # Get display positioning for external display
            display_pos_start = time.time()
            x_pos, y_pos = self._get_display_position(fullscreen_display)
            display_pos_time = time.time()
            print(f"VIDEO TIMING: Display position calculation took {display_pos_time - display_pos_start:.3f}s")
            
            # Build ffplay command optimized for INSTANT startup
            ffplay_cmd = [
                'ffplay',
                '-loop', '0',  # Loop infinitely
                '-fs',         # Start in fullscreen
                '-left', str(x_pos),
                '-top', str(y_pos),
                '-noborder',   # No window border
                '-alwaysontop', # Keep on top
                '-an',         # Disable audio (since we're using audio analyzer)
                '-loglevel', 'quiet',  # Suppress ffplay output
                
                # AGGRESSIVE startup optimization - skip all analysis
                '-probesize', '32',           # Tiny probe size 
                '-analyzeduration', '0',      # No analysis at all
                '-fflags', '+fastseek+genpts+igndts',  # Fast seeking + ignore DTS issues
                '-flags', '+low_delay',       # Low delay mode
                '-threads', '1',              # Single thread for faster startup
                '-sync', 'ext',               # External sync (fastest)
                '-framedrop',                 # Drop frames if needed for performance
                '-infbuf',                    # Infinite buffer to prevent stalling
                
                # Video codec optimizations for instant playback
                '-vf', 'scale=flags=fast_bilinear',  # Fast scaling
                '-sws_flags', 'fast_bilinear',       # Fast software scaling
                '-lowres', '0',                      # No resolution reduction
                
                video_path
            ]
            
            # Start ffplay process with timing
            process_start_time = time.time()
            
            self.video_process = subprocess.Popen(
                ffplay_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new process group
            )
            
            process_created_time = time.time()
            print(f"VIDEO TIMING: Process creation took {process_created_time - process_start_time:.3f}s")
            
            self.current_video = video_path
            
            # Verify process started successfully
            if self.video_process.poll() is None:
                total_time = time.time() - start_time
                print(f"VIDEO: ffplay started successfully: {os.path.basename(video_path)}")
                print(f"VIDEO TIMING: Total startup time: {total_time:.3f}s")
                return True
            else:
                print(f"VIDEO: ffplay failed to start")
                self.video_process = None
                return False
            
        except Exception as e:
            print(f"VIDEO: Failed to start ffplay: {e}")
            self.video_process = None
            return False
    
    def _get_display_position(self, display_number: int) -> tuple:
        """Get x,y position for the specified display - optimized for speed"""
        if display_number <= 1:
            return (0, 0)
        
        # Position external display to the right of primary display
        # Primary display is 1512x982 (scaled), so external starts at x=1512
        return (1512, 0)  # Position external display at right edge of primary
     
     
    def _is_valid_video_file(self, video_path: str) -> bool:
        """Quick validation of video file format and basic integrity"""
        try:
            # Check file extension
            valid_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.wmv', '.flv', '.webm', '.mpg', '.mpeg'}
            file_ext = os.path.splitext(video_path.lower())[1]
            
            if file_ext not in valid_extensions:
                return False
                
            # Basic file size check (should be > 1KB)
            file_size = os.path.getsize(video_path)
            if file_size < 1024:
                return False
                
            return True
            
        except Exception as e:
            print(f"Error validating video file: {e}")
            return False
    
    def _is_valid_video_file_fast(self, video_path: str) -> bool:
        """Ultra-fast validation - extension only for instant startup"""
        try:
            valid_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.wmv', '.flv', '.webm', '.mpg', '.mpeg'}
            file_ext = os.path.splitext(video_path.lower())[1]
            return file_ext in valid_extensions
        except:
            return False
    
    def _stop_async(self):
        """Stop existing video asynchronously to avoid blocking"""
        if self.video_process:
            try:
                # Kill immediately without waiting
                os.killpg(os.getpgid(self.video_process.pid), signal.SIGKILL)
                self.video_process = None
            except (ProcessLookupError, AttributeError):
                self.video_process = None
            except Exception:
                # Ignore errors - we want to start the new video quickly
                self.video_process = None
    
    
    
    
    
    
    def ensure_video_looping(self) -> bool:
        """ffplay loops automatically with -loop 0"""
        return True  # ffplay is started with -loop 0
    
    
    
            
    def stop(self):
        """Stop ffplay video playback"""
        if not self._cleaned_up:
            if self.video_process:
                try:
                    # Send SIGTERM to the process group
                    os.killpg(os.getpgid(self.video_process.pid), signal.SIGTERM)
                    
                    # Wait for process to terminate
                    try:
                        self.video_process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't respond
                        os.killpg(os.getpgid(self.video_process.pid), signal.SIGKILL)
                        self.video_process.wait()
                        
                except ProcessLookupError:
                    # Process already terminated
                    pass
                except Exception as e:
                    print(f"Warning: Error stopping video process: {e}")
                finally:
                    self.video_process = None
            
            # Also kill any remaining ffplay processes as fallback
            try:
                subprocess.run(['pkill', '-f', 'ffplay'], 
                             capture_output=True, text=True, timeout=2)
            except:
                pass
                
            self.current_video = None
            print("Video playback stopped")
            
    def pause(self):
        """Pause video playback (ffplay doesn't easily support pause)"""
        print("Warning: ffplay doesn't support pause/resume. Use stop() and play_video() instead.")
            
    def resume(self):
        """Resume video playback (ffplay doesn't easily support resume)"""
        print("Warning: ffplay doesn't support pause/resume. Use stop() and play_video() instead.")
            
    def is_playing(self) -> bool:
        """Check if ffplay process is running"""
        return self.video_process is not None and self.video_process.poll() is None
        
    def is_paused(self) -> bool:
        """Check if video is currently paused"""
        # For subprocess approach, we'll assume not paused if playing
        return self.video_process is not None and not self.is_playing()
        
    def set_volume(self, volume: int):
        """Volume control not supported with ffplay -an (audio disabled)"""
        print("Warning: Volume control not available when using ffplay with -an (audio disabled)")
            
    def get_volume(self) -> int:
        """Volume control not supported with ffplay -an (audio disabled)"""
        return 0
        
    def set_position(self, position: float):
        """Position control not easily supported with ffplay"""
        print("Warning: Position control not supported with current ffplay implementation")
            
    def get_position(self) -> float:
        """Position control not easily supported with ffplay"""
        return 0.0
        
    def get_length(self) -> int:
        """Length info not easily supported with ffplay"""
        return 0
        
    def get_time(self) -> int:
        """Time info not easily supported with ffplay"""
        return 0
        
    def set_fullscreen(self, fullscreen: bool):
        """Fullscreen is set at startup with ffplay -fs"""
        print("Warning: Fullscreen is set at startup with ffplay. Restart video to change.")
            
    def toggle_fullscreen(self):
        """Fullscreen is set at startup with ffplay -fs"""
        print("Warning: Fullscreen is set at startup with ffplay. Restart video to change.")
            
    def get_current_video(self) -> Optional[str]:
        """Get path of currently loaded video"""
        return self.current_video
        
    def quit_video(self):
        """Stop ffplay video playback"""
        self.stop()
            
    def cleanup(self):
        """Clean up video resources"""
        if not self._cleaned_up:
            self._cleaned_up = True  # Set flag before calling stop to prevent message
            self.stop()
            print("Video resources cleaned up")
        
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup()
        
    @staticmethod
    def get_supported_formats() -> list:
        """Get list of supported video formats"""
        return [
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', 
            '.webm', '.m4v', '.3gp', '.mpg', '.mpeg'
        ]
        