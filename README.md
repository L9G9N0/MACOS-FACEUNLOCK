macOS FaceUnlock (Apple Silicon)
An offline Face Authentication system designed for macOS. Since Apple computers currently lack Infrared (IR) hardware for secure Face ID, this project implements a software-based solution using the standard RGB webcam. It relies on an Active Liveness state machine to prevent spoofing, Euclidean distance matching for identity verification, and a custom Pluggable Authentication Module (PAM) written in C++ to interface with the macOS kernel.

Motivation
Standard 2D facial recognition through an RGB camera is highly vulnerable to spoofing attacks (e.g., using photos or video playback on an iPad). The objective of this project was to build an authentication daemon that operates securely without external hardware or cloud APIs, while maintaining performance on Apple Silicon.

Development Process & Architectural Decisions
Building this system required navigating specific hardware limitations and computer vision constraints. Here is the progression of the architecture:

1. Monocular Depth Estimation (Failed Attempt)
Approach: Used the MiDaS depth-estimation model to calculate the 3D topology of the face using Standard Deviation and Gradient metrics.

Why it failed: High-resolution digital screens display well-lit photos with "baked-in" shadows. The depth model interpreted these 2D shadows as actual 3D structures, leading to false positives during iPad spoofing attacks.

2. Passive Face Anti-Spoofing CNNs (Failed Attempt)
Approach: Transitioned to a Face Anti-Spoofing (FAS) CNN trained to detect Moiré patterns and unnatural screen glare.

Why it failed: The Image Signal Processor (ISP) on Apple's M1 chip aggressively smooths and denoises the raw webcam feed at the hardware level. This hardware-level filtering destroyed the microscopic Moiré patterns, causing severe domain shift and rendering the CNN ineffective.

3. Active Challenge-Response Liveness (Final Implementation)
Approach: Moved to Deterministic 3D Geometry. Using the MediaPipe Tasks API, the daemon extracts the 4x4 Facial Transformation Matrix to calculate real-time Head Yaw (horizontal rotation).

Mechanism: The authentication state machine remains locked until the user physically executes a randomized head-turn challenge. A static photo or a flat digital screen cannot generate a dynamic 3D rotational matrix on demand, making it practically impossible to spoof without real-time 3D rendering.


System Architecture
The project is structured across three core layers:

Layer 1: Vision Daemon (Python)State Machine: To prevent the lockscreen from triggering on a glitchy frame, a 5-Frame Queue Buffer (collections.deque) tracks the liveness state. The system authenticates only if the buffer reaches a 5/5 confidence state, processed in $O(1)$ time.Identity Verification: Extracts a 128-Dimension facial vector using dlib.RAM Caching: To prevent Disk I/O latency and battery drain, the master face profile is read from disk only once during initialization and cached into RAM. Real-time Euclidean distance calculations happen entirely in memory.

Layer 2: Inter-Process Communication (IPC)
UNIX Domain Sockets: The Python user-space daemon communicates with the macOS kernel module via UNIX sockets (.sock), bypassing the TCP/IP stack for microsecond latency.

Layer 3: Pluggable Authentication Module (C++)
Kernel Integration: A custom C++ PAM library (pam_faceunlock.so) is injected into /etc/pam.d/sudo and /etc/pam.d/screensaver.

Fallback Mechanism: Configured with the sufficient PAM flag and a 5-second select() timeout. If the face is not recognized or the daemon is inactive, the system gracefully falls back to the default Apple Touch ID/Password prompt.

Security Constraints
The UNIX socket is fortified against local malicious processes using Defense in Depth:

DAC File Permissions: The socket resides in a hidden directory with strict chmod 700 and chmod 600 permissions.

Kernel Process Validation: The C++ module uses macOS internal libraries (LOCAL_PEERCRED and proc_pidpath) to verify the Process ID (PID) and executable path of the client. Any connection not originating from the verified Python daemon environment is dropped.


Installation & Setup
1. Clone the repository

Bash
git clone https://github.com/YourUsername/macOS-M1-FaceUnlock.git
cd macOS-M1-FaceUnlock

2. Setup the Vision Daemon

Bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

3. Enroll Your Face
Execute the encoder to generate your 128-D vector profile.

Bash
python vision_daemon/core/encoder.py

4. Compile the C++ PAM Module

Bash
cd pam
clang++ -dynamiclib -fPIC -o pam_faceunlock.so pam_faceunlock.cpp -lpam

5. macOS System Integration
Copy the compiled module to the local lib directory and set root permissions.

Bash
sudo mkdir -p /usr/local/lib/pam
sudo cp pam_faceunlock.so /usr/local/lib/pam/
sudo chown root:wheel /usr/local/lib/pam/pam_faceunlock.so
sudo chmod 444 /usr/local/lib/pam/pam_faceunlock.so



Add auth sufficient /usr/local/lib/pam/pam_faceunlock.so to the top of /etc/pam.d/sudo or /etc/pam.d/screensaver


AND THANKS for coming here :::::)))))
