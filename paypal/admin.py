from django.contrib import admin
from paypal.models import Mail, Token
from django.contrib import messages
from paypal.paypal_mail import assign_user_and_conduct_transaction, MailAssignmentResponse


@admin.register(Mail)
class MailAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_id', 'mail_ts', 'extraction_was_successful',
                    'assignment_was_successful', 'mail_is_processed', 'user_str',
                    'transaction_code')
    list_filter = ('extraction_was_successful', 'mail_ts', 'assignment_was_successful',
                   'mail_is_processed', 'user_str',)
    search_fields = ('message_id', 'user_str',
                     'transaction_code', 'notice', 'data', 'envelope_str')
    change_list_template = 'admin/mail_change_list.html'
    readonly_fields = ('geld_transaktion',)
    actions = ['create_transaction_from_details',]
    list_editable = ('mail_is_processed',)

    @admin.action(description='Create money transaction with given details.')
    def create_transaction_from_details(self, request, queryset):
        """Given the (manually modified) details from the mail, the transaction is created manually.
        This is, if there was a not automatically working incoming mail and we have to modify by hand."""
        for _mail in queryset:

            if _mail.geld_transaktion:
                self.message_user(
                    request,
                    f'(ID {_mail.id}) Geld-Transaktion bereits zugeordnet',
                    messages.ERROR,
                )
            elif not _mail.user_str or not _mail.transaction_code or not _mail.amount or not _mail.notice:
                self.message_user(
                    request,
                    f'(ID {_mail.id}) Es fehlen Details: User_str, Transaktions-Code, Betrag, Notiz',
                    messages.ERROR,
                )
            else:
                response: MailAssignmentResponse = assign_user_and_conduct_transaction(_mail)
                self.message_user(
                    request,
                    f'(ID {_mail.id}) {response.get("reason")}',
                    messages.SUCCESS if response.get('success') else messages.ERROR,
                )


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    pass
