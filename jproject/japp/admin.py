from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    search_fields = ('user__username', 'role')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'address', 'dob', 'education', 'work_experience', 'skills')
    search_fields = ('user__username', 'phone', 'address')
    list_filter = ('dob', 'skills')
    ordering = ('user',)


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'address', 'phone', 'website', 'founded_date', 'number_of_employees')
    search_fields = ('company_name', 'user__username', 'phone', 'website')
    list_filter = ('founded_date',)
    ordering = ('company_name',)
    
@admin.register(Jobs)
class JobsAdmin(admin.ModelAdmin):
    list_display = ('jobtitle', 'company', 'location', 'salrange', 'is_active', 'date_posted', 'application_deadline')
    search_fields = ('jobtitle', 'company__company_name', 'location', 'job_type')
    list_filter = ('is_active', 'job_type', 'date_posted')
    ordering = ('-date_posted',)

@admin.register(UserJobApplication)
class UserJobApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'comp', 'application_date', 'status', 'resume')
    search_fields = ('applicant__username', 'job__jobtitle', 'comp__company_name', 'status')
    list_filter = ('status', 'application_date')
    ordering = ('-application_date',)
    
@admin.register(Premiums)
class PremiumsAdmin(admin.ModelAdmin):
    list_display = ('user', 'premium_start_date', 'premium_end_date', 'is_active')
    search_fields = ('user__username',)
    list_filter = ('is_active',)
    ordering = ('-premium_start_date',)
