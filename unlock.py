import cv2
import face_recognition
import pyautogui
import time

# Load authorized face
authorized_image = face_recognition.load_image_file("me.jpg")
authorized_encoding = face_recognition.face_encodings(authorized_image)[0]

video = cv2.VideoCapture(0)

print("Camera started...")

verified_frames = 0

while True:
    ret, frame = video.read()
    if not ret:
        continue

    rgb = frame[:, :, ::-1]
    faces = face_recognition.face_encodings(rgb)

    for face in faces:
        match = face_recognition.compare_faces(
            [authorized_encoding], face, tolerance=0.45
        )

        if match[0]:
            verified_frames += 1
            print(f"Verified frames: {verified_frames}")

            if verified_frames >= 5:
                print("Access Granted")
                video.release()
                cv2.destroyAllWindows()

                # Give Windows time to focus PIN field
                time.sleep(1)

                # TYPE YOUR WINDOWS PIN HERE
                pyautogui.write("1234", interval=0.15)
                pyautogui.press("enter")
                exit()
        else:
            verified_frames = 0

    cv2.imshow("Face Unlock", frame)
    if cv2.waitKey(1) == 27:  # ESC to quit
        break

video.release()
cv2.destroyAllWindows()
