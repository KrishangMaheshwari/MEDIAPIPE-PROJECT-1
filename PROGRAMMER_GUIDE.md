**___________________________________PHASE 1: INITIAL SETUPS ____________________________________**

# 1. IMPORTING LIBRARIES & THEIR USES:

import cv2                       Handles image processing.
import mediapipe as mp           Detects hand landmarks.
import pyautogui                 Controls mouse/keyboard programmatically.
import time                      Tracks time for FPS and logging.
import numpy as np               Math library for arrays and calculations.
import math                      For trigonometry (angles).
import os, platform, subprocess  To interact with the Operating System (opening files).
import random                    Random number generator (not heavily used here but good practice).
from fpdf import FPDF            Creates the PDF reports.
from datetime import datetime    timestamps in pdf reports
from pynput.mouse import         Low-level mouse control (smoother than pyautogui).
from pynput.keyboard import      Low-level keyboard control.

# 2. INITIALISING PYNPUT CONTROLLERS:
   
mouse = MouseController()
keyboard = KeyboardController()

# 3. PERFORMING FAILSAFE

pyautogui.FAILSAFE = False  
pyautogui.PAUSE = 0 

# 3.1. WHAT IS FAILSAFE?
By default PyAutoGUI crashes if the mouse cursor is whipped to one of the edges of the 
computer window, in shooting games , this mistake is common thus we turned off the failsafe.

# 3.2. pyautogui.PAUSE = 0?
Removes the built-in 0.1s delay after every command, ensuring instant response for gaming.

# 4. BASICS OF MEDIAPIPE

AI/ML trained mediapipe model is called mediapipe_solutions

mediapipe_solutions contains various detection models we will be using 3 of it:

a. mp_solutions.hands         - HAND DETECTION
b. mp_solutions.drawing_utils - STYLING THE INTERFACE
c. mp_solutions.pose          - POSE DETECTION

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# 4.2. INITIALISING GENERIC MODEL
# FOR HANDS

hands = mp_hands.Hands(
    max_num_hands=2, 
    model_complexity=0, 
    min_detection_confidence=0.5, 
    min_tracking_confidence=0.5
)
# FOR POSE

pose = mp_pose.Pose(model_complexity=0, min_detection_confidence=0.5)

This code initializes MediaPipe Hands and Pose models for real-time detection. 
The Hands object is created to detect up to two hands using a lightweight model 
(model_complexity=0) for faster performance, with min_detection_confidence=0.5 ensuring that a 
hand is detected only when the model is at least 50% confident, and min_tracking_confidence=0.5
maintaining reliable tracking of detected hands across frames. 

Similarly, the Pose object initializes a full-body pose detection model with low complexity 
for speed, and min_detection_confidence=0.5 ensures that a human pose is detected only when 
sufficient confidence is achieved.

# 5. DISPLAY & VIDEO CAPTURE

cap = cv2.VideoCapture(0)
W, H = 1280, 720
cap.set(3, W) 
cap.set(4, H)

HERE 3 & 4 are fixed codes, 
3 - frame width
4 - frame height

**______________________________________PHASE 2: VISION Z________________________________________**

This section covers the styling in which we added glassmorphic look with transparency and neon borders

# 6. LOCATING FILE FUNCTION DEFINATION (LOCATES THE FILE ON MACOS / WINDOWS):

def system_locate_file(file_path):
    """
    OS-Agnostic file locator. Opens the folder containing the generated report.
    """
    path = os.path.abspath(file_path)
    if platform.system() == "Windows":
        subprocess.run(['explorer', '/select,', path])
    elif platform.system() == "Darwin":
        subprocess.run(['open', '-R', path])
    else:
        subprocess.run(['xdg-open', os.path.dirname(path)])
# 7. GENERATING PDF

# 7.1. PRIOR KNOWLEDGE

# ______________________________________________________________________________________________________________________________________

FPDF() - Initializes the PDF class and creates the document object in the computer's memory.

add_page() - Adds a new blank page to the document so you have a canvas to write on.

set_fill_color(r, g, b) - Defines the background color for cells (used for your dark blue header and gray table bars).

set_text_color(r, g, b) - Sets the "ink" color for all text that follows this command.

set_font(family, style, size) - Chooses the font (Arial), the weight ('B' for Bold or '' for Regular), and the point size.

cell(w, h, txt, border, ln, align, fill) - The primary tool; draws a rectangular box of a specific width/height and places text inside it.

ln(h) - Acts like the "Enter" key on a keyboard; it creates a line break to move down to the next row.

output(filename) - Compiles all the data in memory and saves it as an actual .pdf file on your hard drive.

# ______________________________________________________________________________________________________________________________________

7.2.___________THE CODE_________
def generate_pdf_report(engine_name):
    """
    Compiles the session logs into a professional PDF report.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_fill_color(10, 10, 30)
        pdf.set_text_color(0, 255, 100)
        pdf.set_font("Arial", 'B', 24)
        pdf.cell(190, 20, f"VISION Z: {engine_name} ANALYTICS", ln=True, align='C', fill=True)
        
        # Subheader
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.ln(10)
        
        # Table Headers
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(50, 50, 50)
        pdf.set_text_color(255, 255, 255)
        
        col_widths = [25, 45, 40, 55, 25]
        headers = ["TIME", "EVENT", "DATA", "MISTAKE", "GAIN"]
        
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 10, h, 1, 0, 'C', True)
        pdf.ln()
        
        # Table Data
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        
        for log in vz_logs:
            for i, item in enumerate(log):
                # Truncate long text to fit cells
                text = str(item)[:20]
                pdf.cell(col_widths[i], 8, text, 1)
            pdf.ln()
            
        filename = f"VisionZ_{engine_name}_{datetime.now().strftime('%H%M%S')}.pdf"
        pdf.output(filename)
        return filename
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return "error.pdf"
__________END_____________

# 7.3. WHAT IS THE FUNCTION DIONG?

This code makes a simple report card for your game. It opens a blank page and adds a 
colorful title at the top so it looks neat. It then adds the date and time to show 
exactly when you played. In the middle, it draws a table with small boxes for things 
like your moves and your mistakes. The code looks at all the notes it took while you 
were playing and writes them into these boxes one by one. If a note is too long, 
it trims the extra letters to keep everything tidy. Finally, it saves the whole page 
as a file on your computer so you can look at it later.








