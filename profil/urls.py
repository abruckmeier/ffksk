from django.conf.urls import url
from django.contrib.auth import views

from . import views as profilViews
from . import forms




urlpatterns = [
    
    #url(r'^accounts/login/$', views.login, name='login'),
    #url(r'^accounts/logout/$', views.logout, name='logout', kwargs={'next_page': '/'}),
    
    url(r'^accounts/password/change/$', views.PasswordChangeView.as_view(template_name='registration/password_change.html'), name='password_change'),
    url(r'^accounts/password/change/done/$', views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),

    url(r'^accounts/password/reset/$', views.PasswordResetView.as_view(template_name='registration/password_reset_form.html', form_class=forms.SlackResetForm, email_template_name='registration/password_reset_message.html', subject_template_name='registration/password_reset_subject.html', ), name='password_reset'),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    url(r'^accounts/password/reset/done/$', views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    url(r'^accounts/password/reset/complete/$', views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    url(r'^accounts/angestellt_bis_change/$', profilViews.angestellt_bis_change, name='angestellt_bis_change'),
    url(r'^accounts/angestellt_bis_changed/$', profilViews.angestellt_bis_changed, name='angestellt_bis_changed'),

    url(r'^accounts/registrationStatus/$', profilViews.registrationStatus.as_view(), name='registrationStatus'),
    url(r'^accounts/activate/(?P<uidb64>[0-9A-Za-z_]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', profilViews.AccountActivate.as_view(), name='account_activate'),
]
