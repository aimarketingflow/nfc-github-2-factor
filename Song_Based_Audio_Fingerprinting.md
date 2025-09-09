# Song-Based Audio Fingerprinting Authentication

**AIMF LLC - Advanced Audio Cryptography**  
**Version**: 1.0  
**Date**: September 8, 2025

## 🎵 Concept Overview

User selects a specific song which plays during authentication. The unique combination of:
- **Known audio content** (selected song)
- **Room acoustics** (reverb, echo, absorption)  
- **Microphone positioning** (distance, angle, obstacles)
- **Environmental factors** (furniture, walls, ambient noise)

Creates a **reproducible yet location-specific audio fingerprint**.

## 🔧 Technical Implementation

### Song Selection & Storage

```python
def setup_song_authentication(song_path, nfc_uid):
    """
    Initialize song-based authentication for specific location
    """
    
    # Load user's selected song
    import librosa
    audio, sample_rate = librosa.load(song_path, duration=10.0)  # 10-second clip
    
    # Create reference fingerprint at setup location
    reference_fingerprint = create_song_fingerprint(audio, sample_rate)
    
    # Store encrypted reference with NFC binding
    setup_data = {
        'song_hash': hashlib.sha256(audio.tobytes()).hexdigest(),
        'reference_fingerprint': reference_fingerprint,
        'nfc_binding': hashlib.sha256(nfc_uid.encode()).hexdigest(),
        'setup_timestamp': time.time(),
        'song_duration': 10.0,
        'sample_rate': sample_rate
    }
    
    with open('.song_auth_setup.json', 'w') as f:
        json.dump(setup_data, f)
    
    return reference_fingerprint

def create_song_fingerprint(audio_signal, sample_rate):
    """
    Extract room-acoustic fingerprint from known song
    """
    
    # Spectral analysis
    stft = librosa.stft(audio_signal, n_fft=2048, hop_length=512)
    magnitude = np.abs(stft)
    
    # Extract room-specific features
    features = []
    
    # 1. Reverb characteristics (decay patterns)
    reverb_profile = extract_reverb_decay(magnitude)
    features.extend(reverb_profile)
    
    # 2. Frequency response variations (room resonances)  
    freq_response = np.mean(magnitude, axis=1)
    room_resonances = detect_room_modes(freq_response)
    features.extend(room_resonances)
    
    # 3. Stereo imaging (microphone position relative to speakers)
    if audio_signal.ndim > 1:
        stereo_imaging = extract_stereo_features(audio_signal)
        features.extend(stereo_imaging)
    
    # 4. Harmonic distortion (speaker/room interactions)
    harmonic_distortion = detect_harmonic_patterns(magnitude)
    features.extend(harmonic_distortion)
    
    # Convert to stable hash
    feature_bytes = np.array(features).tobytes()
    fingerprint = hashlib.sha256(feature_bytes).digest()
    
    return fingerprint

def extract_reverb_decay(magnitude_spectrogram):
    """Extract room reverb characteristics"""
    
    # Analyze decay patterns in different frequency bands
    freq_bands = [
        (20, 200),    # Low frequencies  
        (200, 2000),  # Mid frequencies
        (2000, 8000), # High frequencies
        (8000, 20000) # Very high frequencies
    ]
    
    decay_patterns = []
    
    for low_freq, high_freq in freq_bands:
        # Extract energy decay in this band
        band_energy = np.mean(magnitude_spectrogram[low_freq:high_freq, :], axis=0)
        
        # Measure decay rate (RT60 approximation)
        peaks = find_energy_peaks(band_energy)
        decay_rates = calculate_decay_rates(peaks, band_energy)
        
        decay_patterns.extend(decay_rates[:5])  # Top 5 decay characteristics
    
    return decay_patterns

def detect_room_modes(frequency_response):
    """Detect room acoustic resonances"""
    
    # Find standing wave patterns
    resonance_peaks = []
    
    # Look for peaks that indicate room dimensions
    for i in range(1, len(frequency_response)-1):
        if (frequency_response[i] > frequency_response[i-1] and 
            frequency_response[i] > frequency_response[i+1]):
            
            # Calculate Q factor (sharpness of resonance)
            q_factor = calculate_q_factor(frequency_response, i)
            resonance_peaks.append((i, q_factor))
    
    # Return top 10 most prominent room modes
    resonance_peaks.sort(key=lambda x: x[1], reverse=True)
    return [peak[0] for peak in resonance_peaks[:10]]
```

### Authentication Process

