import streamlit as st
def subject_card(name, code, section, stats=None, footer_callback=None):
    html = f"""
        <div style="background_color:white; border-left: 8px solid #EB45E; padding:25px; border-radius: 20px; border: 1px solid black; margin-bototm:20
        <h3 style="margin:0; color: 1e293b; font_size: 1.5rem | ">{name}</h3>
        <p style="color:#64748b; margin: 10px 0;">Code :<span style="background_color:#E0E3FF; color:#5865F2; padding:2px 8px; border-radius:5px;">{code} </span> | section : {section} </p>

        """

    if stats:
        html+="""
        <div style="display:flex; gap:8px; flex-wrap;">
        """

        for icon, label, value in stats:
            html+= f'<div style="background: EB459E10; padding:5px 12px; border-radius:12px; font-size: 0.9rem">{icon} <b>{value}</b> {label} </div>'


        html+= "</div>"


    st.markdown(html, unsafe_allow_html=True)

# Inside subject_card(...)
    if footer_callback:
        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
        footer_callback()

        