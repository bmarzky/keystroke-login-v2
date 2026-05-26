import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY              = os.getenv('SECRET_KEY', 'dev-secret')
    SUPABASE_URL            = os.getenv('SUPABASE_URL')
    SUPABASE_KEY            = os.getenv('SUPABASE_KEY')
    MIN_PASSWORD_LENGTH     = int(os.getenv('MIN_PASSWORD_LENGTH', 6))
    MAX_LOGIN_BEFORE_ACTIVE = int(os.getenv('MAX_LOGIN_BEFORE_ACTIVE', 5))

    @classmethod
    def validate(cls):
        missing = []
        if not cls.SUPABASE_URL: missing.append('SUPABASE_URL')
        if not cls.SUPABASE_KEY: missing.append('SUPABASE_KEY')
        if missing:
            raise ValueError(f"ENV tidak lengkap: {', '.join(missing)}")