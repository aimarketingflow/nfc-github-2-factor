#!/usr/bin/env python3
"""
Song Recorder - Capture 30-second ambient audio for authentication
Simple recording system for future cryptographic enhancement
"""

import pyaudio
import wave
import time
import os
from datetime import datetime

class SongRecorder:
    """Simple 30-second ambient audio recorder"""
    
    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.record_seconds = 30
        self.output_dir = "recorded_songs"
        
        # Create output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def record_song(self, filename=None):
        """Record 30 seconds of ambient audio"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"song_auth_{timestamp}.wav"
        
        filepath = os.path.join(self.output_dir, filename)
        
        print("=" * 60)
        print("   30-SECOND SONG RECORDER")
        print("=" * 60)
        print(f"\n🎵 Recording ambient audio for authentication")
        print(f"   Duration: {self.record_seconds} seconds")
        print(f"   Sample Rate: {self.rate} Hz")
        print(f"   Output: {filepath}")
        
        # Initialize audio
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print(f"\n🎤 Recording started...")
            print("   Play your authentication song now!")
            
            frames = []
            
            # Record with progress indicator
            for i in range(0, int(self.rate / self.chunk * self.record_seconds)):
                data = stream.read(self.chunk)
                frames.append(data)
                
                # Progress indicator every second
                elapsed = i * self.chunk / self.rate
                if int(elapsed) != int((i-1) * self.chunk / self.rate):
                    remaining = self.record_seconds - elapsed
                    print(f"   ⏱️  {elapsed:.0f}s recorded, {remaining:.0f}s remaining...")
            
            stream.stop_stream()
            stream.close()
            
            print(f"\n✅ Recording complete!")
            
            # Save to WAV file
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
            
            print(f"💾 Saved: {filepath}")
            print(f"📊 File size: {os.path.getsize(filepath)} bytes")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return None
            
        finally:
            audio.terminate()
    
    def list_recordings(self):
        """List all recorded song files"""
        
        print("\n📁 Recorded Songs:")
        print("-" * 40)
        
        if not os.path.exists(self.output_dir):
            print("   No recordings found")
            return []
        
        recordings = []
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.wav'):
                filepath = os.path.join(self.output_dir, filename)
                size = os.path.getsize(filepath)
                mtime = os.path.getmtime(filepath)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"   📄 {filename}")
                print(f"      Size: {size:,} bytes")
                print(f"      Date: {date_str}")
                print()
                
                recordings.append(filepath)
        
        return recordings
    
    def play_recording(self, filepath):
        """Simple playback test (requires additional libraries)"""
        print(f"🔊 To play {filepath}:")
        print(f"   macOS: afplay '{filepath}'")
        print(f"   Linux: aplay '{filepath}'")
        print(f"   Windows: start '{filepath}'")

def main():
    """Interactive song recording interface"""
    
    recorder = SongRecorder()
    
    while True:
        print("\n" + "=" * 50)
        print("   SONG RECORDER MENU")
        print("=" * 50)
        print("1. Record new 30-second song")
        print("2. List recorded songs")
        print("3. Record with custom filename")
        print("4. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            filepath = recorder.record_song()
            if filepath:
                print(f"\n🎉 Successfully recorded authentication song!")
                print(f"   Ready for future cryptographic enhancement")
        
        elif choice == '2':
            recordings = recorder.list_recordings()
            if recordings:
                print(f"\n📊 Total recordings: {len(recordings)}")
        
        elif choice == '3':
            filename = input("Enter filename (without .wav): ").strip()
            if filename:
                if not filename.endswith('.wav'):
                    filename += '.wav'
                filepath = recorder.record_song(filename)
                if filepath:
                    print(f"\n🎉 Successfully recorded: {filename}")
        
        elif choice == '4':
            print("\n👋 Recording session complete!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
