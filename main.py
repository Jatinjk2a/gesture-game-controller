import cv2
import mediapipe as mp
import pyautogui
import webbrowser
import time

# Disable pyautogui fail-safe to prevent crashes when mouse moves to corner
pyautogui.FAILSAFE = False

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Configure hand detection for single hand
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Open webcam
cap = cv2.VideoCapture(0)

# Set target resolution for optimization
TARGET_WIDTH = 640
TARGET_HEIGHT = 480

# Display window settings
DISPLAY_WIDTH = 300
DISPLAY_HEIGHT = 200

# Get screen size and calculate top-right position
screen_width, screen_height = pyautogui.size()
window_x = screen_width - DISPLAY_WIDTH - 10  # 10px padding from edge
window_y = 10  # 10px from top

# Create named window and set properties
cv2.namedWindow('Controller', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Controller', DISPLAY_WIDTH, DISPLAY_HEIGHT)
cv2.moveWindow('Controller', window_x, window_y)

# State machine variables
previous_zone = 'NEUTRAL'
key_pressed = False

# Launch the game in browser
print("Opening Temple Run in browser...")
webbrowser.open('https://poki.com/en/g/temple-run')

# Wait 5 seconds for user to get ready
print("Get your hand ready! Starting in 5 seconds...")
time.sleep(5)
print("Starting hand tracking now!")

def get_zone(x, y, frame_width, frame_height):
    """Determine which zone the index finger tip is in based on 3x3 grid"""
    # Calculate grid boundaries
    col_width = frame_width / 3
    row_height = frame_height / 3
    
    # Determine column (0=left, 1=center, 2=right)
    col = int(x / col_width)
    # Determine row (0=top, 1=middle, 2=bottom)
    row = int(y / row_height)
    
    # Map grid position to zone
    if row == 0 and col == 1:
        return 'JUMP'
    elif row == 2 and col == 1:
        return 'DUCK'
    elif row == 1 and col == 0:
        return 'LEFT'
    elif row == 1 and col == 2:
        return 'RIGHT'
    elif row == 1 and col == 1:
        return 'NEUTRAL'
    else:
        return 'NONE'

def highlight_zone(frame, zone, frame_width, frame_height):
    """Highlight the active zone with a semi-transparent overlay"""
    col_width = frame_width // 3
    row_height = frame_height // 3
    
    # Create overlay for semi-transparency
    overlay = frame.copy()
    
    # Define zone coordinates
    zone_coords = {
        'JUMP': (col_width, 0, col_width * 2, row_height),
        'DUCK': (col_width, row_height * 2, col_width * 2, frame_height),
        'LEFT': (0, row_height, col_width, row_height * 2),
        'RIGHT': (col_width * 2, row_height, frame_width, row_height * 2),
        'NEUTRAL': (col_width, row_height, col_width * 2, row_height * 2)
    }
    
    if zone in zone_coords:
        x1, y1, x2, y2 = zone_coords[zone]
        # Draw semi-transparent rectangle
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), -1)
        # Blend with original frame
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        # Draw thicker border
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 4)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Failed to capture frame from webcam")
        break
    
    # Resize frame for better performance
    frame = cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT))
    
    # Mirror the frame horizontally
    frame = cv2.flip(frame, 1)
    
    # Get frame dimensions
    frame_height, frame_width, _ = frame.shape
    
    # Convert BGR to RGB for MediaPipe processing
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Set writeable flag to False for better performance
    rgb_frame.flags.writeable = False
    
    # Process the frame to detect hands
    results = hands.process(rgb_frame)
    
    # Set writeable flag back to True
    rgb_frame.flags.writeable = True
    
    # Draw green grid lines
    col_width = frame_width // 3
    row_height = frame_height // 3
    cv2.line(frame, (col_width, 0), (col_width, frame_height), (0, 255, 0), 2)
    cv2.line(frame, (col_width * 2, 0), (col_width * 2, frame_height), (0, 255, 0), 2)
    cv2.line(frame, (0, row_height), (frame_width, row_height), (0, 255, 0), 2)
    cv2.line(frame, (0, row_height * 2), (frame_width, row_height * 2), (0, 255, 0), 2)
    
    # Track index finger tip and detect zone
    current_zone = 'NONE'
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks and connections
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            
            # Get index finger tip coordinates (landmark 8)
            index_finger_tip = hand_landmarks.landmark[8]
            x = int(index_finger_tip.x * frame_width)
            y = int(index_finger_tip.y * frame_height)
            
            # Determine zone
            current_zone = get_zone(x, y, frame_width, frame_height)
            
            # Draw circle on index finger tip
            cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
    
    # State machine logic for key presses
    if current_zone == 'NEUTRAL':
        # Reset the flag when returning to neutral zone
        key_pressed = False
        print(f"Current Zone: {current_zone}")
    elif current_zone in ['JUMP', 'DUCK', 'LEFT', 'RIGHT'] and not key_pressed:
        # Press key only if we haven't pressed one yet
        try:
            if current_zone == 'JUMP':
                pyautogui.press('up')
                print(f"Current Zone: {current_zone} -> Pressed 'up'")
            elif current_zone == 'DUCK':
                pyautogui.press('down')
                print(f"Current Zone: {current_zone} -> Pressed 'down'")
            elif current_zone == 'LEFT':
                pyautogui.press('left')
                print(f"Current Zone: {current_zone} -> Pressed 'left'")
            elif current_zone == 'RIGHT':
                pyautogui.press('right')
                print(f"Current Zone: {current_zone} -> Pressed 'right'")
            
            # Set flag to prevent repeated presses
            key_pressed = True
        except Exception as e:
            print(f"Error pressing key: {e}")
    else:
        # In a zone but key already pressed, or in NONE zone
        print(f"Current Zone: {current_zone}")
    
    previous_zone = current_zone
    
    # Highlight active zone
    if current_zone in ['JUMP', 'DUCK', 'LEFT', 'RIGHT', 'NEUTRAL']:
        highlight_zone(frame, current_zone, frame_width, frame_height)
    
    # Display status text
    status_text = f"Status: {current_zone}"
    if current_zone == 'JUMP':
        status_text = "Status: JUMPING"
    elif current_zone == 'DUCK':
        status_text = "Status: DUCKING"
    elif current_zone == 'LEFT':
        status_text = "Status: MOVING LEFT"
    elif current_zone == 'RIGHT':
        status_text = "Status: MOVING RIGHT"
    elif current_zone == 'NEUTRAL':
        status_text = "Status: NEUTRAL"
    else:
        status_text = "Status: INACTIVE"
    
    # Draw status text with background (smaller for compact window)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    text_size = cv2.getTextSize(status_text, font, font_scale, thickness)[0]
    text_x = 5
    text_y = 20
    
    # Draw background rectangle for text
    cv2.rectangle(frame, (text_x - 3, text_y - text_size[1] - 3), 
                  (text_x + text_size[0] + 3, text_y + 3), (0, 0, 0), -1)
    # Draw text
    cv2.putText(frame, status_text, (text_x, text_y), font, font_scale, 
                (0, 255, 0), thickness, cv2.LINE_AA)
    
    # Display the frame
    cv2.imshow('Controller', frame)
    
    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
hands.close()
