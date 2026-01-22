import cv2
import mediapipe as mp
import time
import threading
from pynput.keyboard import Key, Controller

# --- Initialize Mac Keyboard Controller ---
keyboard = Controller()

# --- Configuration ---
SENSITIVITY = 0.10  # Lower = more sensitive
DEADZONE = 0.02     # Range where steering stays centered
current_key = None  # Tracks if 'a' or 'd' is currently held

# --- Threaded Camera Class ---
class WebCamStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
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

# --- Setup MediaPipe ---
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
pose = mp_pose.Pose(model_complexity=0, min_detection_confidence=0.5)
hands = mp_hands.Hands(model_complexity=0, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Start Stream
vs = WebCamStream(src=0).start()
time.sleep(2.0)

prev_frame_time = 0
quit_timer_start = None

while True:
    frame = vs.read()
    if frame is None: continue

    # 1. Calculate FPS
    new_frame_time = time.time()
    fps = 1 / (max(new_frame_time - prev_frame_time, 0.001))
    prev_frame_time = new_frame_time

    # 2. Prep frame
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process models
    pose_results = pose.process(rgb_frame)
    hand_results = hands.process(rgb_frame)

    active_inputs = []
    quit_gesture_active = False

    # --- HAND LOGIC: Peace Sign to Quit ---
    if hand_results.multi_hand_landmarks:
        for hand_lms in hand_results.multi_hand_landmarks:
            index_up = hand_lms.landmark[8].y < hand_lms.landmark[6].y
            middle_up = hand_lms.landmark[12].y < hand_lms.landmark[10].y
            ring_down = hand_lms.landmark[16].y > hand_lms.landmark[14].y
            pinky_down = hand_lms.landmark[20].y > hand_lms.landmark[18].y

            if index_up and middle_up and ring_down and pinky_down:
                quit_gesture_active = True
                mp_drawing.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

    # --- QUIT TIMER ---
    if quit_gesture_active:
        if quit_timer_start is None:
            quit_timer_start = time.time()
        elapsed = time.time() - quit_timer_start
        active_inputs.append(f"QUITTING IN {max(0, 3 - int(elapsed))}s")
        if elapsed >= 3:
            break
    else:
        quit_timer_start = None

    # --- POSE LOGIC (Steering & Braking) ---
    if pose_results.pose_landmarks and not quit_gesture_active:
        lms = pose_results.pose_landmarks.landmark
        nose = lms[mp_pose.PoseLandmark.NOSE]
        l_shldr = lms[mp_pose.PoseLandmark.LEFT_SHOULDER]
        r_shldr = lms[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        l_wrist = lms[mp_pose.PoseLandmark.LEFT_WRIST]

        shldr_x = (l_shldr.x + r_shldr.x) / 2
        diff = nose.x - shldr_x

        # --- LAG-FREE STEERING ---
        if diff < -DEADZONE:
            if current_key != 'a':
                keyboard.release('d')
                keyboard.press('a')
                current_key = 'a'
            active_inputs.append("STEER LEFT (A)")
        elif diff > DEADZONE:
            if current_key != 'd':
                keyboard.release('a')
                keyboard.press('d')
                current_key = 'd'
            active_inputs.append("STEER RIGHT (D)")
        else:
            if current_key is not None:
                keyboard.release('a')
                keyboard.release('d')
                current_key = None
            active_inputs.append("STRAIGHT")

        # --- BRAKE LOGIC ---
        if l_wrist.y < l_shldr.y:
            keyboard.press('s')
            active_inputs.append("BRAKE (S)")
        else:
            keyboard.release('s')

        mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # --- HUD ---
    cv2.rectangle(frame, (10, 10), (280, 160), (0, 0, 0), -1)
    cv2.putText(frame, "MAC CONTROLLER", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    for i, text in enumerate(active_inputs):
        cv2.putText(frame, f"- {text}", (20, 75 + (i * 25)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(frame, f"FPS: {int(fps)}", (w - 110, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow('Motion Controller HUD', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

# Cleanup
keyboard.release('a')
keyboard.release('d')
keyboard.release('s')
vs.stop()
cv2.destroyAllWindows()