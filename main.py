import cv2
import mediapipe as mp
import time
import math


#---MediaPipe Setup---
BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult

model_path = "gesture_recognizer.task"

latest_result = None
start_time = time.time()

def result_callback(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    latest_result = result

options = GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,
    num_hands=2,
    result_callback=result_callback
)

recognizer = GestureRecognizer.create_from_options(options)



HAND_CONNECTIONS = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS




FINGER_COLORS = {
    "thumb":  (0, 0, 255),     # Red
    "index":  (0, 255, 0),     # Green
    "middle": (255, 0, 0),     # Blue
    "ring":   (0, 255, 255),   # Yellow
    "pinky":  (255, 0, 255),   # Magenta
    "palm":   (200, 200, 200)  # Gray
}

#---custom gestures---




# pinch

def is_touching(hand_landmarks, a, b, w, h, ratio=0.25):
    thumb = hand_landmarks[a]
    index = hand_landmarks[b]
    wrist = hand_landmarks[0]
    middle_mcp = hand_landmarks[9]

    # pinch distance
    pinch_dist = math.hypot(
        (thumb.x - index.x) * w,
        (thumb.y - index.y) * h
    )

    # hand reference size
    hand_size = math.hypot(
        (wrist.x - middle_mcp.x) * w,
        (wrist.y - middle_mcp.y) * h
    )

    return pinch_dist < (hand_size * ratio)




#---Webcam---
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    timestamp_ms = int((time.time() - start_time) * 1000)
    recognizer.recognize_async(mp_image, timestamp_ms)

    if latest_result and latest_result.hand_landmarks:
        

        for i, hand_landmarks in enumerate(latest_result.hand_landmarks):

            h, w, _ = frame.shape

            # Define finger landmark groups
            FINGERS = {
                "thumb":  [1,2,3,4],
                "index":  [5,6,7,8],
                "middle": [9,10,11,12],
                "ring":   [13,14,15,16],
                "pinky":  [17,18,19,20]
            }

            # Draw Palm
            palm_points = [0, 5, 9, 13, 17]

            for p_i in range(len(palm_points)):
                for p_j in range(i+1, len(palm_points)):
                    p1 = hand_landmarks[palm_points[p_i]]
                    p2 = hand_landmarks[palm_points[p_j]]

                    x1, y1 = int(p1.x * w), int(p1.y * h)
                    x2, y2 = int(p2.x * w), int(p2.y * h)

                    cv2.line(frame, (x1, y1), (x2, y2), FINGER_COLORS["palm"], 1)

            # Draw Each Finger
            for finger_name, indices in FINGERS.items():

                color = FINGER_COLORS[finger_name]


                # Draw joints
                for idx in indices:
                    lm = hand_landmarks[idx]
                    x, y = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (x, y), 6, color, -1)

                # Draw connections (3 lines per finger)
                for i_i in range(len(indices)-1):
                    p1 = hand_landmarks[indices[i_i]]
                    p2 = hand_landmarks[indices[i_i+1]]

                    x1, y1 = int(p1.x * w), int(p1.y * h)
                    x2, y2 = int(p2.x * w), int(p2.y * h)

                    cv2.line(frame, (x1, y1), (x2, y2), color, 3)

            # Draw wrist
            wrist = hand_landmarks[0]
            x, y = int(wrist.x * w), int(wrist.y * h)
            cv2.circle(frame, (x, y), 8, FINGER_COLORS["palm"], -1)

            # Draw gesture label
            if latest_result.gestures and len(latest_result.gestures) > i:
                top_gesture = latest_result.gestures[i][0]
                label = f"{top_gesture.category_name} ({top_gesture.score:.2f})"

                wrist = hand_landmarks[0]
                text_x = int(wrist.x * w)
                text_y = int(wrist.y * h) - 20

                cv2.putText(frame, label,
                            (text_x, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, color, 2)

                if is_touching(hand_landmarks, 4, 8, w, h) and top_gesture.category_name == "None":
                    cv2.putText(frame, "PINCH",
                    (text_x, text_y - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 255, 255), 3)
                    continue

                if is_touching(hand_landmarks, 4, 20, w, h) and top_gesture.category_name == "None":
                    cv2.putText(frame, "TICK",
                    (text_x, text_y - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 255, 255), 3)
                    continue

    cv2.imshow("2-Hand Skeleton Tracker", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
