from services.supabase_client import get_supabase

def save_session(user_id: str, dwell: list, flight: list, meta: dict):
    supabase = get_supabase()

    supabase.table('keystroke_sessions').insert({
        'user_id':         user_id,
        'dwell':           dwell,
        'flight':          flight,
        'backspace_count': meta.get('backspace_count', 0),
        'paste_detected':  meta.get('paste_detected', False),
        'is_synthetic':    False
    }).execute()

def get_sessions(user_id: str) -> list:
    supabase = get_supabase()

    result = supabase.table('keystroke_sessions') \
        .select('*') \
        .eq('user_id', user_id) \
        .eq('is_synthetic', False) \
        .order('created_at') \
        .execute()

    return result.data