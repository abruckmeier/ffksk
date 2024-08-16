from django.contrib import admin
from paypal.models import Mail


@admin.register(Mail)
class MailAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_id', 'mail_ts', 'extraction_was_successful',
                    'assignment_was_successful', 'user_str',
                    'transaction_code')
    list_filter = ('extraction_was_successful', 'mail_ts', 'assignment_was_successful',
                   'user_str',)
    search_fields = ('envelope_str', 'message_id', 'data', 'user_str',
                     'transaction_code', 'notice')
    change_list_template = 'admin/mail_change_list.html'
