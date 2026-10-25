import streamlit as st
import pandas as pd
from datetime import datetime
from src.database.config import supabase
from src.pipelines.voice_pipelines import process_bulk_audio
from src.Components.dialog_attendance_results import show_attendance_result


@st.dialog('Voice Attendance')
def voice_attendance_dialog(selected_subject_id, subject_name=None, *args, **kwargs):
    if subject_name:
        st.caption(f"Taking voice attendance for **{subject_name}**")
    st.write("Record audio of students speaking roll call phrases (e.g., *'I am present'*). AI will identify and match enrolled student voices.")

    audio_data = st.audio_input("Record classroom audio", key="voice_attendance_audio_input")

    col_btn1, col_btn2 = st.columns([2, 1])

    with col_btn1:
        analyze_clicked = st.button('Analyze Audio', use_container_width=True, type='primary')

    with col_btn2:
        if st.button('Close', use_container_width=True, type='secondary'):
            if 'voice_attendance_results' in st.session_state:
                del st.session_state.voice_attendance_results
            st.rerun()

    if analyze_clicked:
        if audio_data is None:
            st.warning("Please record classroom audio before clicking 'Analyze Audio'.")
            return

        with st.spinner('Processing audio and matching voice embeddings...'):
            enrolled_res = supabase.table('subject_students') \
                .select("*, students(*)") \
                .eq('subject_id', selected_subject_id) \
                .execute()

            enrolled_students = enrolled_res.data or []

            if not enrolled_students:
                st.warning('No students are enrolled in this subject.')
                return

            # Build candidates dictionary with both int and string keys so matching never fails due to type mismatch
            candidates_dict = {}
            for s in enrolled_students:
                student_node = s.get('students')
                if student_node and student_node.get('voice_embedding'):
                    sid = student_node.get('student_id') or student_node.get('id')
                    # Populate both string and int representations
                    candidates_dict[str(sid)] = student_node['voice_embedding']
                    try:
                        candidates_dict[int(sid)] = student_node['voice_embedding']
                    except (ValueError, TypeError):
                        pass

            if not candidates_dict:
                st.error('None of the enrolled students have voice profiles registered.')
                return

            # Safely extract audio bytes using getvalue() to prevent empty buffer reads
            if hasattr(audio_data, 'getvalue'):
                audio_bytes = audio_data.getvalue()
            else:
                audio_data.seek(0)
                audio_bytes = audio_data.read()

            detected_scores = process_bulk_audio(audio_bytes, candidates_dict) or {}

            # Temporary diagnostic expander to inspect the raw output from process_bulk_audio
            with st.expander("🔍 Diagnostic: Raw Audio Scores", expanded=False):
                st.write("Candidates Checked:", list(candidates_dict.keys()))
                st.write("Detected Scores Returned:", detected_scores)

            results = []
            attendance_to_log = []
            current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            # Match detections against full class roster
            for node in enrolled_students:
                student = node.get('students')
                if not student:
                    continue

                sid_raw = student.get('student_id') or student.get('id')
                try:
                    student_id_int = int(sid_raw)
                except (ValueError, TypeError):
                    student_id_int = sid_raw

                # Check string, int, and raw key in detected_scores
                score = (
                    detected_scores.get(str(sid_raw))
                    or detected_scores.get(student_id_int)
                    or detected_scores.get(sid_raw)
                    or 0.0
                )

                try:
                    score_val = float(score)
                except (ValueError, TypeError):
                    score_val = 0.0

                # Mark present if similarity score indicates a match (> 0)
                is_present = bool(score_val > 0.0)

                results.append({
                    "Name": student.get('name', 'N/A'),
                    "ID": student_id_int,
                    "Score": f"{score_val:.2f}" if is_present else "-",
                    "Status": "✅ Present" if is_present else "❌ Absent"
                })

                attendance_to_log.append({
                    'student_id': student_id_int,
                    'subject_id': selected_subject_id,
                    'timestamp': current_timestamp,
                    'is_present': bool(is_present)
                })

            st.session_state.voice_attendance_results = (pd.DataFrame(results), attendance_to_log)

    # Render results table and confirmation actions directly in dialog
    if st.session_state.get('voice_attendance_results'):
        st.divider()
        df_results, logs = st.session_state.voice_attendance_results
        show_attendance_result(df_results, logs)