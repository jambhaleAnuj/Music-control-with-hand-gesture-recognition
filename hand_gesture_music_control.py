#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from pygame import mixer
from tensorflow.keras.models import load_model

# Initialize pygame mixer for music playback control
mixer.init()
mixer.music.set_volume(0.5)  # Set initial music volume (0.0 to 1.0)
music_playing = False  # Flag to track music playback state

# Load the pre-trained gesture recognition model
model = load_model("mp_hand_gesture")  # Load model for gesture classification

# Load class names associated with gestures from a text file


def find_file(name: str) -> str:
    """Return a readable path for name by checking common locations."""
    candidates = [
        Path(name),
        Path("assets") / "audio" / name,
        Path("assets") / "config" / name,
        Path("docs") / name,
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return name  # fallback; will error later if truly missing


with open(find_file("gesture.names"), "r") as f:
    classNames = f.read().split("\n")
print(classNames)  # Print loaded gesture class names (for debugging)

# Initialize webcam capture or video stream from URL
# Tip: set source to 0 for default webcam, or to an IP camera URL.
source = 0  # e.g., 0 or "http://x192.168.43.1:8080/video"
cap = cv2.VideoCapture(source)
if isinstance(source, str):
    cap.open(source)
if not cap.isOpened():
    raise RuntimeError(
        "Failed to open video source. Set 'source=0' for webcam or check your URL."
    )

# Initialize MediaPipe hands object for hand detection
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mpDraw = mp.solutions.drawing_utils  # For drawing landmarks on frame (optional)

while True:
    # Read each frame from the webcam or video stream
    _, frame = cap.read()

    # Get frame dimensions (width, height, channels)
    x, y, c = frame.shape

    # Flip the frame vertically for better landmark alignment on the hand
    frame = cv2.flip(frame, 1)

    # Convert frame to RGB format for MediaPipe hand detection
    framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame using MediaPipe to detect hand landmarks
    result = hands.process(framergb)

    className = ""  # Initialize variable to store predicted gesture class name

    # Process the hand detection result if hands are found
    if result.multi_hand_landmarks:
        landmarks = []  # List to store extracted hand landmarks
        for handslms in result.multi_hand_landmarks:
            for lm in handslms.landmark:
                # Extract landmark coordinates (normalized to frame dimensions)
                lmx = int(lm.x * x)  # Scale x-coordinate to frame width
                lmy = int(lm.y * y)  # Scale y-coordinate to frame height
                landmarks.append([lmx, lmy])

            # Draw hand landmarks on the frame for visualization (optional)
            mpDraw.draw_landmarks(frame, handslms, mpHands.HAND_CONNECTIONS)

            # Predict gesture class using the loaded model and extracted landmarks
            prediction = model.predict([landmarks])
            classID = np.argmax(prediction)  # Get index of the highest prediction value
            className = classNames[classID]  # Retrieve gesture class name based on index

            print("Class name: ", className)  # Print predicted gesture class (for debugging)

            # Perform music playback actions based on the detected gesture
            if className == "thumbs up" and not music_playing:
                print("THUMB")
                mp3_path = find_file("METAMORPHOSIS.mp3")
                mixer.music.load(mp3_path)  # Load the music file
                mixer.music.play()  # Start music playback
                music_playing = True  # Update music playback state
            elif className == "thumbs down":
                print("THUMB DOWN")
                mixer.music.stop()  # Stop music playback
                music_playing = False  # Update music playback state
            elif className == "fist" and music_playing:
                print("ROCK")
                mixer.music.unpause()  # Resume paused music playback
            elif (className == "stop" or className == "live long") and music_playing:
                print("PALM")
                mixer.music.pause()  # Pause music playback

    # Display the predicted gesture class name on the frame (optional)
    cv2.putText(
        frame,
        className,
        (10, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )

    # Display the final frame with landmarks (if drawn) and prediction text
    cv2.imshow("Output", frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
