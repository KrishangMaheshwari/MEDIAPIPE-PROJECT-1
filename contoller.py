import cv2
import mediapipe as mp
import pyautogui
import math

# --- System Setup ---
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0 
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.75, model_complexity=1)

cap = cv2.VideoCapture(0)
W, H = 1280, 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

# Settings
SENSITIVITY = 0.5 
DEADZONE = 60
prev_rx = 0 

print("1: RACING | 2: SHOOTING | 3: FLYING | 4: SPORTS")
genre = input("Select Genre: ")

def get_fingers(lms, hand_label):
    # Returns [Thumb, Index, Middle, Ring, Pinky]
    fingers = []
    
    # Thumb Logic (Different for Left/Right hand in Mediapipe)
    if hand_label == "Left":
        fingers.append(1 if lms[4].x > lms[3].x else 0)
    else:
        fingers.append(1 if lms[4].x < lms[3].x else 0)
        
    # Other 4 fingers
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        fingers.append(1 if lms[tip].y < lms[pip].y else 0)
    return fingers

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # UI Anchors
    cv2.circle(frame, (300, 350), DEADZONE, (255, 255, 255), 1) # Movement Center
    cv2.circle(frame, (980, 350), 30, (0, 0, 255), 2)           # Aiming Center
    
    if results.multi_hand_landmarks:
        for i, hand_lms in enumerate(results.multi_hand_landmarks):
            lbl = results.multi_handedness[i].classification[0].label
            lms = hand_lms.landmark
            cx, cy = int(lms[9].x * W), int(lms[9].y * H)
            
            # Get finger states: [Thumb, Index, Middle, Ring, Pinky]
            f = get_fingers(lms, lbl)
            up_count = sum(f[1:]) # Count excluding thumb

            # --- LEFT HAND: KEYBOARD (WASD + UTILITY) ---
            if cx < W // 2:
                lx, ly = 300, 350
                dx, dy = cx - lx, cy - ly
                
                # WASD Movement
                # Forward/Back
                if dy < -DEADZONE: pyautogui.keyDown('w'); pyautogui.keyUp('s')
                elif dy > DEADZONE: pyautogui.keyDown('s'); pyautogui.keyUp('w')
                else: pyautogui.keyUp('w'); pyautogui.keyUp('s')
                
                # Left/Right
                if dx < -DEADZONE: pyautogui.keyDown('a'); pyautogui.keyUp('d')
                elif dx > DEADZONE: pyautogui.keyDown('d'); pyautogui.keyUp('a')
                else: pyautogui.keyUp('a'); pyautogui.keyUp('d')

                # Sprint (Shift) - Hand very high
                if cy < 150: pyautogui.keyDown('shift')
                else: pyautogui.keyUp('shift')

                # Jump (4 fingers up)
                if up_count == 4: pyautogui.press('space')
                
                # Interact (Thumb only)
                if f[0] == 1 and up_count == 0: 
                    pyautogui.press('e')
                    cv2.putText(frame, "INTERACT (E)", (cx, cy-50), 1, 2, (255, 255, 0), 2)

            # --- RIGHT HAND: MOUSE (LOOK + COMBAT) ---
            else:
                rx, ry = 980, 350
                rdx, rdy = cx - rx, cy - ry
                
                # Aiming
                if abs(rdx) > 20 or abs(rdy) > 20:
                    pyautogui.moveRel(rdx * SENSITIVITY, rdy * SENSITIVITY)
                
                # Shoot (2 Fingers: Index + Middle)
                if up_count == 2 and f[1] == 1 and f[2] == 1:
                    pyautogui.click()
                    cv2.putText(frame, "SHOOT", (cx, cy-80), 1, 2, (0, 0, 255), 3)
                
                # Reload (3 Fingers: Index + Middle + Ring)
                elif up_count == 3:
                    pyautogui.press('r')
                    cv2.putText(frame, "RELOAD", (cx, cy-80), 1, 2, (0, 255, 0), 2)
                
                # Scope (Fist)
                if up_count == 0 and f[0] == 0:
                    pyautogui.mouseDown(button='right')
                else:
                    pyautogui.mouseUp(button='right')

            mp.solutions.drawing_utils.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

    # --- THE ALL-IN-ONE HUD ---
    cv2.rectangle(frame, (20, 20), (500, 200), (0, 0, 0), -1)
    cv2.putText(frame, f"UNIVERSAL CTRL: {genre}", (30, 50), 1, 1.5, (0, 255, 0), 2)
    cv2.putText(frame, "L-HAND: WASD Movement | Thumb: E", (30, 85), 1, 1, (255, 255, 255), 1)
    cv2.putText(frame, "R-HAND: Aim | 2-Fing: Shoot | 3-Fing: R", (30, 115), 1, 1, (255, 255, 255), 1)
    cv2.putText(frame, "FIST: Scope (Right Click)", (30, 145), 1, 1, (255, 255, 255), 1)
    cv2.putText(frame, "SPRINT: Move Hand Top | JUMP: 4-Fingers", (30, 175), 1, 1, (255, 255, 255), 1)

    cv2.imshow("Universal Omni-Controller v4.5", frame)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()