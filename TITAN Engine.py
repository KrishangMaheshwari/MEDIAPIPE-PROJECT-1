import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np
import math
import os
import platform
import subprocess
import random
from fpdf import FPDF
from datetime import datetime
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

# ==============================================================================
#   TITAN X ENGINE - TITAN COMMERCIAL BUILD
#   VERSION: 5.0 (FINAL INTERVIEW RELEASE)
# ==============================================================================

# --- SECTION 1: SYSTEM CORE INITIALIZATION ---
print(">>> SYSTEM BOOT SEQUENCE INITIATED...")
print(">>> LOADING NEURAL NETWORKS...")
print(">>> OPTIMIZING GPU PIPELINES...")

# 1.1 Input Controllers
mouse = MouseController()
keyboard = KeyboardController()
pyautogui.FAILSAFE = False  # Allows full screen control without corner failsafe
pyautogui.PAUSE = 0         # Removes delay for real-time gaming

# 1.2 Computer Vision Configuration
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# We initialize a generic hand model first. 
# Engines will re-optimize this later for specific tasks.
hands = mp_hands.Hands(
    max_num_hands=2, 
    model_complexity=0, 
    min_detection_confidence=0.5, 
    min_tracking_confidence=0.5
)

# 1.3 Display & Camera Setup
cap = cv2.VideoCapture(0)
W, H = 1280, 720
cap.set(3, W)
cap.set(4, H)

# 1.4 Global Engine States
engine_mode = None          # 1=Shooter, 2=Racing, 3=Flight
pTime = 0                   # For FPS calculation
program_running = True

# --- SECTION 2: VISION Z DATA ANALYTICS MODULE ---
# This module handles performance tracking, logging, and PDF generation.

vision_z_active = False
vz_start_time = 0
vz_logs = []

def system_locate_file(file_path):
    """
    OS-Agnostic file locator. Opens the folder containing the generated report.
    """
    path = os.path.abspath(file_path)
    if platform.system() == "Windows":
        subprocess.run(['explorer', '/select,', path])
    elif platform.system() == "Darwin":
        subprocess.run(['open', '-R', path])
    else:
        subprocess.run(['xdg-open', os.path.dirname(path)])

