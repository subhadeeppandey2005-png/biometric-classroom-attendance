import time
import streamlit as st
from src.UI.base_layout import style_background_dashboard, style_base_layout
from src.Components.header import header_dashboard
from src.Components.footer import footer_dashboard
from src.database.db import check_teacher_exists, create_teacher, teacher_login


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
        st.subheader(f"""Welcome, {teacher_data['name']} """)
        st.markdown('<div style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("Logout", type='secondary', key='logout_btn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
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


    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()


    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    footer_dashboard()

def teacher_tab_take_attendance():
    st.header('Take AI Attendance')

def teacher_tab_manage_subjects():
    st.header('Manage Subjects')

def teacher_tab_attendance_records():
    st.header('Attendance Records')


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
    st.markdown("<br>", unsafe_allow_html=True)

    teacher_username = st.text_input("enter user name", placeholder='subhadeep', key='login_user')
    teacher_password = st.text_input("enter password", type='password', placeholder='123@', key='login_pass')

    st.divider()

    btnc1, btnc2 = st.columns(2)
    with btnc1:
        # Left Button: Pink Action Button
        if st.button('Login', type='secondary', icon=':material/passkey:', shortcut='control+enter', use_container_width=True, key='login_submit_btn'):
            if teacher_username and teacher_password:
                if login_teacher(teacher_username, teacher_password):
                    st.toast("Welcome back!", icon="👋")
                    st.success(f"Welcome, {teacher_username}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please enter your username and password.")

    with btnc2:
        # Right Button: Blue Switch Button
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
    teacher_password_confirm = st.text_input("Confirm your password", type='password', placeholder='Enter password', key='reg_pass_confirm')

    st.divider()

    btnc1, btnc2 = st.columns(2)
    
    # Left Column: Login Instead Switch Button
    with btnc1:
        if st.button('Login Instead', type='secondary', icon=':material/passkey:', shortcut='shift+enter', use_container_width=True, key='goto_login_btn'):
            st.session_state.teacher_login_type = 'login'
            st.rerun()

    # Right Column: Register Action Button
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
                time.sleep(1.5)
                st.session_state.teacher_login_type = 'login'
                st.rerun()
            else:
                st.error(message)

    footer_dashboard()