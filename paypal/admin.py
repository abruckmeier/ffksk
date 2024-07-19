from django.contrib import admin
from paypal.models import Mail


@admin.register(Mail)
class MailAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_id', 'envelope_str', 'extraction_was_successful',
                    'assignment_was_successful', 'user_str', 'transaction_date',
                    'transaction_code')
    list_filter = ('extraction_was_successful', 'assignment_was_successful',
                   'user_str', 'transaction_date')
    search_fields = ('envelope_str', 'message_id', 'data', 'user_str',
                     'transaction_code')
