from .start import start
from .profile import handle_profile_callback, edit_name, handle_upload_photo, get_name, get_age, get_gender
from .application import handle_document, get_app_id
from .specialty import choose_specialty, handle_specialty_action
from .email import (
    get_email, ask_email_code, confirm_email, confirm_email_callback,
    edit_email, confirm_edit_email, confirm_edit_email_callback
)
from .common import (
    send_main_menu, handle_main_menu_text, error_handler, fallback_text_handler,
    menu_command, handle_callback, handle_specialty_text_fallback
)
from .faq import handle_faq_callback, handle_faq_text, show_faq_page
from .admin import process_admin_response, show_pending_applications, handle_admin_callback

__all__ = [
    'handle_faq_callback',
    'handle_faq_text',
    'show_faq_page',
    # ... остальные экспорты ...
]