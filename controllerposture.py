import cv2
import mediapipe as mp
import pyautogui
import time 

# --- Setup ---
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=0, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

last_spin_time = 0 
target_fps = 40
frame_duration = 1.0 / target_fps  # Time per frame (approx 0.033s)

while cap.isOpened():
    start_time = time.time()  # Start timing the loop

    success, frame = cap.read()
    if not success: break

    frame = cv2.resize(frame, (640, 480)) 
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)

    active_inputs = []

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        l_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        r_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        r_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        l_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

        shoulder_center_x = (l_shoulder.x + r_shoulder.x) / 2
        current_time = time.time()

        # 1. Spin Logic
        if nose.x > shoulder_center_x + 0.15 and (current_time - last_spin_time > 1.5):
            pyautogui.press('s', presses=2, interval=0.05) 
            last_spin_time = current_time
            active_inputs.append("SPIN (S+S)")

        # 2. Steering Logic
        if nose.x < shoulder_center_x - 0.05:
            pyautogui.keyDown('a')
            pyautogui.keyUp('d')
            active_inputs.append("STEER LEFT (A)")
        elif nose.x > shoulder_center_x + 0.05:
            pyautogui.keyDown('d')
            pyautogui.keyUp('a')
            active_inputs.append("STEER RIGHT (D)")
        else:
            pyautogui.keyUp('a')
            pyautogui.keyUp('d')

        # 3. Jump Logic
        if r_wrist.y < r_shoulder.y:
            pyautogui.press('space')
            active_inputs.append("JUMP (SPACE)")

        # 4. Brake/Back Logic
        if l_wrist.y < l_shoulder.y:
            pyautogui.keyDown('s')
            active_inputs.append("BRAKE (S)")
        else:
            pyautogui.keyUp('s')

        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # --- HUD Overlay ---
    cv2.rectangle(frame, (10, 10), (250, 150), (0, 0, 0), -1)
    cv2.putText(frame, "CONTROLS ACTIVE:", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    for i, text in enumerate(active_inputs):
        cv2.putText(frame, f"- {text}", (20, 75 + (i * 25)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow('Motion Controller HUD', frame)

    # --- FPS Control Logic ---d
    elapsed_time = time.time() - start_time
    sleep_time = frame_duration - elapsed_time
    if sleep_time > 0:
        time.sleep(sleep_time)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()