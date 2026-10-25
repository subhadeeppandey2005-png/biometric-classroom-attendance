import time
import streamlit as st
from PIL import Image
import numpy as np

from src.UI.base_layout import style_background_dashboard, style_base_layout
from src.Components.header import header_dashboard
from src.Components.footer import footer_dashboard
from src.database.db import check_teacher_exists, create_teacher, teacher_login
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier 
from src.pipelines.voice_pipelines import get_voice_embedding
from src.database.db import get_all_students, create_student, get_student_subjects, get_student_attendance, unenroll_student_to_subject
from src.Components.subject_card import subject_card

from src.Components.dialog_enroll import enroll_dialog

def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, {student_data.get('name', '')}")
        st.markdown('<div style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("Logout", type='secondary', key='logout_btn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            if 'student_data' in st.session_state:
                del st.session_state.student_data
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.header("Your Enrolled Subjects")

    with c2:
        if st.button('Enroll in Subject', type='primary', use_container_width=True):
            enroll_dialog()

    st.divider()

    with st.spinner('Loading your enrolled subjects...'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs:
        sid = log['subject_id']

        if sid not in stats_map:
            stats_map[sid] = {"total":0, "attended": 0}

        stats_map[sid]['total'] =+ 1

        if logs.get('is_present'):
            stats_map[sid]['attended'] += 1

    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']


        stats = stats_map.get(sid, {"total":0, "attended": 0})
        def unenroll_button():
            if st.button("Unenroll from this course", type='tertiary', use_container_width=True, icon=':material/delete_forever:'):
                unenroll_student_to_subject(student_id, sid)
                st.toast(f"Unenroll from {sub['name']} successfully!")
                st.rerun()

        with cols[i % 2]:
            subject_card(
                name = sub['name'],
                code =sub['subject_code'],
                section = sub['section'],
                stats = [
                    ('📆', 'Total', stats['total']),
                    ('☑️', 'Attended', stats['attended']),
                ],
                footer_callback=unenroll_button
            )
    footer_dashboard()

def student_screen():
    style_background_dashboard()
    style_base_layout()

    # CSS to ensure Streamlit's native audio input controls are fully visible and not clipped
    st.markdown("""
        <style>
            div[data-testid="stAudioInput"] {
                overflow: visible !important;
                margin-top: 14px !important;
                padding-top: 8px !important;
            }
            div[data-testid="stAudioInput"] > div {
                overflow: visible !important;
            }
        </style>
    """, unsafe_allow_html=True)

    if "student_data" in st.session_state:
        student_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.markdown('<div style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("Back", type='secondary', key='student_back_btn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.session_state['teacher_login_type'] = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.header('Login Using FaceID')
    st.markdown("<br>", unsafe_allow_html=True)

    show_registration = False

    photo_source = st.camera_input("Position your face in the center")

    if photo_source:
        img = np.array(Image.open(photo_source))

        with st.spinner('AI is scanning...'):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.warning('Face not found! Please look directly at the camera.')

            elif num_faces > 1:
                st.warning('Multiple faces found! Only one student can verify at a time.')

            else:
                # Exactly 1 face found: check if recognized or new student
                if detected:
                    student_id = list(detected.keys())[0]
                    all_students = get_all_students()

                    student = next((s for s in all_students if s['student_id'] == student_id), None)

                    if student:
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = 'student'
                        st.session_state.student_data = student
                        st.toast(f"Welcome back, {student['name']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info('Face not recognized! You might be a new student!')
                        show_registration = True
                else:
                    # Face detected in camera, but no match found in database
                    st.info('Face not recognized! You might be a new student!')
                    show_registration = True

        if show_registration:
            with st.container(border=True):
                st.header('Register new Profile')
                new_name = st.text_input("Enter your name", placeholder='E.g. Subha Pandey')

                st.subheader('Optional : Voice Enrollment')
                st.info("Enroll for voice-only attendance")

                audio_data = None
                try:
                    audio_data = st.audio_input(
                        'Record a short phrase like: "I am present, my name is Subha"',
                        key="voice_reg"
                    )
                except Exception:
                    st.error('Audio recording failed to initialize.')

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button('Create Account', type='primary'):
                    if new_name.strip():
                        with st.spinner('Creating profile...'):
                            img = np.array(Image.open(photo_source))
                            encoding = get_face_embeddings(img)
                            if encoding:
                                face_emb = encoding[0].tolist()

                                voice_emb = None
                                if audio_data:
                                    voice_emb = get_voice_embedding(audio_data.read())

                                response_data = create_student(new_name, face_embedding=face_emb, voice_embedding=voice_emb)

                                if response_data:
                                    train_classifier() 
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_role = 'student'
                                    st.session_state.student_data = response_data[0]
                                    st.toast(f"Profile Created! Hi {new_name}!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error('Failed to create student record in database.')
                            else:
                                st.error('Could not capture facial features for registration.')
                    else:
                        st.warning('Please enter your name.')

    footer_dashboard()