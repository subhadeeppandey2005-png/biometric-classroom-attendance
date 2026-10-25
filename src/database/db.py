from src.database.config import supabase
import bcrypt


def hash_pass(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_pass(pwd: str, hashpwd: str) -> bool:
    try:
        return bcrypt.checkpw(pwd.encode('utf-8'), hashpwd.encode('utf-8'))
    except Exception:
        return False


def check_teacher_exists(username: str) -> bool:
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0


def create_teacher(username: str, password: str, name: str):
    data = {
        "username": username,
        "password": hash_pass(password),
        "name": name
    }
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username: str, password: str):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        stored_hash = teacher.get('password', '')
        if check_pass(password, stored_hash):
            return teacher
    return None


def get_all_students():
    response = supabase.table('students').select("*").execute()
    return response.data


def create_student(new_name, face_embedding=None, voice_embedding=None):
    data = {
        'name': new_name,
        'face_embedding': face_embedding,
        'voice_embedding': voice_embedding
    }
    response = supabase.table('students').insert(data).execute()
    return response.data


def create_subject(subject_code, name, section, teacher_id):
    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id
    }
    response = supabase.table("subjects").insert(data).execute()
    return response.data


def get_teacher_subjects(teacher_id):
    try:
        # Fetch with relationships (student counts and class log timestamps)
        response = supabase.table('subjects').select(
            "*, subject_students(count), attendance_logs(timestamp)"
        ).eq("teacher_id", teacher_id).execute()

        subjects = response.data or []

        for sub in subjects:
            # Extract student count from the 'subject_students' relation
            students_info = sub.get("subject_students", [])
            sub['total_students'] = students_info[0].get('count', 0) if students_info else 0

            # Calculate unique session timestamps for total classes held
            attendance = sub.get('attendance_logs', [])
            unique_sessions = len(set(log['timestamp'] for log in attendance if 'timestamp' in log))
            sub['total_classes'] = unique_sessions

            # Clean up relation artifacts
            sub.pop('subject_students', None)
            sub.pop('attendance_logs', None)

        return subjects

    except Exception:
        # Fallback: Query directly from subjects if relational joins fail
        response = supabase.table('subjects').select("*").eq("teacher_id", teacher_id).execute()
        subjects = response.data or []
        for sub in subjects:
            sub['total_students'] = 0
            sub['total_classes'] = 0
        return subjects


def enroll_student_to_subject(student_id, subject_id):
    data = {'student_id': student_id, 'subject_id': subject_id}
    response = supabase.table('subject_students').insert(data).execute()
    return response.data

def unenroll_student_to_subject(student_id, subject_id):
    response = supabase.table('subject_students').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()

    return response.data


def get_student_subjects(student_id):
    response = supabase.table('subject_students').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def get_student_attendance(student_id):
    response = supabase.table('attendance_logs').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data



def create_attendance(logs):
    response = supabase.table('attendance_logs').insert(logs).execute()
    return response.data


def get_attendance_for_teacher(teacher_id):
    response = supabase.table('attendance_logs').select("*, subjects!inner(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data
