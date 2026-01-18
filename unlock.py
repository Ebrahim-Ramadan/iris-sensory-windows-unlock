from dotenv import load_dotenv
import os
import cv2
import mediapipe as mp
import pyautogui
import time
import math
import traceback

# =======================
# ENV + LOGGING
# =======================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "unlock.log")

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} | {msg}")         # print to terminal
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | {msg}\n")
    except Exception:
        pass  # don't crash if log file fails

# Wrap everything in try/except to keep terminal open
try:
    log("==== Script started ====")

    # Load .env
    load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

    WINDOWS_PIN = os.getenv("WINDOWS_PIN")
    if not WINDOWS_PIN:
        log("ERROR: WINDOWS_PIN not set")
        input("Press Enter to exit...")
        raise RuntimeError("WINDOWS_PIN not set")

    log("PIN loaded successfully")

    # =======================
    # CONFIG
    # =======================
    REQUIRED_FACE_FRAMES = 15
    BLINK_THRESHOLD = 0.20
    BLINK_FRAMES = 2

    # =======================
    # MEDIA PIPE SETUP
    # =======================
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )

    LEFT_EYE = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    def eye_aspect_ratio(landmarks, eye):
        def dist(a, b):
            return math.hypot(a.x - b.x, a.y - b.y)
        p1, p2 = landmarks[eye[1]], landmarks[eye[5]]
        p3, p4 = landmarks[eye[2]], landmarks[eye[4]]
        p5, p6 = landmarks[eye[0]], landmarks[eye[3]]
        return (dist(p1, p2) + dist(p3, p4)) / (2.0 * dist(p5, p6))

    # =======================
    # CAMERA
    # =======================
    log("Opening camera")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        log("ERROR: Camera failed to open")
        input("Press Enter to exit...")
        raise RuntimeError("Camera failed to open")
    log("Camera opened successfully")

    face_frames = 0
    blink_frames = 0
    blinked = False

    # =======================
    # MAIN LOOP
    # =======================
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (640, 480))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        if result.multi_face_landmarks:
            face_frames += 1
            landmarks = result.multi_face_landmarks[0].landmark

            left_ear = eye_aspect_ratio(landmarks, LEFT_EYE)
            right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE)
            ear = (left_ear + right_ear) / 2.0

            if ear < BLINK_THRESHOLD:
                blink_frames += 1
            else:
                if blink_frames >= BLINK_FRAMES:
                    blinked = True
                    log("Blink detected")
                blink_frames = 0

            if face_frames >= REQUIRED_FACE_FRAMES and blinked:
                log("Face + blink verified, unlocking")
                cap.release()
                cv2.destroyAllWindows()

                time.sleep(0.8)
                pyautogui.press("enter")
                time.sleep(0.3)
                pyautogui.write(WINDOWS_PIN, interval=0.12)
                pyautogui.press("enter")

                log("PIN sent, exiting")
                break
        else:
            face_frames = 0
            blink_frames = 0
            blinked = False

    cap.release()
    cv2.destroyAllWindows()

except Exception as e:
    log("CRASH: " + str(e))
    log(traceback.format_exc())
    print("CRASH:", e)
    traceback.print_exc()
    input("Press Enter to exit...")
