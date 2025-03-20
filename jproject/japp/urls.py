from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from japp import views
from .views import company_profile_view
urlpatterns = [

    path('',views.jobs),
    path('register',views.register),
    path('login_view',views.login_view, name='login_view'),
    path('logout',views.user_logout),

    path('job_details/<int:jid>/', views.job_details, name='job_details'),  
    path('catfilter/<cat>/', views.catfilter, name='catfilter'),
    path('datefilter',views.datefilter ,name='filter_jobs_by_date'),
    path('salfilter',views.salfilter,name='filter_jobs_by_sal'),
    path('user_profile',views.user_profile,name='user_profile'),
    path('create_user_profile',views.create_user_profile,name='create_user_profile'),
    path('edit_user_profile',views.edit_user_profile,name='edit_user_profile'),

    path('company_view',views.company_view,name='company_view'),
    path('company_profile/', company_profile_view, name='company_profile'),
    path('create_company_profile/', views.create_company_profile, name='create_company_profile'),
    path('edit_company_profile',views.edit_company_profile, name='edit_company_profile'),
    path('post_job',views.post_job,name='post_job'),
    path('applicationsubmit',views.applicationsubmit),

    path('edit_job/<jid>/',views.edit_job),
    path('delete_job/<jid>/',views.delete_job),

    path('application_form/<jid>/<cid>',views.application_form),
    path('appliedjobuserview',views.appliedjobuserview),
    path('delete-application/<int:aid>/', views.delete_application, name='delete_application'),
    path('update_application/<aid>/<jid>/', views.update_application),
    path('delete_application/<jid>',views.delete_application),
    path('see_application_for_company/', views.see_application_for_company, name='see_application_for_company'),  

    path('update_application_status/<jid>',views.update_application_status),
    path('delete_application_for_company/<jid>',views.delete_application_for_company),
    path('premium_form_view',views.premium_form_view,name='premium_form_view'),
    path('paymentsuccess/', views.paymentsuccess, name='paymentsuccess')


]
urlpatterns+=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)