def generate_pdf_report(engine_name):
    """
    Compiles the session logs into a professional PDF report.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_fill_color(10, 10, 30)
        pdf.set_text_color(0, 255, 100)
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(190, 20, f"VISION Z: {engine_name} ANALYTICS", ln=True, align='C', fill=True)
        
        # Subheader
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.ln(10)
        
        # Table Headers
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(50, 50, 50)
        pdf.set_text_color(255, 255, 255)
        
        col_widths = [25, 45, 40, 55, 25]
        headers = ["TIME", "EVENT", "DATA", "MISTAKE", "GAIN"]
        
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 10, h, 1, 0, 'C', True)
        pdf.ln()
        
        # Table Data
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        
        for log in vz_logs:
            for i, item in enumerate(log):
                # Truncate long text to fit cells
                text = str(item)[:20]
                pdf.cell(col_widths[i], 8, text, 1)
            pdf.ln()
            
        filename = f"VisionZ_{engine_name}_{datetime.now().strftime('%H%M%S')}.pdf"
        pdf.output(filename)
        return filename
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return "error.pdf"

def log_vz(event, data, fix, gain):
    """
    Logs an event to the volatile memory if Vision Z is active.
    Does not block the main thread.
    """
    if not vision_z_active: return
    
    elapsed = time.time() - vz_start_time
    ts = f"{int(elapsed//60):02}:{elapsed%60:05.2f}"
    
    # Store log
    vz_logs.append([ts, event, data, fix, gain])
    
    # Keep log size manageable in memory
    if len(vz_logs) > 100:
        vz_logs.pop(0)

def show_vz_report_interface(engine_name):
    """
    Displays the High-Tech Report Interface with 'Encryption' animation.
    Pauses the game loop while active.
    """
    print(">>> ENTERING REPORT INTERFACE...")
    
    while True:
        report_bg = np.zeros((H, W, 3), dtype=np.uint8)
        # Background gradient effect (simple grey fill)
        report_bg[:] = (20, 20, 25)
        
        # Header Graphics
        cv2.rectangle(report_bg, (0, 0), (W, 80), (0, 50, 0), -1)
        cv2.putText(report_bg, f"VISION Z: {engine_name} PERFORMANCE", (50, 55), 1, 2.5, (255, 255, 255), 3)
        
        # Instructions
        cv2.putText(report_bg, "PRESS [9] TO DOWNLOAD PDF REPORT", (50, 130), 1, 1.2, (0, 255, 255), 2)
        cv2.putText(report_bg, "PRESS [ESC] TO RETURN TO GAME", (50, 160), 1, 1.2, (200, 200, 200), 2)
        
        # Display Logs Visualizer
        y_pos = 250
        cols = [50, 200, 450, 800, 1100]
        
        # Headers
        headers = ["TIMESTAMP", "EVENT", "DATA", "REMEDY", "GAIN"]
        for i, h in enumerate(headers):
            cv2.putText(report_bg, h, (cols[i], 220), 1, 1, (100, 100, 255), 2)
            
        # Draw last 12 logs
        for entry in vz_logs[-12:]:
            # Conditional Formatting
            color = (0, 255, 0) # Default Green
            if "Spike" in entry[1] or "Aggressive" in entry[1] or "Miss" in entry[1]:
                color = (0, 0, 255) # Red for bad events
                
            for i, text in enumerate(entry):
                cv2.putText(report_bg, str(text), (cols[i], y_pos), 1, 0.8, color if i==1 else (200,200,200), 1)
            y_pos += 35

        cv2.imshow("TITAN X", report_bg)
        
        # Input Handling for Report Screen
        k = cv2.waitKey(1) & 0xFF
        if k == 27: # ESC
            break
        if k == ord('9'):
            # The "Encryption" Animation
            for i in range(101):
                load_frame = report_bg.copy()
                # Progress Bar
                bar_w = 600
                start_x = W//2 - bar_w//2
                cv2.rectangle(load_frame, (start_x, H//2), (start_x + bar_w, H//2 + 40), (50, 50, 50), -1)
                cv2.rectangle(load_frame, (start_x, H//2), (start_x + int(bar_w * (i/100)), H//2 + 40), (0, 255, 0), -1)
                
                # Tech Text
                cv2.putText(load_frame, f"COMPILING NEURAL DATA: {i}%", (start_x, H//2 - 20), 1, 1.2, (255, 255, 255), 2)
                cv2.imshow("TITAN X", load_frame)
                cv2.waitKey(10)
                
            # Generate and Locate
            fname = generate_pdf_report(engine_name)
            system_locate_file(fname)
            break

# --- SECTION 3: ADVANCED GRAPHICS ENGINE ---

def draw_glass_panel(img, x, y, w, h, title=None, color=(30, 30, 40), alpha=0.6, border_color=(0, 255, 255)):
    """
    Renders a 'Glassomorphism' style UI panel with transparency and neon borders.
    This creates the commercial Sci-Fi look.
    """
    # 1. Create Overlay
    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
    
    # 2. Apply Alpha Blending
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    
    # 3. Draw Neon Corners (Tech Look)
    line_len = 20
    thickness = 2
    # Top-Left
    cv2.line(img, (x, y), (x + line_len, y), border_color, thickness)
    cv2.line(img, (x, y), (x, y + line_len), border_color, thickness)
    # Top-Right
    cv2.line(img, (x + w, y), (x + w - line_len, y), border_color, thickness)
    cv2.line(img, (x + w, y), (x + w, y + line_len), border_color, thickness)
    # Bottom-Left
    cv2.line(img, (x, y + h), (x + line_len, y + h), border_color, thickness)
    cv2.line(img, (x, y + h), (x, y + h - line_len), border_color, thickness)
    # Bottom-Right
    cv2.line(img, (x + w, y + h), (x + w - line_len, y + h), border_color, thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - line_len), border_color, thickness)
    
    # 4. Optional Title
    if title:
        cv2.putText(img, title.upper(), (x + 10, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

def draw_radar(img, cx, cy, radius, angle):
    """
    Draws a rotating radar scanner for the Flight Engine.
    """
    # Radar Background
    draw_glass_panel(img, cx - radius - 10, cy - radius - 10, radius * 2 + 20, radius * 2 + 20, color=(0, 20, 0), alpha=0.3)
    cv2.circle(img, (cx, cy), radius, (0, 100, 0), 1)
    cv2.circle(img, (cx, cy), radius // 2, (0, 100, 0), 1)
    cv2.line(img, (cx - radius, cy), (cx + radius, cy), (0, 50, 0), 1)
    cv2.line(img, (cx, cy - radius), (cx, cy + radius), (0, 50, 0), 1)
    
    # Scanner Line
    end_x = int(cx + radius * math.cos(math.radians(angle)))
    end_y = int(cy + radius * math.sin(math.radians(angle)))
    cv2.line(img, (cx, cy), (end_x, end_y), (0, 255, 0), 2)

# --- SECTION 4: ENGINE LOGIC CONTROLLERS ---

def count_fingers(hand_lms):
    """
    Utilities: Counts extended fingers.
    Returns list [Index, Middle, Ring, Pinky] as 0 or 1.
    """
    fingers = []
    # Tips: 8, 12, 16, 20 | PIPs: 6, 10, 14, 18
    # If Tip Y < PIP Y, finger is UP (assuming camera coordinates where Y increases downwards)
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        if hand_lms.landmark[tip].y < hand_lms.landmark[pip].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

# --- 4.1 SHOOTING ENGINE LOGIC (DUAL JOYSTICK) ---
# Global vars for shooter to maintain state
aim_center_x, aim_center_y = W // 2, H // 2
AIM_DEADZONE = 70       # Center area where cursor doesn't move
AIM_SENSITIVITY = 3.5   # Speed multiplier
is_shooting_state = False

def engine_shooter_update(frame, results):
    """
    Handles Krunker/FPS Logic.
    Left Hand: WASD Joystick
    Right Hand: Aim Joystick + Fist to Shoot
    """
    global is_shooting_state
    status_text = "STANDBY"
    
    # We need hands sorted Left to Right for intuition
    if results.multi_hand_landmarks:
        h_list = sorted(results.multi_hand_landmarks, key=lambda x: x.landmark[9].x)
        
        # --- LEFT HAND: MOVEMENT (WASD) ---
        if len(h_list) > 0:
            lh = h_list[0].landmark
            lx, ly = lh[9].x, lh[9].y
            
            # Visualize Virtual Joystick (Left)
            joy_cx, joy_cy = 200, H - 150
            cv2.circle(frame, (joy_cx, joy_cy), 60, (100, 100, 100), 2)
            # Map hand position to joystick knob
            knob_x = joy_cx + int((lx - 0.25) * 400) 
            knob_y = joy_cy + int((ly - 0.5) * 400)
            # Clamp knob inside visual circle (aesthetic)
            cv2.line(frame, (joy_cx, joy_cy), (knob_x, knob_y), (100, 100, 100), 1)
            cv2.circle(frame, (knob_x, knob_y), 15, (0, 255, 0), -1)

            # Keyboard Logic
            # Y-Axis (Forward/Back)
            if ly < 0.4: keyboard.press('w'); keyboard.release('s')
            elif ly > 0.6: keyboard.press('s'); keyboard.release('w')
            else: keyboard.release('w'); keyboard.release('s')
            
            # X-Axis (Left/Right Strafe)
            if lx < 0.2: keyboard.press('a'); keyboard.release('d')
            elif lx > 0.4: keyboard.press('d'); keyboard.release('a')
            else: keyboard.release('a'); keyboard.release('d')

        # --- RIGHT HAND: AIMING & FIRING ---
        if len(h_list) > 1:
            rh = h_list[1].landmark
            rx, ry = int(rh[9].x * W), int(rh[9].y * H)
            
            # 1. AIMING (Deadzone Logic)
            # Draw Aim Interface
            cv2.circle(frame, (aim_center_x, aim_center_y), AIM_DEADZONE, (50, 50, 50), 1)
            cv2.line(frame, (aim_center_x, aim_center_y), (rx, ry), (0, 255, 255), 1)
            
            dx = rx - aim_center_x
            dy = ry - aim_center_y
            
            move_x, move_y = 0, 0
            
            # X-Axis Aim
            if abs(dx) > AIM_DEADZONE:
                val = dx - (AIM_DEADZONE if dx > 0 else -AIM_DEADZONE)
                move_x = int(val * 0.1 * AIM_SENSITIVITY)
            
            # Y-Axis Aim
            if abs(dy) > AIM_DEADZONE:
                val = dy - (AIM_DEADZONE if dy > 0 else -AIM_DEADZONE)
                move_y = int(val * 0.1 * AIM_SENSITIVITY)
                
            if move_x != 0 or move_y != 0:
                mouse.move(move_x, move_y)
                status_text = "AIMING"
                if vision_z_active and (abs(move_x) > 50 or abs(move_y) > 50):
                     log_vz("Fast Aim", f"dx:{move_x}", "Reduce Sens", "Precision")

            # 2. ACTIONS (Fingers)
            fingers = count_fingers(h_list[1])
            total_fingers = sum(fingers)
            
            # SHOOT: FIST (0 fingers)
            if total_fingers == 0:
                if not is_shooting_state:
                    mouse.press(Button.left)
                    is_shooting_state = True
                    status_text = "FIRING"
                    if vision_z_active: log_vz("Trigger", "Fist Clench", "N/A", "Shot Fired")
                
                # Muzzle Flash Visual
                cv2.circle(frame, (rx, ry), 40, (0, 0, 255), -1)
                cv2.putText(frame, "BANG", (rx-20, ry-50), 1, 1, (0, 0, 255), 2)
            else:
                if is_shooting_state:
                    mouse.release(Button.left)
                    is_shooting_state = False
            
            # RELOAD: OPEN HAND (4 Fingers, Thumb ignored usually)
            if total_fingers >= 4:
                keyboard.press('r')
                time.sleep(0.05)
                keyboard.release('r')
                status_text = "RELOAD"
                draw_glass_panel(frame, W//2-80, H-120, 160, 50, "ACTION", (0,100,0))
                cv2.putText(frame, "RELOADING", (W//2-60, H-90), 1, 1, (255, 255, 255), 2)
                
    return status_text

# --- 4.2 RACING ENGINE LOGIC ---
last_steer_angle = 0

def engine_racing_update(frame, results):
    """
    Handles Racing Logic.
    Steering: Relative angle between hands.
    Nitro: Double Fists.
    Braking: Double 'Peace' Sign (2 fingers).
    """
    global last_steer_angle
    status = "CRUISING"
    
    if not results.multi_hand_landmarks or len(results.multi_hand_landmarks) != 2:
        return "WAITING FOR HANDS..."
        
    # Sort Hands
    h_list = sorted(results.multi_hand_landmarks, key=lambda x: x.landmark[9].x)
    hL, hR = h_list[0], h_list[1]
    
    lx, ly = int(hL.landmark[9].x * W), int(hL.landmark[9].y * H)
    rx, ry = int(hR.landmark[9].x * W), int(hR.landmark[9].y * H)
    
    # 1. STEERING CALCULATIONS
    angle = math.degrees(math.atan2(ry - ly, rx - lx))
    
    # Visualization
    center_x, center_y = (lx + rx) // 2, (ly + ry) // 2
    cv2.line(frame, (lx, ly), (rx, ry), (0, 255, 0), 3)
    cv2.circle(frame, (center_x, center_y), 10, (0, 0, 255), -1)
    
    # Steering Logic
    if angle > 8: # Right
        pyautogui.keyDown('d')
        pyautogui.keyUp('a')
        status = f"RIGHT {int(angle)}°"
    elif angle < -8: # Left
        pyautogui.keyDown('a')
        pyautogui.keyUp('d')
        status = f"LEFT {int(abs(angle))}°"
    else: # Straight
        pyautogui.keyUp('a')
        pyautogui.keyUp('d')
        status = "STRAIGHT"
        
    # Auto-Throttle
    pyautogui.keyDown('w')
    
    # Vision Z Telemetry
    if vision_z_active and abs(angle - last_steer_angle) > 30:
        log_vz("Steer Jerk", f"{int(angle)}deg", "Smooth Hands", "Stability")
    last_steer_angle = angle

    # 2. ACTION RECOGNITION
    f_left = count_fingers(hL)
    f_right = count_fingers(hR)
    sum_l = sum(f_left)
    sum_r = sum(f_right)
    
    # BRAKE: 2 Fingers (Index+Middle) UP on BOTH hands
    # Pattern: [1, 1, 0, 0] roughly
    l_brake_pose = (f_left[0] == 1 and f_left[1] == 1 and f_left[2] == 0)
    r_brake_pose = (f_right[0] == 1 and f_right[1] == 1 and f_right[2] == 0)
    
    if l_brake_pose and r_brake_pose:
        pyautogui.keyUp('w')
        pyautogui.keyDown('down')
        status = "!!! BRAKING !!!"
        
        # Brake Visuals
        draw_glass_panel(frame, W//2 - 200, H//2 - 50, 400, 100, "WARNING", (0, 0, 100))
        cv2.putText(frame, "BRAKES ENGAGED", (W//2 - 180, H//2 + 10), 1, 2, (0, 0, 255), 3)
        if vision_z_active: log_vz("Brake", "Manual Input", "Corner Entry", "Speed Check")
    else:
        pyautogui.keyUp('down')

    # NITRO: DOUBLE FISTS (0 fingers up on both)
    if sum_l == 0 and sum_r == 0:
        pyautogui.press('space')
        status = ">>> NITRO <<<"
        
        # Nitro Visuals
        cv2.circle(frame, (lx, ly), 50, (0, 255, 255), 4)
        cv2.circle(frame, (rx, ry), 50, (0, 255, 255), 4)
        cv2.putText(frame, "NITRO BOOST", (center_x - 100, center_y - 50), 1, 2, (0, 255, 255), 2)
        if vision_z_active: log_vz("Nitro", "Full Boost", "Timing", "Max Speed")

    return status

# --- 4.3 FLIGHT ENGINE LOGIC ---
flight_throttle = 0.0
is_throttle_locked = False
radar_sweep_angle = 0

def engine_flight_update(frame, results):
    """
    Handles Flight Simulation (GeoFS).
    Throttle: Right Hand Height (Lockable).
    Steering: Two Hand Roll/Pitch.
    """
    global flight_throttle, is_throttle_locked, radar_sweep_angle
    
    THROTTLE_X_BOUNDARY = int(W * 0.8)
    status_msg = "AUTOPILOT OFF"
    
    # Draw Division Line
    cv2.line(frame, (THROTTLE_X_BOUNDARY, 0), (THROTTLE_X_BOUNDARY, H), (100, 100, 100), 1)
    
    # 1. IDENTIFY HANDS
    steer_hands = []
    throttle_hand = None
    
    if results.multi_hand_landmarks:
        for h in results.multi_hand_landmarks:
            cx = h.landmark[9].x * W
            if cx > THROTTLE_X_BOUNDARY:
                throttle_hand = h
            else:
                steer_hands.append(h)
                
    # 2. THROTTLE LOGIC (Right Side Zone)
    # UI Box
    draw_glass_panel(frame, THROTTLE_X_BOUNDARY + 10, 50, (W - THROTTLE_X_BOUNDARY - 20), H - 100, "THROTTLE")
    
    # Calculate Target Throttle from Hand Height
    if throttle_hand:
        hy = throttle_hand.landmark[9].y * H
        # Map Y (0 top to H bottom) to Throttle (100% top to 0% bottom)
        # We clamp it between 10% margin
        target_val = np.interp(hy, [100, H-100], [100, 0])
        
        if is_throttle_locked:
            # Just visualize the lock
            flight_throttle = target_val
            cv2.putText(frame, "LOCKED", (THROTTLE_X_BOUNDARY + 20, int(hy)), 1, 1, (0, 255, 255), 2)
            
            # Key Press logic (0-9)
            key_val = str(int(flight_throttle / 10))
            if key_val == '10': key_val = '9'
            pyautogui.press(key_val)
        else:
            # Check for lock condition (Hand held steady near value)
            diff = abs(target_val - flight_throttle)
            cv2.circle(frame, (THROTTLE_X_BOUNDARY + 50, int(hy)), 10, (0, 0, 255), 2)
            if diff < 5.0:
                is_throttle_locked = True # Simple lock trigger
    else:
        is_throttle_locked = False
        
    # Draw Throttle Bar
    bar_h = int(np.interp(flight_throttle, [0, 100], [H-120, 100]))
    cv2.rectangle(frame, (THROTTLE_X_BOUNDARY + 30, bar_h), (W - 50, H - 120), (0, 255, 0), -1)
    cv2.putText(frame, f"{int(flight_throttle)}%", (THROTTLE_X_BOUNDARY + 30, bar_h - 10), 1, 1.5, (255, 255, 255), 2)

    # 3. FLIGHT STICK LOGIC (Steering)
    if len(steer_hands) == 2:
        steer_hands.sort(key=lambda x: x.landmark[9].x)
        hL, hR = steer_hands[0], steer_hands[1]
        
        lx, ly = hL.landmark[9].x * W, hL.landmark[9].y * H
        rx, ry = hR.landmark[9].x * W, hR.landmark[9].y * H
        
        # ROLL (Angle)
        angle = (ry - ly) # simplified vertical delta
        if angle > 30: 
            pyautogui.keyDown('right'); pyautogui.keyUp('left'); status_msg="BANK RIGHT"
        elif angle < -30: 
            pyautogui.keyDown('left'); pyautogui.keyUp('right'); status_msg="BANK LEFT"
        else: 
            pyautogui.keyUp('left'); pyautogui.keyUp('right'); status_msg="WINGS LEVEL"
            
        # PITCH (Wrist vs Fingers) - Simplified for robustness
        # Calculate average height of hands. 
        # High hands = Pitch Down (Push stick). Low hands = Pitch Up (Pull stick).
        avg_y = (ly + ry) / 2
        center_y = H / 2
        
        if avg_y < center_y - 100:
             pyautogui.keyDown('up'); pyautogui.keyUp('down') # Dive
        elif avg_y > center_y + 100:
             pyautogui.keyDown('down'); pyautogui.keyUp('up') # Climb
        else:
             pyautogui.keyUp('down'); pyautogui.keyUp('up')
             
        # Visuals
        cv2.line(frame, (int(lx), int(ly)), (int(rx), int(ry)), (0, 255, 255), 2)

    # 4. RADAR
    draw_radar(frame, 100, H-100, 60, radar_sweep_angle)
    radar_sweep_angle = (radar_sweep_angle + 5) % 360
    
    return status_msg

# ==============================================================================
# 5. MAIN APPLICATION LOOP
# ==============================================================================

print(">>> ENGINE READY. AWAITING USER INPUT...")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("!!! CAMERA FAILURE !!!")
        break
        
    # Flip for Mirror Effect
    frame = cv2.flip(frame, 1)
    
    # --------------------------------------------------------------------------
    # STATE: MENU SELECTION
    # --------------------------------------------------------------------------
    if engine_mode is None:
        # Background Grid Animation
        for x in range(0, W, 100):
            cv2.line(frame, (x, 0), (x, H), (20, 20, 20), 1)
        for y in range(0, H, 100):
            cv2.line(frame, (0, y), (W, y), (20, 20, 20), 1)
            
        # Title
        cv2.putText(frame, "     1TITAN X", (W//2 - 280, 150), 1, 4, (0, 255, 0), 4)
        cv2.putText(frame, "TITAN EDITION v5.0", (W//2 - 120, 200), 1, 1, (150, 150, 150), 1)
        
        # Engine Options
        # Card 1: Shooter
        draw_glass_panel(frame, 150, 300, 300, 250, "SHOOTER [1]", (50, 0, 0))
        cv2.putText(frame, "JOYSTICK AIM", (170, 400), 1, 1.5, (200, 200, 200), 2)
        cv2.putText(frame, "FIST FIRE", (170, 450), 1, 1.5, (200, 200, 200), 2)
        
        # Card 2: Racing
        draw_glass_panel(frame, 500, 300, 300, 250, "RACING [2]", (0, 50, 0))
        cv2.putText(frame, "WHEEL STEER", (520, 400), 1, 1.5, (200, 200, 200), 2)
        cv2.putText(frame, "FIST NITRO", (520, 450), 1, 1.5, (200, 200, 200), 2)
        
        # Card 3: Flight
        draw_glass_panel(frame, 850, 300, 300, 250, "FLIGHT [3]", (0, 0, 50))
        cv2.putText(frame, "RADAR SYS", (870, 400), 1, 1.5, (200, 200, 200), 2)
        cv2.putText(frame, "THROTTLE", (870, 450), 1, 1.5, (200, 200, 200), 2)
        
        cv2.imshow("TITAN X", frame)
        
        # Input Check
        key = cv2.waitKey(1)
        if key == ord('1'): engine_mode = 1; print(">>> ENGINE SELECTED: SHOOTER")
        if key == ord('2'): engine_mode = 2; print(">>> ENGINE SELECTED: RACING")
        if key == ord('3'): engine_mode = 3; print(">>> ENGINE SELECTED: FLIGHT")
        if key == 27: break
        continue

    # --------------------------------------------------------------------------
    # STATE: ACTIVE ENGINE
    # --------------------------------------------------------------------------
    
    # Process Hand Landmarks
    # Note: We convert BGR to RGB for MediaPipe
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    # Calculate FPS
    c_time = time.time()
    fps = 1 / (c_time - pTime) if (c_time - pTime) > 0 else 0
    pTime = c_time
    
    # Draw FPS Panel
    draw_glass_panel(frame, W-180, 20, 160, 60, "PERFORMANCE", (20,20,20))
    cv2.putText(frame, f"FPS: {int(fps)}", (W-160, 60), 1, 1.5, (0, 255, 100), 2)
    
    # Draw Vision Z Recorder Status
    if vision_z_active:
        cv2.circle(frame, (W-40, 40), 10, (0, 0, 255), -1)
        cv2.putText(frame, "REC", (W-90, 45), 1, 1, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "VZ: OFF [0]", (W-120, 45), 1, 0.8, (100, 100, 100), 1)

    # Engine Switch
    current_status = "ACTIVE"
    
    if engine_mode == 1:
        # SHOOTING ENGINE
        current_status = engine_shooter_update(frame, results)
        draw_glass_panel(frame, 20, H-100, 300, 80, "WEAPON SYS")
        cv2.putText(frame, current_status, (40, H-40), 1, 2, (0, 255, 255), 2)
        
    elif engine_mode == 2:
        # RACING ENGINE
        current_status = engine_racing_update(frame, results)
        draw_glass_panel(frame, W//2-150, 20, 300, 80, "ECU MONITOR")
        cv2.putText(frame, current_status, (W//2-130, 70), 1, 1.5, (255, 255, 0), 2)
        
    elif engine_mode == 3:
        # FLIGHT ENGINE
        current_status = engine_flight_update(frame, results)
        draw_glass_panel(frame, 20, 20, 250, 60, "FLIGHT COMPUTER")
        cv2.putText(frame, current_status, (30, 60), 1, 1, (100, 255, 255), 2)

    # Render Frame
    cv2.imshow("TITAN X", frame)

    # Global Keys
    key = cv2.waitKey(1) & 0xFF
    if key == 27: # ESC
        break
    if key == ord('0'): # Toggle Vision Z
        if not vision_z_active:
            vision_z_active = True
            vz_start_time = time.time()
            vz_logs = []
            print(">>> VISION Z RECORDING STARTED")
        else:
            vision_z_active = False
            # Determine engine name for report
            e_name = "SHOOTER" if engine_mode == 1 else "RACING" if engine_mode == 2 else "FLIGHT"
            show_vz_report_interface(e_name)

# --- CLEANUP ---
cap.release()
cv2.destroyAllWindows()
print(">>> SYSTEM SHUTDOWN. GOODBYE.")
