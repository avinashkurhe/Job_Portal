from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator

# UserRole Model
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)

# UserProfile Model
class UserProfile(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, db_column='uid', related_name='profile')
    phone = models.CharField(max_length=15, blank=True, validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Phone number must be entered in the format: "+999999999".')])
    address = models.CharField(max_length=255, blank=True)
    dob = models.DateField(null=True, blank=True)
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True)  # Add resume field

# CompanyProfile Model
class CompanyProfile(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, db_column='uid')
    company_name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    website = models.URLField(blank=True)
    founded_date = models.DateField(null=True, blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True)
    description = models.TextField(blank=True)
    number_of_employees = models.IntegerField(null=True, blank=True)

# Jobs Model
class Jobs(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='jobs', default=1)    
    jobtitle = models.CharField(max_length=100)
    salrange = models.IntegerField()
    cat = models.CharField(max_length=100)
    jdetails = models.TextField()
    is_active = models.BooleanField(default=True)
    location = models.CharField(max_length=100)
    date_posted = models.DateTimeField(auto_now_add=True)
    application_deadline = models.DateTimeField()
    contact_email = models.EmailField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    job_type = models.CharField(max_length=50)
    experience_required = models.CharField(max_length=100)
    job_summary = models.TextField()
    required_skills = models.TextField()

    def __str__(self):
        return self.jobtitle

#User job application
class UserJobApplication(models.Model):
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE, related_name='jobs')
    comp= models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='company')
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Interview Scheduled', 'Interview Scheduled'),
        ('Offered', 'Offered'),
        ('Rejected', 'Rejected'),
    ], default='Pending')
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='applications/resumes/', blank=True)

    def __str__(self):
        return f"{self.applicant.username} applied for {self.job.jobtitle}"

#premium data
class Premiums(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    premium_start_date = models.DateField(auto_now_add=True)
    premium_end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


