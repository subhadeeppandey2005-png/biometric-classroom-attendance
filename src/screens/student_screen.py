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
from src.database.config import supabase
from src.database.db import (
    get_all_students,
    create_student,
    get_student_subjects,
    get_student_attendance,
    unenroll_student_to_subject
)
from src.Components.subject_card import subject_card
from src.Components.dialog_enroll import enroll_dialog


def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data.get('student_id') or student_data.get('id')

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
        subjects = get_student_subjects(student_id) or []
        logs = get_student_attendance(student_id) or []

    # Calculate attendance statistics per subject
    stats_map = {}
    for log in logs:
        if not isinstance(log, dict):
            continue

        sid = log.get('subject_id')
        if not sid:
            continue

        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0}

        stats_map[sid]['total'] += 1

        if log.get('is_present'):
            stats_map[sid]['attended'] += 1

    if not subjects:
        st.info("You are not enrolled in any subjects yet. Click **Enroll in Subject** above to join a class!")
    else:
        cols = st.columns(2)
        for i, sub_node in enumerate(subjects):
            sub = sub_node.get('subjects') if isinstance(sub_node, dict) and 'subjects' in sub_node else sub_node
            if not sub:
                continue

            sid = sub.get('subject_id') or sub.get('id')
            stats = stats_map.get(sid, {"total": 0, "attended": 0})

            def make_unenroll_callback(curr_sub_id, curr_sub_name):
                def unenroll_button():
                    if st.button(
                        "Unenroll from this course",
                        type='tertiary',
                        use_container_width=True,
                        icon=':material/delete_forever:',
                        key=f"unenroll_{curr_sub_id}"
                    ):
                        unenroll_student_to_subject(student_id, curr_sub_id)
                        st.toast(f"Unenrolled from {curr_sub_name} successfully!", icon="👋")
                        time.sleep(0.5)
                        st.rerun()
                return unenroll_button

            with cols[i % 2]:
                subject_card(
                    name=sub.get('name', 'Unnamed Subject'),
                    code=sub.get('subject_code', ''),
                    section=sub.get('section', ''),
                    stats=[
                        ('📆', 'Total', stats['total']),
                        ('☑️', 'Attended', stats['attended']),
                    ],
                    footer_callback=make_unenroll_callback(sid, sub.get('name', 'Subject'))
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

    # Track student authentication mode: 'face' vs 'voice'
    if 'student_login_mode' not in st.session_state:
        st.session_state.student_login_mode = 'face'

    # Track whether to reveal the voice registration container
    if 'show_voice_reg_form' not in st.session_state:
        st.session_state.show_voice_reg_form = False

    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.markdown('<div style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("Back", type='secondary', key='student_back_btn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.session_state['teacher_login_type'] = "login"
            st.session_state['student_login_mode'] = 'face'
            st.session_state['show_voice_reg_form'] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ========================== 1. FACE ID LOGIN ==========================
    if st.session_state.student_login_mode == 'face':
        st.header('Login Using FaceID')
        st.markdown("<br>", unsafe_allow_html=True)

        show_registration = False
        photo_source = st.camera_input("Position your face in the center")

        # Controlled gap between camera widget and voice option
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        if st.button("🎙️ Login Using Voice", type="secondary", use_container_width=True, icon=":material/mic:"):
            st.session_state.student_login_mode = 'voice'
            st.session_state.show_voice_reg_form = False
            st.rerun()

        if photo_source:
            img = np.array(Image.open(photo_source))

            with st.spinner('AI is scanning...'):
                detected, all_ids, num_faces = predict_attendance(img)

                if num_faces == 0:
                    st.warning('Face not found! Please look directly at the camera.')
                elif num_faces > 1:
                    st.warning('Multiple faces found! Only one student can verify at a time.')
                else:
                    if detected:
                        student_id = list(detected.keys())[0]
                        all_students = get_all_students()

                        student = next(
                            (s for s in all_students if str(s.get('student_id') or s.get('id')) == str(student_id)),
                            None
                        )

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

                if st.button('Create Account', type='primary', use_container_width=True):
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

    # ========================== 2. VOICE LOGIN ==========================
    elif st.session_state.student_login_mode == 'voice':
        st.header('Login Using Voice')
        st.markdown("<br>", unsafe_allow_html=True)

        voice_audio = st.audio_input("Speak verification phrase (e.g. 'I am present')", key="student_voice_login")

        # Controlled vertical gap before action buttons
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("📸 Back to FaceID", type="secondary", use_container_width=True, icon=":material/ar_on_you:"):
                st.session_state.student_login_mode = 'face'
                st.session_state.show_voice_reg_form = False
                st.rerun()

        with col_v2:
            if st.button("Verify Voice", type="primary", use_container_width=True, icon=":material/verified:"):
                if voice_audio:
                    with st.spinner("Analyzing voice print..."):
                        current_voice_emb = get_voice_embedding(voice_audio.read())
                        all_students = get_all_students()

                        matched_student = None
                        highest_similarity = -1.0

                        for s in all_students:
                            stored_emb = s.get('voice_embedding')
                            if stored_emb:
                                v1 = np.array(current_voice_emb)
                                v2 = np.array(stored_emb)
                                norm_prod = np.linalg.norm(v1) * np.linalg.norm(v2)
                                if norm_prod > 0:
                                    score = float(np.dot(v1, v2) / norm_prod)
                                    if score > 0.75 and score > highest_similarity:
                                        highest_similarity = score
                                        matched_student = s

                        if matched_student:
                            st.session_state.is_logged_in = True
                            st.session_state.user_role = 'student'
                            st.session_state.student_data = matched_student
                            st.session_state.show_voice_reg_form = False
                            st.toast(f"Voice verified! Welcome, {matched_student['name']}!", icon="🎙️")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Voice not recognized or not yet registered.")
                            st.session_state.show_voice_reg_form = True
                else:
                    st.warning("Please record your voice first.")

        # Show voice registration container when voice is not recognized
        if st.session_state.show_voice_reg_form:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.subheader("🎙️ Register Voice Profile")
                st.caption("No matching voice profile found. Enter your details to create or link your voice print.")

                reg_name = st.text_input("Enter your full name", placeholder="E.g. Subhadeep Pandey", key="voice_reg_name_input")
                reg_photo = st.camera_input("Take a photo to register Face ID as well (Optional)", key="voice_reg_cam_input")

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

                if st.button("Register Voice & Login", type="primary", use_container_width=True, icon=":material/person_add:"):
                    if not reg_name.strip():
                        st.warning("Please enter your name.")
                    elif voice_audio is None:
                        st.warning("Please record your voice above before registering.")
                    else:
                        with st.spinner("Registering voice profile..."):
                            # Read recorded audio buffer
                            voice_emb = get_voice_embedding(voice_audio.read())

                            face_emb = None
                            if reg_photo is not None:
                                img = np.array(Image.open(reg_photo))
                                encoding = get_face_embeddings(img)
                                if encoding:
                                    face_emb = encoding[0].tolist()

                            # Check if student name already exists in database
                            all_students = get_all_students()
                            existing_student = next(
                                (s for s in all_students if s.get('name', '').strip().lower() == reg_name.strip().lower()),
                                None
                            )

                            if existing_student:
                                student_id_val = existing_student.get('student_id') or existing_student.get('id')
                                update_payload = {'voice_embedding': voice_emb}
                                if face_emb and not existing_student.get('face_embedding'):
                                    update_payload['face_embedding'] = face_emb

                                supabase.table('students').update(update_payload).eq('student_id', student_id_val).execute()
                                existing_student.update(update_payload)
                                registered_student = existing_student
                            else:
                                created = create_student(reg_name.strip(), face_embedding=face_emb, voice_embedding=voice_emb)
                                registered_student = created[0] if created else None

                            if registered_student:
                                if face_emb:
                                    train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = registered_student
                                st.session_state.show_voice_reg_form = False
                                st.toast(f"Profile registered successfully! Hi {reg_name}!", icon="🎉")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to register profile. Please try again.")

    footer_dashboard()