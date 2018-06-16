from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import ugettext_lazy as _

from .models import KioskUser


# Base Form for the flexUserAdmin
class MyUserChangeForm(UserChangeForm):
	class Meta(UserChangeForm.Meta):
		model = KioskUser

# Modified UserAdmin with additional fieldsets to adjust in the admin area
# Also modify the view for non-Superuser staff -> restricted rights
class KioskUserAdmin(UserAdmin):
	
	# New User Form in Admin area
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('username','password1','password2','aktivBis','slackName')
		}),
	)

	form = MyUserChangeForm

	# Add Verification and Approvement variables for view and modification
	superuser_fieldsets = UserAdmin.fieldsets + (
		(_('Slack'), {'fields': ('slackName',),}),
		( _('Verification and Approvement'), {'fields': ('is_verified',)}),
		(_('Kiosk Specific'), {'fields': ('aktivBis','instruierterKaeufer','rechte','visible','activity_end_msg','dsgvo_accepted',),},),
	)

	# Restricted views for non-superuser staff
	staff_fieldsets = (
		(None, {'fields': ('username', 'password')}),
		(_('Personal Info'), {'fields': ('first_name', 'last_name', 'email','slackName')}),
		(_('Important dates'), {'fields': ('last_login', 'date_joined')}),
		( _('Verification and Approvement'), {'fields': ('is_verified',)}),
		(_('Kiosk Specific'), {'fields': ('aktivBis','instruierterKaeufer','rechte','visible','activity_end_msg','dsgvo_accepted',),},),
	)

	# Change the view, when staff or superuser accesses the page
	def change_view(self, request, *args, **kwargs):

		if not request.user.is_superuser:
			self.fieldsets = self.staff_fieldsets
		else:
			self.fieldsets = self.superuser_fieldsets

		return super(KioskUserAdmin, self).change_view(request, *args, **kwargs)

	# When a user is modified by an admin or staff member, look, if the user is now accepted by the flex platform. Then send a confirmation mail.
	def save_model(self, request, obj, form, change):

		# ToDo: If no Kontostand exists (z.B. from creating a user in admin area), a Kontostand has to be created
		#k = Kontostand(nutzer_id = user.id, stand=0)
		#k.save()

		super().save_model(request, obj, form, change)


# Register
admin.site.register(KioskUser, KioskUserAdmin)