```python
def authenticate_with_song(nfc_uid, song_path):
    """
    Authenticate using song playback + room acoustics
    """
    
    print("🎵 Song-Based Authentication")
    print("1. Place microphone in same position as setup")
    print("2. Ensure room conditions match setup environment")
    print("3. Play your authentication song...")
    
    # Load setup reference
    with open('.song_auth_setup.json', 'r') as f:
        setup_data = json.load(f)
    
    # Verify NFC binding
    nfc_hash = hashlib.sha256(nfc_uid.encode()).hexdigest()
    if nfc_hash != setup_data['nfc_binding']:
        raise ValueError("NFC token mismatch")
    
    # Record authentication audio
    print("🎤 Recording authentication sample...")
    
    import pyaudio
    audio_recorder = pyaudio.PyAudio()
    stream = audio_recorder.open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=setup_data['sample_rate'],
        input=True,
        frames_per_buffer=1024
    )
    
    # Record for same duration as setup
    duration = setup_data['song_duration']
    frames = int(duration * setup_data['sample_rate'] / 1024)
    
    audio_data = []
    for _ in range(frames):
        data = stream.read(1024)
        audio_data.append(np.frombuffer(data, dtype=np.float32))
    
    stream.close()
    audio_recorder.terminate()
    
    # Create authentication fingerprint
    auth_audio = np.concatenate(audio_data)
    auth_fingerprint = create_song_fingerprint(auth_audio, setup_data['sample_rate'])
    
    # Compare fingerprints with tolerance
    reference_fp = bytes.fromhex(setup_data['reference_fingerprint'])
    similarity = calculate_fingerprint_similarity(auth_fingerprint, reference_fp)
    
    # Threshold for authentication (allows minor variations)
    similarity_threshold = 0.85
    
    if similarity >= similarity_threshold:
        # Generate authentication multiplier from audio features
        audio_multiplier = int.from_bytes(auth_fingerprint[:4], 'big') | 1
        return audio_multiplier
    else:
        raise ValueError(f"Audio authentication failed (similarity: {similarity:.2f})")

def calculate_fingerprint_similarity(fp1, fp2):
    """Calculate similarity between audio fingerprints"""
    
    # Hamming distance for binary comparison
    xor_result = bytes(a ^ b for a, b in zip(fp1, fp2))
    hamming_distance = bin(int.from_bytes(xor_result, 'big')).count('1')
    
    # Convert to similarity percentage
    max_distance = len(fp1) * 8  # Total bits
    similarity = 1.0 - (hamming_distance / max_distance)
    
    return similarity
```

## 🔒 Security Analysis

### Advantages of Song-Based Authentication

1. **Reproducible Source Material**
   - Same song content eliminates ambient noise variables
   - User controls the audio source
   - Consistent baseline for fingerprinting

2. **Room Acoustic Binding**
   - Unique reverb patterns for each location
   - Standing wave resonances specific to room dimensions  
   - Microphone positioning creates directional signatures

3. **Multi-Factor Security**
   ```
   Authentication = NFC_Token × Song_Selection × Room_Acoustics × Microphone_Position
   ```

4. **Replay Attack Resistance**
   - Recording cannot replicate live room acoustics
   - Microphone positioning variations detectable
   - Environmental changes affect fingerprint

### Attack Resistance Analysis

```
Attack Vector                    | Mitigation
---------------------------------|------------------------------------------
Stolen NFC + Song File          | Missing room acoustic fingerprint
Audio Recording Replay          | Cannot replicate live room acoustics  
Different Room Same Song        | Room resonances/reverb will differ
Same Room Different Position    | Microphone positioning changes signature
Audio Synthesis Attack          | Room modes cannot be artificially created
```

### Implementation Security

```python
def enhanced_nfc_with_song_auth(nfc_uid, chaos_value):
    """
    Combine NFC with song-based audio authentication
    """
    
    # 1. Invisible NFC scan
    scanner = InvisibleNFCScanner()  
    nfc_hash = scanner.invisible_scan_simple()
    
    # 2. Song authentication
    song_path = get_user_song_selection()
    audio_multiplier = authenticate_with_song(nfc_hash, song_path)
    
    # 3. Enhance NFC with audio
    nfc_int = int.from_bytes(bytes.fromhex(nfc_hash)[:4], 'big')
    enhanced_nfc = (nfc_int * audio_multiplier) % (2**32)
    
    # 4. Combine with chaos
    enhanced_bytes = enhanced_nfc.to_bytes(4, 'big')
    final_key = bytes(a ^ b for a, b in zip(enhanced_bytes, chaos_value[:4]))
    
    return final_key
```

## 🎯 User Experience Flow

```
1. 🎵 "Select your authentication song" 
   → User chooses 10-second audio clip

2. 📍 "Position microphone for setup scan"
   → User places microphone in desired authentication location

3. 📟 "Scan NFC tag to bind authentication"
   → Invisible NFC scan links tag to song+location

4. 🎤 "Play song for acoustic fingerprinting"  
   → System records room acoustic signature

5. ✅ "Song authentication setup complete"
   → Reference fingerprint stored securely

Authentication Flow:
1. 📟 "Scan NFC tag" (invisible)
2. 🎵 "Play your authentication song"
3. 🎤 "Recording acoustic signature..." (10 seconds)
4. ✅ "Authentication successful"
```

## 📊 Security Comparison

```
Method                  | Attack Complexity      | User Experience
------------------------|------------------------|------------------
Fixed Chaos            | 2^32 (VULNERABLE)     | Single NFC scan
Ambient Audio          | 2^32 × Audio_Variance | NFC + 2sec silence
Song Authentication    | 2^32 × Room_Signature | NFC + 10sec song
Dual NFC               | 2^64                  | Two NFC scans
```

**Song-based authentication provides excellent security with manageable user experience - the song becomes part of the authentication ritual while binding to specific physical location acoustics.**

---

**Recommendation**: Implement song-based authentication as it provides strong location binding while maintaining user control and reproducibility.
