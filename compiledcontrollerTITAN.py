import cv2
import mediapipe as mp
import time
import numpy as np
import math
import threading
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

# ==============================================================================
#   TITAN X ENGINE - TITAN COMMERCIAL BUILD (MERGED)
#   VERSION: 7.0 (FULL SUITE)
# ==============================================================================

# --- SECTION 1: SYSTEM CORE INITIALIZATION ---
print(">>> SYSTEM BOOT SEQUENCE INITIATED...")

# 1.1 Input Controllers
mouse = MouseController()
keyboard = KeyboardController()

# 1.2 Computer Vision Configuration
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

# Initialize Models
hands = mp_hands.Hands(max_num_hands=2, model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose = mp_pose.Pose(model_complexity=0, min_detection_confidence=0.5)

# 1.3 Threaded Camera
class WebCamStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

W, H = 1280, 720
vs = WebCamStream(src=0).start()
time.sleep(2.0)

# 1.4 Global States
engine_mode = None          # 1=Shooter, 2=Race(Hand), 3=Flight, 4=Race(Posture)
pTime = 0
current_steer_key = None    # For Lag-Free Posture Steering

# --- SECTION 2: UI & GRAPHICS ---
def draw_glass_panel(img, x, y, w, h, title=None, color=(30, 30, 40), alpha=0.6, border_color=(0, 255, 255)):
    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    
    # Neon Corners
    line_len = 20; thickness = 2
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
    
    if title:
        cv2.putText(img, title.upper(), (x + 10, y + 25), cv2.FONT_HERSHEY_DUPLEX, 0.6, (200, 200, 200), 1)

def draw_radar(img, cx, cy, radius, angle):
    draw_glass_panel(img, cx - radius - 10, cy - radius - 10, radius * 2 + 20, radius * 2 + 20, color=(0, 20, 0), alpha=0.3)
    cv2.circle(img, (cx, cy), radius, (0, 100, 0), 1)
    cv2.circle(img, (cx, cy), radius // 2, (0, 100, 0), 1)
    
    end_x = int(cx + radius * math.cos(math.radians(angle)))
    end_y = int(cy + radius * math.sin(math.radians(angle)))
    cv2.line(img, (cx, cy), (end_x, end_y), (0, 255, 0), 2)

def count_fingers(hand_lms):
    fingers = []
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        fingers.append(1 if hand_lms.landmark[tip].y < hand_lms.landmark[pip].y else 0)
    return fingers

# --- SECTION 3: ENGINE LOGIC CONTROLLERS ---

# 3.1 SHOOTER (Hands)
aim_center_x, aim_center_y = W // 2, H // 2
is_shooting_state = False

def engine_shooter_update(frame, hand_results):
    global is_shooting_state
    status_text = "STANDBY"
    
    if hand_results.multi_hand_landmarks:
        h_list = sorted(hand_results.multi_hand_landmarks, key=lambda x: x.landmark[9].x)
        
        # Left Hand (Movement)
        if len(h_list) > 0:
            lh = h_list[0].landmark
            ly, lx = lh[9].y, lh[9].x
            
            # WASD Logic
            if ly < 0.4: keyboard.press('w'); keyboard.release('s')
            elif ly > 0.6: keyboard.press('s'); keyboard.release('w')
            else: keyboard.release('w'); keyboard.release('s')
            
            if lx < 0.2: keyboard.press('a'); keyboard.release('d')
            elif lx > 0.4: keyboard.press('d'); keyboard.release('a')
            else: keyboard.release('a'); keyboard.release('d')

        # Right Hand (Aim)
        if len(h_list) > 1:
            rh = h_list[1].landmark
            rx, ry = int(rh[9].x * W), int(rh[9].y * H)
            cv2.circle(frame, (rx, ry), 20, (0, 255, 255), 1)
            
            dx, dy = rx - aim_center_x, ry - aim_center_y
            if abs(dx) > 60 or abs(dy) > 60:
                mouse.move(int(dx*0.2), int(dy*0.2))
                status_text = "AIMING"

            # Fire (Fist)
            if sum(count_fingers(h_list[1])) == 0:
                if not is_shooting_state: mouse.press(Button.left); is_shooting_state = True
                status_text = "FIRING"
                cv2.circle(frame, (rx, ry), 40, (0, 0, 255), -1)
            else:
                if is_shooting_state: mouse.release(Button.left); is_shooting_state = False

    return status_text

# 3.2 RACING (Hands)
def engine_racing_hands(frame, hand_results):
    status = "CRUISING"
    if not hand_results.multi_hand_landmarks or len(hand_results.multi_hand_landmarks) != 2:
        return "WAITING FOR HANDS"
        
    h_list = sorted(hand_results.multi_hand_landmarks, key=lambda x: x.landmark[9].x)
    hL, hR = h_list[0], h_list[1]
    lx, ly = int(hL.landmark[9].x * W), int(hL.landmark[9].y * H)
    rx, ry = int(hR.landmark[9].x * W), int(hR.landmark[9].y * H)
    
    angle = math.degrees(math.atan2(ry - ly, rx - lx))
    cv2.line(frame, (lx, ly), (rx, ry), (0, 255, 0), 3)

    if angle > 10: keyboard.press('d'); keyboard.release('a'); status="RIGHT"
    elif angle < -10: keyboard.press('a'); keyboard.release('d'); status="LEFT"
    else: keyboard.release('a'); keyboard.release('d'); status="STRAIGHT"
    
    keyboard.press('w') # Auto Gas
    if sum(count_fingers(hL)) == 0 and sum(count_fingers(hR)) == 0:
        keyboard.press(Key.space); status="NITRO"
    else: keyboard.release(Key.space)
        
    return status

# 3.3 RACING (Posture)
def engine_racing_posture(frame, pose_results):
    global current_steer_key
    status = "NEUTRAL"
    DEADZONE = 0.02
    
    if pose_results.pose_landmarks:
        lms = pose_results.pose_landmarks.landmark
        nose = lms[mp_pose.PoseLandmark.NOSE]
        l_sh = lms[mp_pose.PoseLandmark.LEFT_SHOULDER]
        r_sh = lms[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        l_wrist = lms[mp_pose.PoseLandmark.LEFT_WRIST]
        
        diff = nose.x - ((l_sh.x + r_sh.x) / 2)
        
        # Steering
        if diff < -DEADZONE:
            if current_steer_key != 'a': keyboard.release('d'); keyboard.press('a'); current_steer_key = 'a'
            status = "STEER LEFT"
        elif diff > DEADZONE:
            if current_steer_key != 'd': keyboard.release('a'); keyboard.press('d'); current_steer_key = 'd'
            status = "STEER RIGHT"
        else:
            if current_steer_key: keyboard.release('a'); keyboard.release('d'); current_steer_key = None
            status = "CENTERED"
            
        # Brake
        if l_wrist.y < l_sh.y: keyboard.press('s'); status = "BRAKING"
        else: keyboard.release('s')
        
        mp_draw.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        # Visual Slider
        cx = W // 2
        tx = int(cx + (diff * 1000))
        draw_glass_panel(frame, cx - 200, H - 100, 400, 50, "NECK AXIS")
        cv2.circle(frame, (tx, H - 75), 10, (0, 255, 255), -1)
        
    return status

# 3.4 FLIGHT (Hands)
flight_throttle = 0.0
radar_angle = 0

def engine_flight_update(frame, hand_results):
    global flight_throttle, radar_angle
    status = "AUTOPILOT OFF"
    THROTTLE_X = int(W * 0.8)
    
    # UI Division
    cv2.line(frame, (THROTTLE_X, 0), (THROTTLE_X, H), (100, 100, 100), 1)
    draw_glass_panel(frame, THROTTLE_X + 10, 50, (W - THROTTLE_X - 20), H - 100, "THROTTLE")
    
    # Identify Hands
    steer_hands = []
    throttle_hand = None
    
    if hand_results.multi_hand_landmarks:
        for h in hand_results.multi_hand_landmarks:
            if h.landmark[9].x * W > THROTTLE_X: throttle_hand = h
            else: steer_hands.append(h)
            
    # Throttle Logic (Right Zone)
    if throttle_hand:
        hy = throttle_hand.landmark[9].y * H
        flight_throttle = np.interp(hy, [100, H-100], [100, 0])
        # Send key 0-9
        k_val = str(int(flight_throttle / 10))
        if k_val == '10': k_val = '9'
        keyboard.press(k_val); keyboard.release(k_val)
        
    # Draw Throttle Bar
    bar_h = int(np.interp(flight_throttle, [0, 100], [H-120, 100]))
    cv2.rectangle(frame, (THROTTLE_X + 40, bar_h), (W - 40, H - 120), (0, 255, 0), -1)
    cv2.putText(frame, f"{int(flight_throttle)}%", (THROTTLE_X + 40, bar_h - 10), 1, 1, (255, 255, 255), 1)

    # Stick Logic (Left Zone)
    if len(steer_hands) == 2:
        steer_hands.sort(key=lambda x: x.landmark[9].x)
        hL, hR = steer_hands[0], steer_hands[1]
        ly, ry = hL.landmark[9].y * H, hR.landmark[9].y * H
        
        # Bank (Roll)
        roll = ry - ly
        if roll > 30: keyboard.press(Key.right); keyboard.release(Key.left); status="BANK RIGHT"
        elif roll < -30: keyboard.press(Key.left); keyboard.release(Key.right); status="BANK LEFT"
        else: keyboard.release(Key.left); keyboard.release(Key.right)
        
        # Pitch (Height)
        avg_y = (ly + ry) / 2
        if avg_y < H/2 - 100: keyboard.press(Key.up); keyboard.release(Key.down); status="DIVE"
        elif avg_y > H/2 + 100: keyboard.press(Key.down); keyboard.release(Key.up); status="CLIMB"
        else: keyboard.release(Key.up); keyboard.release(Key.down)
        
        cv2.line(frame, (int(hL.landmark[9].x*W), int(ly)), (int(hR.landmark[9].x*W), int(ry)), (0, 255, 255), 2)

    # Radar
    draw_radar(frame, 100, H-100, 60, radar_angle)
    radar_angle = (radar_angle + 5) % 360
    
    return status

# ==============================================================================
# 5. MAIN LOOP
# ==============================================================================

while True:
    frame = vs.read()
    if frame is None: continue
    frame = cv2.flip(frame, 1)
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # --- MENU ---
    if engine_mode is None:
        draw_glass_panel(frame, 0, 0, W, H, color=(10,10,15), alpha=0.9)
        cv2.putText(frame, "TITAN X ENGINE", (W//2 - 240, 150), 1, 3.5, (0, 255, 0), 3)
        cv2.putText(frame, "FULL SUITE v7.0", (W//2 - 120, 200), 1, 1, (150, 150, 150), 1)
        
        # Option Cards
        draw_glass_panel(frame, 80, 300, 250, 200, "SHOOTER [1]", (50, 20, 20))
        draw_glass_panel(frame, 360, 300, 250, 200, "RACE HANDS [2]", (20, 50, 20))
        draw_glass_panel(frame, 640, 300, 250, 200, "FLIGHT [3]", (20, 20, 50))
        draw_glass_panel(frame, 920, 300, 250, 200, "POSTURE [4]", (50, 50, 0))
        
        cv2.imshow("TITAN X", frame)
        k = cv2.waitKey(1)
        if k == ord('1'): engine_mode = 1
        if k == ord('2'): engine_mode = 2
        if k == ord('3'): engine_mode = 3
        if k == ord('4'): engine_mode = 4
        if k == 27: break
        continue

    # --- ENGINE ACTIVE ---
    hand_results = None
    pose_results = None
    
    # Process necessary models
    if engine_mode in [1, 2, 3]: hand_results = hands.process(img_rgb)
    if engine_mode == 4: pose_results = pose.process(img_rgb)
    
    # FPS
    c_time = time.time()
    fps = 1 / (c_time - pTime) if (c_time - pTime) > 0 else 0
    pTime = c_time
    draw_glass_panel(frame, W-150, 20, 130, 50, "FPS", (0,0,0))
    cv2.putText(frame, str(int(fps)), (W-100, 55), 1, 1.5, (0, 255, 100), 2)
    
    msg = ""
    if engine_mode == 1: msg = engine_shooter_update(frame, hand_results)
    elif engine_mode == 2: msg = engine_racing_hands(frame, hand_results)
    elif engine_mode == 3: msg = engine_flight_update(frame, hand_results)
    elif engine_mode == 4: msg = engine_racing_posture(frame, pose_results)
    
    cv2.putText(frame, msg, (W//2 - 100, 60), 1, 1.5, (255, 255, 0), 2)
    cv2.imshow("TITAN X", frame)

    # ESC to Menu
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        engine_mode = None
        for key in ['w','a','s','d', Key.space, Key.up, Key.down, Key.left, Key.right]:
            keyboard.release(key)
        if current_steer_key: keyboard.release(current_steer_key); current_steer_key = None

vs.stop()
cv2.destroyAllWindows()
print(">>> SHUTDOWN.")