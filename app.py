import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.student_screen import student_screen
from src.screens.teacher_screen import teacher_screen
from src.Components.dialog_auto_enroll import auto_enroll_dialog


def main():
    st.set_page_config(
        page_title = 'SnapClass - Making Atendance faster using AI',
        page_icon="https://i.ibb.co/YTYGn5qV/logo.png"
    )
    # 1. Check for query parameter (handling both hyphen and underscore formats)
    join_code = st.query_params.get('join-code') or st.query_params.get('join_code')

    # 2. If a join link was accessed, force routing to student screen
    if join_code:
        st.session_state['pending_join_code'] = join_code
        if st.session_state.get('login_type') != 'student':
            st.session_state['login_type'] = 'student'

    # Initialize default login_type if still unset
    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None

    # 3. Route to the active screen
    match st.session_state['login_type']:
        case 'teacher':
            teacher_screen()

        case 'student':
            student_screen()

        case None:
            home_screen()

    # 4. Trigger auto-enroll dialog if the student is already authenticated
    if join_code and st.session_state.get('is_logged_in') and st.session_state.get('user_role') == 'student':
        auto_enroll_dialog(join_code)


if __name__ == '__main__':
    main()