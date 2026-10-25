import streamlit as st

import segno
import io



@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    app_domain = "http://localhost:8501/"
    join_url = f"{app_domain}/?join-code={subject_code}"


    st.header("Scan to join")


    qr = segno.make(join_url)

    out = io.BytesIO()

    qr.save(out, kind='png', scale=10, border=1)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### copy link')
        st.code(join_url, language="text")
        st.code(subject_code, language="text")
        st.info('Copy this link to share on whatsapp or email')

    with col2:
        st.markdown('### scan to join')
        st.image(out.getvalue(), caption='QR CODE for class joining')
