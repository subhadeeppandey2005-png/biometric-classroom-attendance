import streamlit as st
from src.Components.header import header_home
from src.UI.base_layout import style_base_layout,style_background_home
from src.Components.footer import footer_home

def home_screen():
    

    header_home()
    style_background_home()
    style_base_layout()
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.header("I'm Student")
        st.image("https://i.ibb.co/844D9Lrt/mascot-student.png", width=120)
        if st.button('Student Portal', type='primary', icon=':material/arrow_outward:'):
            st.session_state['login_type'] = 'student'
            st.rerun()

    with col2:
        st.header("I'm Teacher")
        st.image("https://i.ibb.co/CsmQQV6X/mascot-prof.png", width=142)
        if st.button('Teacher Portal', type='primary', icon=':material/arrow_outward:'):
            st.session_state['login_type'] = 'teacher'
            st.rerun()



    footer_home()