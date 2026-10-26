import io
import segno
import streamlit as st


@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    # Strip any trailing slashes to guarantee exactly one slash before the query string
    app_domain = "snapclass-main.streamlit.app".rstrip("/")
    join_url = f"{app_domain}/?join-code={subject_code}"

    st.header(f"Join {subject_name}")

    qr = segno.make(join_url)
    out = io.BytesIO()
    qr.save(out, kind="png", scale=10, border=1)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Copy Link")
        st.code(join_url, language="text")
        st.markdown("### Subject Code")
        st.code(subject_code, language="text")
        st.info("Copy this link to share on WhatsApp or Email.")

    with col2:
        st.markdown("### Scan to Join")
        st.image(out.getvalue(), caption="QR Code for class joining", width=200)