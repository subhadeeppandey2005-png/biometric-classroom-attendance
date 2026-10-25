import streamlit as st
from PIL import Image


@st.dialog("Capture or upload photo")
def add_photos_dialog(*args, **kwargs):
    st.caption("Add classroom photos to scan for attendance")

    # Ensure attendance image list exists in session state
    if "attendance_images" not in st.session_state:
        st.session_state.attendance_images = []

    tab_cam, tab_upload = st.tabs(["📸 Camera", "📁 Upload Photos"])

    cam_photo = None
    uploaded_files = None

    with tab_cam:
        cam_photo = st.camera_input("Take Snapshot", key="dialog_camera_widget")

    with tab_upload:
        uploaded_files = st.file_uploader(
            "Choose classroom image files",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True,
            key="dialog_upload_widget"
        )

    # Show count of photos already collected
    queued_count = len(st.session_state.attendance_images)
    if queued_count > 0:
        st.info(f"Currently queued photos: **{queued_count}**")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        # Done button: commits any unsaved photo and closes modal
        if st.button("Done", type="primary", use_container_width=True):
            added = False

            if cam_photo is not None:
                st.session_state.attendance_images.append(Image.open(cam_photo))
                added = True

            if uploaded_files:
                for f in uploaded_files:
                    st.session_state.attendance_images.append(Image.open(f))
                added = True

            if added:
                st.toast("Photos added to queue!", icon="✅")

            st.rerun()

    with col2:
        if st.button("Cancel", type="secondary", use_container_width=True):
            st.rerun()