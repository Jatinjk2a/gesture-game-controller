# 🎮 Gesture-Controlled Game Controller

Control browser games like Temple Run and Subway Surfers using hand gestures! This project uses computer vision and hand tracking to map your hand movements to keyboard inputs.

## ✨ Features

- **Real-time Hand Tracking**: Uses MediaPipe to detect and track hand landmarks
- **Gesture-Based Controls**: Control games with simple hand movements
- **Smart State Machine**: Prevents key spamming with intelligent gesture detection
- **Visual Feedback**: See your active zones and current status in real-time
- **Auto-Launch**: Automatically opens the game in your browser
- **Optimized Performance**: Runs smoothly with frame resizing and efficient processing
- **Compact Display**: Small controller window positioned at top-right corner

## 🎯 How It Works

The screen is divided into a 3x3 grid. Move your index finger to different zones to trigger actions:

```
┌─────────┬─────────┬─────────┐
│         │  JUMP   │         │
│         │   ⬆️    │         │
├─────────┼─────────┼─────────┤
│  LEFT   │ NEUTRAL │  RIGHT  │
│   ⬅️    │    🏠   │    ➡️   │
├─────────┼─────────┼─────────┤
│         │  DUCK   │         │
│         │   ⬇️    │         │
└─────────┴─────────┴─────────┘
```

- **JUMP** (Top-Center): Press UP arrow
- **DUCK** (Bottom-Center): Press DOWN arrow
- **LEFT** (Middle-Left): Press LEFT arrow
- **RIGHT** (Middle-Right): Press RIGHT arrow
- **NEUTRAL** (Center): Reset - return here between moves

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- Webcam
- Windows/Mac/Linux

### Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/gesture-game-controller.git
cd gesture-game-controller
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## 🎮 Usage

1. Run the script:
```bash
python main.py
```

2. The script will:
   - Automatically open Temple Run in your browser
   - Give you 5 seconds to get ready
   - Start the hand tracking controller

3. Position your hand in front of the webcam

4. Click on the game window to focus it

5. Move your index finger to different zones to control the game

6. Press `q` in the Controller window to exit

## 🎯 Tips for Best Performance

- **Lighting**: Ensure good lighting for better hand detection
- **Background**: Use a plain background for optimal tracking
- **Distance**: Keep your hand 1-2 feet from the camera
- **Return to Neutral**: Always return to the center zone between moves to trigger the next action
- **Game Focus**: Make sure the browser game window is focused (clicked)

## 🎨 Customization

### Change the Game URL

Edit line 48 in `main.py`:
```python
webbrowser.open('https://your-game-url-here.com')
```

### Adjust Window Size

Modify lines 30-31 in `main.py`:
```python
DISPLAY_WIDTH = 300  # Change width
DISPLAY_HEIGHT = 200  # Change height
```

### Change Key Mappings

Edit lines 175-182 in `main.py` to map zones to different keys:
```python
if current_zone == 'JUMP':
    pyautogui.press('space')  # Change to any key
```

### Adjust Detection Sensitivity

Modify lines 14-16 in `main.py`:
```python
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,  # Increase for stricter detection
    min_tracking_confidence=0.7    # Increase for smoother tracking
)
```

## 🛠️ Technical Details

- **Hand Detection**: MediaPipe Hands solution
- **Landmark Tracking**: Index finger tip (Landmark 8)
- **Grid System**: 3x3 zone detection
- **State Machine**: Prevents key spam by requiring neutral zone reset
- **Frame Processing**: 640x480 resolution for optimal performance
- **Display**: 300x200 compact window at top-right corner

## 🎮 Compatible Games

This controller works with any browser game that uses arrow keys:
- Temple Run
- Subway Surfers
- Chrome Dino Game
- And many more!

## 📝 Requirements

- opencv-python: Computer vision and image processing
- mediapipe: Hand tracking and landmark detection
- pyautogui: Keyboard input simulation

## 🐛 Troubleshooting

**Hand not detected?**
- Check your lighting
- Ensure your hand is clearly visible
- Try adjusting the camera angle

**Keys not working in game?**
- Make sure the game window is focused (click on it)
- Check if the game uses arrow keys for controls

**Low FPS?**
- Close other applications
- Reduce the TARGET_WIDTH and TARGET_HEIGHT values
- Lower the min_detection_confidence

**Controller window in wrong position?**
- The window auto-positions at top-right
- You can manually drag it if needed

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 👨‍💻 Author

Created with ❤️ for gamers who want to play hands-free!

## 🌟 Show Your Support

Give a ⭐️ if this project helped you!

---

**Note**: This project is for educational purposes. Make sure to follow the terms of service of any games you play with this controller.
