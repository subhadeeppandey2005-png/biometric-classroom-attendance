import time
import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

from src.UI.base_layout import style_background_dashboard, style_base_layout
from src.Components.header import header_dashboard
from src.Components.footer import footer_dashboard
from src.Components.subject_card import subject_card
from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects, get_attendance_for_teacher
from src.Components.dialog_create_subject import create_subject_dialog
from src.Components.dialog_share_subject import share_subject_dialog
from src.Components.dialog_add_photo import add_photos_dialog
from src.pipelines.face_pipeline import predict_attendance
from src.database.config import supabase
from src.Components.dialog_attendance_results import attendance_result_dialog

try:
    from src.Components.dialog_voice_attendance import voice_attendance_dialog
except ImportError:
    voice_attendance_dialog = None


def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type is None:
        st.session_state.teacher_login_type = "login"

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, {teacher_data.get('name', '')}")
        st.markdown('<div style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("Logout", type='secondary', key='logout_btn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            if 'teacher_data' in st.session_state:
                del st.session_state.teacher_data
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'

    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('Take Attendance', type=type1, use_container_width=True, icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Manage Subjects', type=type2, use_container_width=True, icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button('Attendance Records', type=type3, use_container_width=True, icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()

    elif st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()

    elif st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    footer_dashboard()


def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data.get('teacher_id') or st.session_state.teacher_data.get('id')

    st.header('Take AI Attendance')

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []
    if 'attendance_mode' not in st.session_state:
        st.session_state.attendance_mode = 'face'

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning('You have not created any subject yet. Please create one in Manage Subjects!')
        return

    subject_map = {f"{s['name']} ({s['subject_code']})": s for s in subjects}

    # 1. Subject selector
    selected_label = st.selectbox('Select Subject', options=list(subject_map.keys()))
    selected_subject = subject_map[selected_label]
    selected_subject_id = selected_subject['subject_id']

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Mode Selector: Choose attendance mode before capturing photos
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        face_btn_type = "primary" if st.session_state.attendance_mode == 'face' else "secondary"
        if st.button("📸 Face Recognition Mode", type=face_btn_type, use_container_width=True, icon=":material/ar_on_you:"):
            st.session_state.attendance_mode = 'face'
            st.rerun()

    with mode_col2:
        voice_btn_type = "primary" if st.session_state.attendance_mode == 'voice' else "secondary"
        if st.button("🎙️ Voice Attendance Mode", type=voice_btn_type, use_container_width=True, icon=":material/mic:"):
            st.session_state.attendance_mode = 'voice'
            st.rerun()

    st.divider()

    # 3A. Voice Attendance Flow
    if st.session_state.attendance_mode == 'voice':
        st.subheader("🎙️ Voice Roll Call")
        st.caption(f"Taking attendance via speech recognition for **{selected_subject['name']}**")

        v_col1, v_col2 = st.columns([2, 1], vertical_alignment='center')
        with v_col1:
            st.info("Click 'Start Listening' to speak student names or roll numbers into your microphone.")
        with v_col2:
            if st.button("Start Listening", type="primary", use_container_width=True, icon=":material/mic:"):
                if voice_attendance_dialog:
                    voice_attendance_dialog(selected_subject_id, selected_subject['name'])
                else:
                    st.info("Voice Attendance feature dialog is currently being configured.")

    # 3B. Face Recognition Flow
    elif st.session_state.attendance_mode == 'face':
        st.subheader("📸 Face Recognition Attendance")

        # Always-available top action bar
        act_col1, act_col2, act_col3 = st.columns(3)

        with act_col1:
            if st.button('Add photos', type='primary', icon=":material/photo_prints:", use_container_width=True):
                st.session_state['selected_attendance_subject_id'] = selected_subject_id
                st.session_state['selected_attendance_subject_name'] = selected_subject['name']
                add_photos_dialog(selected_subject_id, selected_subject['name'])

        with act_col2:
            has_photos = len(st.session_state.attendance_images) > 0
            if st.button('Run Face analysis', use_container_width=True, type='secondary', icon=':material/analytics:', disabled=not has_photos):
                with st.spinner('Deep scanning classroom photos...'):
                    all_detected_ids = {}

                    # Process all photos through the face pipeline
                    for idx, img in enumerate(st.session_state.attendance_images):
                        img_np = np.array(img.convert('RGB'))
                        detected, _, _ = predict_attendance(img_np)

                        if detected:
                            for sid in detected.keys():
                                try:
                                    student_id = int(sid)
                                    all_detected_ids.setdefault(student_id, []).append(f"Photo {idx+1}")
                                except (ValueError, TypeError):
                                    all_detected_ids.setdefault(sid, []).append(f"Photo {idx+1}")

                    # Fetch all enrolled students for this subject
                    enrolled_res = supabase.table('subject_students') \
                        .select("*, students(*)") \
                        .eq('subject_id', selected_subject_id) \
                        .execute()

                    enrolled_students = enrolled_res.data or []

                    if not enrolled_students:
                        st.warning('No students are enrolled in this subject yet.')
                    else:
                        results = []
                        attendance_to_log = []
                        current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                        # Match detections with enrollment roster
                        for node in enrolled_students:
                            student = node.get('students')
                            if not student:
                                continue

                            student_id_val = student.get('student_id') or student.get('id')
                            try:
                                sid_lookup = int(student_id_val)
                            except (ValueError, TypeError):
                                sid_lookup = student_id_val

                            sources = all_detected_ids.get(sid_lookup, [])
                            is_present = len(sources) > 0

                            results.append({
                                "Name": student.get('name', 'N/A'),
                                "ID": student_id_val,
                                "Source": ", ".join(sources) if is_present else "-",
                                "Status": "✅ Present" if is_present else "❌ Absent"
                            })

                            attendance_to_log.append({
                                'student_id': student_id_val,
                                'subject_id': selected_subject_id,
                                'timestamp': current_timestamp,
                                'is_present': bool(is_present)
                            })

                        attendance_result_dialog(pd.DataFrame(results), attendance_to_log)

        with act_col3:
            if st.button('Clear all photos', use_container_width=True, type='tertiary', icon=':material/delete:', disabled=not has_photos):
                st.session_state.attendance_images = []
                st.rerun()

        # Display gallery when photos are queued
        if st.session_state.attendance_images:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Added Photos")
            gallery_cols = st.columns(min(len(st.session_state.attendance_images), 4))

            for idx, img in enumerate(st.session_state.attendance_images):
                with gallery_cols[idx % 4]:
                    st.image(img, use_container_width=True, caption=f'Photo {idx+1}')
        else:
            st.info("No photos added yet. Click **Add photos** above to snap a classroom snapshot or upload files.")


def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data.get('teacher_id') or st.session_state.teacher_data.get('id')

    col1, col2 = st.columns(2)
    with col1:
        st.header('Manage Subjects')

    with col2:
        if st.button('Create New Subject', use_container_width=True):
            create_subject_dialog(teacher_id)

    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for sub in subjects:
            total_students = sub.get('total_students', 0)
            total_classes = sub.get('total_classes', 0)

            stats = [
                ("👥", "Students", total_students),
                ("🕰️", "Classes", total_classes),
            ]

            def make_share_btn(current_sub):
                def share_btn():
                    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                    if st.button(
                        f"Share Code: {current_sub['name']}",
                        key=f"share_{current_sub['subject_code']}",
                        icon=":material/share:"
                    ):
                        share_subject_dialog(current_sub['name'], current_sub['subject_code'])
                return share_btn

            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub.get('section', ''),
                stats=stats,
                footer_callback=make_share_btn(sub)
            )
    else:
        st.info("NO SUBJECTS FOUND. CREATE ONE ABOVE")


def teacher_tab_attendance_records():
    st.header('Attendance Records')

    teacher_id = st.session_state.teacher_data['teacher_id']
    records = get_attendance_for_teacher(teacher_id)
    if not records:
        return
    data = []

    for r in records:
        ts = r.get('timestamp')
        data.append({
            "ts_group": ts.split(".")[0] if ts else None,
            "Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N/A", 
            "Subject": r['subjects']['name'],  # <-- Comma added here
            "Subject Code": r['subjects']['subject_code'],
            "is_present": bool(r.get('is_present', False))
        })

        df = pd.DataFrame(data)

        summary = (
            df.groupby(['ts_group', 'Time', 'Subject', 'Subject Code'])
            .agg(
                Present_Count = ('is_present', 'sum'),
                Total_Count = ('is_present', 'count')
            ).reset_index()
        )
        summary['Attendance Stats'] = (
            "✅ " + summary['Present_Count'].astype(str) + " /"
            + summary['Total_Count'].astype(str) + ' Students'
        )

        display_df = ( summary.sort_values(by='ts_group', ascending=False)
                      [['Time', 'Subject', 'Subject Code', 'Attendance Stats']]
                      )
        st.dataframe(display_df, use_container_width=True, hide_index = True)
    st.caption("Historical class attendance logs will be displayed here.")


def login_teacher(username, password):
    if not username or not password:
        return False

    teacher = teacher_login(username, password)
    if teacher:
        st.session_state.user_role = 'teacher'
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True

    return False


def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.markdown('<div style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("Back", type='secondary', key='login_back_btn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.session_state['teacher_login_type'] = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.header('Login Using Password')
    st.markdown("<br>", unsafe_allow_html=True)

    teacher_username = st.text_input("Enter username", placeholder='subhadeep', key='login_user')
    teacher_password = st.text_input("Enter password", type='password', placeholder='••••', key='login_pass')

    st.divider()

    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button('Login', type='secondary', icon=':material/passkey:', shortcut='control+enter', use_container_width=True, key='login_submit_btn'):
            if teacher_username and teacher_password:
                if login_teacher(teacher_username, teacher_password):
                    st.toast("Welcome back!", icon="👋")
                    st.success(f"Welcome, {teacher_username}!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please enter your username and password.")

    with btnc2:
        if st.button('Register', type="primary", icon=':material/person_add:', shortcut='shift+enter', use_container_width=True, key='goto_reg_btn'):
            st.session_state.teacher_login_type = 'register'
            st.rerun()

    footer_dashboard()


def register_teacher(teacher_username, teacher_name, teacher_password, teacher_pass_confirm):
    if not teacher_username or not teacher_name or not teacher_password:
        return False, "All fields are required!"
    if check_teacher_exists(teacher_username):
        return False, "Username already taken."
    if teacher_password != teacher_pass_confirm:
        return False, "Passwords do not match."

    try:
        create_teacher(teacher_username, teacher_password, teacher_name)
        return True, "Successfully registered! Please login."
    except Exception as e:
        return False, f"Unexpected error: {e}"


def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.markdown('<div style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("Go back to Home", type='secondary', key='register_back_btn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.session_state['teacher_login_type'] = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.header('Register your teacher profile')
    st.markdown("<br>", unsafe_allow_html=True)

    teacher_username = st.text_input("Enter username", placeholder='abhishek', key='reg_user')
    teacher_name = st.text_input("Enter name", placeholder='Abhishek Bachchan', key='reg_name')
    teacher_password = st.text_input("Enter password", type='password', placeholder='••••', key='reg_pass')
    teacher_password_confirm = st.text_input("Confirm your password", type='password', placeholder='••••', key='reg_pass_confirm')

    st.divider()

    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button('Login Instead', type='secondary', icon=':material/passkey:', shortcut='shift+enter', use_container_width=True, key='goto_login_btn'):
            st.session_state.teacher_login_type = 'login'
            st.rerun()

    with btnc2:
        if st.button('Register now', type='primary', icon=':material/person_add:', shortcut='control+enter', use_container_width=True, key='reg_submit_btn'):
            success, message = register_teacher(
                teacher_username,
                teacher_name,
                teacher_password,
                teacher_password_confirm
            )
            if success:
                st.success(message)
                time.sleep(1)
                st.session_state.teacher_login_type = 'login'
                st.rerun()
            else:
                st.error(message)

    footer_dashboard()