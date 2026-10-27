# SnapClass – AI-Powered Biometric Classroom Attendance System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://subhadeeppandey2005-png-biometric-classroom-attendan-app-ajcqjw.streamlit.app)
![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)
![Database](https://img.shields.io/badge/Database-Supabase%20%2F%20PostgreSQL-3ECF8E.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

SnapClass is an intelligent classroom management and multimodal biometric attendance platform designed to eliminate proxy attendance and streamline classroom administration. Built with Streamlit, Supabase, and custom computer vision and speech processing pipelines, SnapClass provides instant, spoof-resistant student verification through facial recognition and voice authentication.

---

## Key Features

- **Multimodal Biometric Verification**:
  - **Facial Recognition**: High-dimensional face embeddings extracted via pre-trained deep learning models and classified using Scikit-Learn SVM classifiers.
  - **Voiceprint Identification**: Speaker verification and acoustic feature extraction using `resemblyzer` and `librosa`.
- **Teacher Dashboard**:
  - Subject and section management.
  - Dynamic QR code generation for in-class student registration and session join links.
  - Real-time automated attendance sheets and exportable records.
- **Student Portal**:
  - Frictionless onboarding and biometric enrollment via browser-based camera and microphone input.
  - One-click attendance verification using session join codes and QR integration.
- **Cloud Architecture**:
  - Serverless relational data storage, authentication, and secure vector persistence powered by **Supabase**.
  - Dynamic host and session header resolution for zero-configuration cloud deployment.

---

## Tech Stack & Architecture

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/)
- **Backend Database**: [Supabase](https://supabase.com/) (PostgreSQL)
- **Computer Vision**: `face_recognition`, `face_recognition_models`, `Pillow`
- **Machine Learning**: `scikit-learn`, `numpy`, `pandas`
- **Audio Processing**: `librosa`, `resemblyzer`, `soundfile`
- **Security & Utilities**: `bcrypt`, `segno` (QR Generation)
- **Linux Runtime Dependencies**: `cmake`, `ffmpeg`, `libsndfile1`, `libgl1`

---

## System Workflow

```text
[Teacher Creates Subject]
        │
        ▼
[Dynamic QR Code Generated] ──► [Student Scans / Opens Join URL]
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       ▼                                             ▼
             [Facial Verification]                         [Voice Verification]
             - Webcam Frame Capture                        - Microphone Audio Sample
             - Embedding Extraction                        - Resemblyzer Voiceprint
             - SVM Match against DB                        - Cosine Similarity Check
                       │                                             │
                       └──────────────────────┬──────────────────────┘
                                              ▼
                                 [Supabase Realtime DB]
                             - Validated Attendance Entry
                             - Timestamped Session Logs




Project Structure

biometric-classroom-attendance/
├── app.py                      # Main entrypoint and navigation router
├── packages.txt                # Debian Linux system dependencies for Streamlit Cloud
├── requirements.txt            # Python dependencies
├── src/
│   ├── Components/             # Reusable UI dialogs, QR generators, cards
│   │   ├── dialog_share_subject.py
│   │   ├── dialog_voice_attendance.py
│   │   └── ...
│   ├── database/               # Supabase connection client and query handlers
│   │   ├── config.py
│   │   └── db.py
│   ├── pipelines/              # Biometric pipelines (embeddings & inference)
│   │   ├── face_pipeline.py
│   │   └── voice_pipelines.py
│   ├── screens/                # Role-specific application views
│   │   ├── home_screen.py
│   │   ├── student_screen.py
│   │   └── teacher_screen.py
│   └── UI/                     # Layout templates and custom styling
│       └── base_layout.py
└── README.md



Local Setup & Installation

1. Prerequisites
(i) Python 3.11 recommended

(ii) CMake and FFmpeg installed locally

(iii) A free Supabase account and project

2. Clone the Repository
git clone [https://github.com/subhadeeppandey2005-png/biometric-classroom-attendance.git](https://github.com/subhadeeppandey2005-png/biometric-classroom-attendance.git)

3. Create a Virtual Environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

4. Install Dependencies
pip install -r requirements.txt

5. Configure Secrets
Create a .streamlit/secrets.toml file in the root directory


6. Run the Application
streamlit run app.py


Cloud Deployment Notes:

When deploying to Streamlit Community Cloud:

1. Ensure packages.txt exists at the root with Debian system libraries (cmake, build-essential, libgl1, libglib2.0-0, libsndfile1, ffmpeg).

2. Add your SUPABASE_URL and SUPABASE_KEY directly inside App Settings > Secrets.

3. Set the runtime environment to Python 3.11 to ensure full wheel compatibility with dlib and audio processing binaries.


Author
Subhadeep Pandey

GitHub: @subhadeeppandey2005-png

- **Project Link**: [GitHub Repository](https://github.com/subhadeeppandey2005-png/biometric-classroom-attendance)
- **Live Demo**: [Streamlit App](https://subhadeeppandey2005-png-biometric-classroom-attendan-app-ajcqjw.streamlit.app)
