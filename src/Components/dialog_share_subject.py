import io
import segno
import streamlit as st


@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    # Automatically grabs the active Streamlit domain or defaults to localhost
    host = st.context.headers.get("host", "localhost:8501")
    protocol = "https" if "streamlit.app" in host else "http"
    join_url = f"{protocol}://{host}/?join-code={subject_code}"
    
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