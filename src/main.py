import cv2
import numpy as np
import mediapipe as mp
from collections import deque

# --- Initializations ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

points = deque(maxlen=1024)
is_drawing = False
was_drawing_previously = False

cap = cv2.VideoCapture(0)

print("Started! Use gestures to control drawing. Press 'q' to exit.")

def is_finger_straight(landmarks, tip_id, pip_id):
    """Checks if a finger is straight based on Y-coordinates."""
    return landmarks.landmark[tip_id].y < landmarks.landmark[pip_id].y


while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    frame.flags.writeable = False
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    frame.flags.writeable = True

    status_text = "WAITING FOR HAND"
    status_color = (255, 255, 255)

    current_frame_is_drawing = False 
    
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        
        index_straight = is_finger_straight(hand_landmarks, mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.INDEX_FINGER_PIP)
        middle_straight = is_finger_straight(hand_landmarks, mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_PIP)
        ring_straight = is_finger_straight(hand_landmarks, mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_PIP)
        pinky_straight = is_finger_straight(hand_landmarks, mp_hands.HandLandmark.PINKY_TIP, mp_hands.HandLandmark.PINKY_PIP)

        index_bent = not index_straight
        middle_bent = not middle_straight
        ring_bent = not ring_straight
        pinky_bent = not pinky_straight
        
        all_straight = index_straight and middle_straight and ring_straight and pinky_straight
        all_bent = not index_straight and not middle_straight and not ring_straight and not pinky_straight
        
        index_only_open = index_straight and middle_bent and ring_bent and pinky_bent
        
        if all_straight:
            points.clear()
            current_frame_is_drawing = False
            status_text = "ERASE: CLEARING CANVAS"
            status_color = (0, 0, 255)
        
        elif all_bent:
            current_frame_is_drawing = False
            status_text = "NO ACTION: FIST CLENCHED"
            status_color = (128, 128, 128)
        
        elif index_only_open:
            current_frame_is_drawing = True
            status_text = "DRAWING: INDEX ONLY OPEN"
            status_color = (0, 255, 0)
        
        elif pinky_straight: 
            current_frame_is_drawing = False
            status_text = "STOP DRAWING: pinky OPEN"
            status_color = (255, 165, 0)
        
        else:
            current_frame_is_drawing = False
            status_text = "UNKNOWN GESTURE: STOPPED"
            status_color = (255, 255, 0)
        
        if was_drawing_previously and not current_frame_is_drawing:
            points.appendleft(None)
        
        if current_frame_is_drawing:
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            h, w, _ = frame.shape
            
            center_x = int(index_finger_tip.x * w)
            center_y = int(index_finger_tip.y * h)
            
            points.appendleft((center_x, center_y))

            cv2.circle(frame, (center_x, center_y), 10, (0, 255, 255), -1)
            
    else:
        current_frame_is_drawing = False
        status_text = "NO HAND DETECTED"
        status_color = (255, 255, 255)
        
        if was_drawing_previously:
            points.appendleft(None)

    
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2, cv2.LINE_AA)

    for i in range(1, len(points)):
        if points[i - 1] is None or points[i] is None:
            continue
        
        cv2.line(frame, points[i - 1], points[i], (0, 0, 255), 5)

    was_drawing_previously = current_frame_is_drawing
    
    cv2.imshow('Virtual Air Canvas (Clean Line Breaks)', frame)
    
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()