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