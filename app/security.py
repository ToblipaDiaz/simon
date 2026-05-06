from __future__ import annotations


DEFAULT_INSECURE_PASSWORDS = {"", "admin1234", "admin", "password", "changeme"}


def is_insecure_default_password(password: str) -> bool:
    return (password or "").strip() in DEFAULT_INSECURE_PASSWORDS


def validate_admin_password_policy(app_env: str, admin_password: str) -> None:
    if (app_env or "").strip().lower() == "production" and is_insecure_default_password(admin_password):
        raise RuntimeError("APP_ENV=production requiere PJ_ADMIN_PASSWORD seguro; no se permite contraseña admin por defecto.")

