from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from japp.models import UserRole   
from japp.models import *
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from datetime import datetime  
from django.db import IntegrityError
import razorpay
from datetime import timedelta
import re
from django.utils import timezone


#REGISTER FORM FOR USER (COMPANY AND CANDIDATE)
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        context = {}
        r = request.POST.get('role', '').strip()
        fn = request.POST.get('fname', '').strip()
        ln = request.POST.get('lname', '').strip()
        e = request.POST.get('email', '').strip()
        p = request.POST.get('pass', '').strip()
        cp = request.POST.get('cpass', '').strip()

        context['role'] = r
        context['fname'] = fn
        context['lname'] = ln
        context['email'] = e

        if r not in ['Candidate', 'Company']:
            context['errmsg'] = 'Please select a valid role (Candidate or Company).'
        elif any(field == "" for field in [fn, ln, e, p, cp]):
            context['errmsg'] = 'All fields are mandatory.'
        elif not re.match(r'^[A-Za-z]{2,}$', fn):
            context['errmsg'] = 'First name must contain only letters and be at least 2 characters long.'
        elif not re.match(r'^[A-Za-z]{2,}$', ln):
            context['errmsg'] = 'Last name must contain only letters and be at least 2 characters long.'
        elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', e):
            context['errmsg'] = 'Please enter a valid email address.'
        elif p != cp:
            context['errmsg'] = 'Password and confirm password must be the same.'
        elif len(p) < 8:
            context['errmsg'] = 'Password must be at least 8 characters long.'
        elif not re.search(r'[A-Z]', p):  
            context['errmsg'] = 'Password must contain at least one uppercase letter.'
        elif not re.search(r'[a-z]', p):  
            context['errmsg'] = 'Password must contain at least one lowercase letter.'
        elif not re.search(r'[0-9]', p):  
            context['errmsg'] = 'Password must contain at least one number.'
        elif not re.search(r'[\W_]', p): 
            context['errmsg'] = 'Password must contain at least one special character.'
        else:
            try:
                user = User.objects.create_user(username=e, first_name=fn, last_name=ln, email=e, password=p)
                UserRole.objects.create(user=user, role=r)
                context['success'] = 'User created successfully. Please log in.'
                return redirect('login_view')
            except IntegrityError:
                context['errmsg'] = 'User already exists, please log in.'
        return render(request, 'register.html', context)
    

#LOGIN FORM FOR BOTH CANDIDATE,COMPANY & ADMIN
def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        context = {}
        e = request.POST.get('email')
        p = request.POST.get('pass')
        context['email'] = e
        context['pass'] = p
        u = authenticate(username=e, password=p)
        if u is None:
            context['errmsg'] = 'Invalid Credentials'
            return render(request, 'login.html', context)
        else:
            auth_login(request, u)
            try:
                user_role = UserRole.objects.get(user=u)
                if user_role.role == 'Candidate':
                    return redirect('/')
                else:
                    return redirect('company_view')
            except UserRole.DoesNotExist:
                context['errmsg'] = 'User role not found'
                return render(request, 'login.html', context)
            
#Logout
@login_required
def user_logout(request):
    logout(request)
    return redirect('/')


# 1 page JOBS CARD
def jobs(request):
    current_time = timezone.now()
    active_jobs = Jobs.objects.filter(is_active=True, application_deadline__gte=current_time)
    if request.user.is_authenticated:
        applied_job_ids = UserJobApplication.objects.filter(applicant=request.user).values_list('job_id', flat=True)
        available_jobs = active_jobs.exclude(id__in=applied_job_ids)
    else:
        available_jobs = active_jobs
    context = {'data': available_jobs}
    return render(request, 'user_home.html', context)

#JOB DETAIL

def job_details(request,jid):
    p=Jobs.objects.filter(id=jid)
    context={}
    context['data']=p
    return render(request,'job_details.html',context)

#Filter by category
def catfilter(request, cat):
    applied_jobs = UserJobApplication.objects.filter(applicant=request.user.id).values_list('job', flat=True)
    q1 = Q(cat=cat)
    q2 = Q(is_active=True)
    q3 = ~Q(id__in=applied_jobs)  # Exclude applied jobs
    q4 = Q(application_deadline__gte=timezone.now())  # Exclude expired jobs

    jobs = Jobs.objects.filter(q1 & q2 & q3 & q4)
    context = {'data': jobs}
    return render(request, 'user_home.html', context)

#filter by date
def datefilter(request):
    if request.method == 'GET':
        s = request.GET.get('start')
        e = request.GET.get('end')
        context = {}
        if s and e:
            try:
                start_date = datetime.strptime(s, '%Y-%m-%d')
                end_date = datetime.strptime(e, '%Y-%m-%d')
                if start_date > end_date:
                    context['derrmsg'] = "Start date should not be later than end date."
                else:
                    applied_jobs = UserJobApplication.objects.filter(applicant=request.user.id)
                    q1 = Q(date_posted__gte=start_date)  # Jobs posted on or after the start date
                    q2 = Q(application_deadline__lte=end_date)  # Jobs with deadline on or before the end date
                    q3 = Q(is_active=True)  # Only active jobs
                    q4 = ~Q(id__in=applied_jobs)  # Exclude applied jobs
                    p = Jobs.objects.filter(q1 & q2 & q3 & q4)
                    context['data'] = p
            except ValueError:
                context['derrmsg'] = "Please provide valid date values in the format YYYY-MM-DD."
        else:
            context['derrmsg'] = "Please provide both start and end dates."
        return render(request, 'user_home.html', context)
    
# Salary filter
def salfilter(request):
    if request.method == 'GET':
        min_sal = request.GET.get('minsal')
        max_sal = request.GET.get('maxsal')
        context = {} 
        if min_sal and max_sal:
            try:
                min_sal = float(min_sal)
                max_sal = float(max_sal)
                if min_sal > max_sal:
                    context['errmsg'] = "Minimum salary should not be greater than maximum salary."
                    return render(request, 'user_home.html', context)
                applied_jobs = UserJobApplication.objects.filter(applicant=request.user.id)
                q1 = Q(salrange__gte=min_sal)  
                q2 = Q(salrange__lte=max_sal)  
                q3 = Q(is_active=True)  
                q4 = ~Q(id__in=applied_jobs)  
                p = Jobs.objects.filter(q1 & q2 & q3 & q4)
                if p.exists():
                    context['data'] = p
                else:
                    context['errmsg'] = "No jobs found within the specified salary range."
            except ValueError:
                context['errmsg'] = "Please provide valid numeric values for the salary range."
        else:
            context['errmsg'] = "Please provide both a minimum and maximum salary."
        return render(request, 'user_home.html', context)

#USER PROFILE
@login_required
def user_profile(request):
    up = UserProfile.objects.filter(user_id=request.user.id)
    context = {}  
    context['data'] = up
    return render(request, 'user_profile.html', context)

#CREATE USER PROFILE
@login_required
def create_user_profile(request):
    if request.method == "GET":
        return render(request, 'createprofile.html')
    else:
        up=UserProfile.objects.filter(user_id=request.user.id)
        contaxt={}
        contaxt['data']=up
        fn = request.POST.get('fname')
        ln = request.POST.get('lname')
        ph = request.POST.get('phone')
        ad = request.POST.get('address')
        do = request.POST.get('dob')
        ed = request.POST.get('education')
        ex = request.POST.get('work_experience')
        sk = request.POST.get('skills')
        pp = request.FILES.get('profile_pic')
        resume = request.FILES.get('resume')
        if not fn or not ln:
            return render(request, 'createprofile.html', {'error': "Username, first name, and last name are required fields."})

        # Create or update User
        user = User.objects.get(id=request.user.id)
        user.first_name = fn
        user.last_name = ln
        user.save()

        up = UserProfile(
            user=user,
            phone=ph,
            address=ad,
            dob=do,
            education=ed,
            work_experience=ex,
            skills=sk,
            profile_pic=pp,
            resume=resume
        )
        up.save()
        return render(request, 'user_profile.html', contaxt)
    
#EDIT USER PROFILE
@login_required
def edit_user_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_profile.user.first_name = request.POST.get('fname', '')
        user_profile.user.last_name = request.POST.get('lname', '')
        user_profile.phone = request.POST.get('phone', '')
        user_profile.address = request.POST.get('address', '')
        user_profile.dob = request.POST.get('dob', '')
        user_profile.education = request.POST.get('education', '')
        user_profile.work_experience = request.POST.get('work_experience', '')
        user_profile.skills = request.POST.get('skills', '')
        # Check if a new profile picture is uploaded
        if 'profile_pic' in request.FILES:
            user_profile.profile_pic = request.FILES['profile_pic']
        if 'resume' in request.FILES:
            user_profile.resume = request.FILES['resume']
        # Save changes
        user_profile.save()
        user_profile.user.save()  # Save user model separately

        return redirect('user_profile')  # Redirect to the profile detail view
    # If not POST, render form or some other logic here
    return render(request, 'user_profile.html', {'user_profile': user_profile})

#COMPANY VIEW
@login_required
def company_view(request):
    try:
        company_profile = CompanyProfile.objects.get(user=request.user)
    except CompanyProfile.DoesNotExist:
        return redirect('create_company_profile')  # Assuming you have a URL named 'create_profile'
    jobs = Jobs.objects.filter(company=company_profile)
    context = {
        'data': jobs
    }
    return render(request, 'company/chome.html', context)

#COMPANY PROFILE
def company_profile_view(request):
    cp=CompanyProfile.objects.filter(user_id=request.user.id)
    context={}
    context['data']=cp
    return render(request, 'company/company_profile.html',context)
#CREATE COMPANY PROFILE
def create_company_profile(request):
    if request.method=="GET":
        return render(request, 'company/createcompanyprofile.html')
    elif request.method=="POST":
        cp = CompanyProfile.objects.filter(user_id=request.user.id)
        context = {'data': cp}
        fn = request.POST.get('fname')
        ln = request.POST.get('lname')
        cn = request.POST.get('company_name')
        ad = request.POST.get('address')
        ph = request.POST.get('phone')
        wb = request.POST.get('website')
        fd = request.POST.get('founded_date')
        dc = request.POST.get('description')
        ne = request.POST.get('number_of_employees')
        lo = request.FILES.get('logo')
        # Debugging print statement
        print('File Upload: ', lo)
        if not (cn and ad and ph and wb and fd and dc and ne and lo):
            return render(request, 'company/createcompanyprofile.html', {'error': "All fields are required."})
        user = User.objects.get(id=request.user.id)
        user.first_name = fn
        user.last_name = ln
        user.save()
        try:
            cp = CompanyProfile(
                user=user,
                company_name=cn,
                phone=ph,
                address=ad,
                website=wb,
                founded_date=fd,
                description=dc,
                number_of_employees=ne,
                logo=lo,
            )
            cp.save()
        except ValidationError as e:
            return render(request, 'company/createcompanyprofile.html', {'error': e.messages})

        return render(request, 'company/company_profile.html', context)
    else:
        return render(request, 'company/createcompanyprofile.html')

#EDIT COMPANY PROFILE
def edit_company_profile(request):
    company_profile = get_object_or_404(CompanyProfile, user=request.user)
    if request.method == 'POST':
        company_profile.user.first_name = request.POST.get('fname', '')
        company_profile.user.last_name = request.POST.get('lname', '')
        company_profile.company_name = request.POST.get('company_name', '')
        company_profile.phone = request.POST.get('phone', '')
        company_profile.address = request.POST.get('address', '')
        company_profile.website = request.POST.get('website', '')
        company_profile.founded_date = request.POST.get('founded_date', '')
        company_profile.description = request.POST.get('description', '')
        company_profile.number_of_employees = request.POST.get('number_of_employees', '')
        if 'profile_pic' in request.FILES:
            company_profile.logo = request.FILES['profile_pic']
        company_profile.save()
        company_profile.user.save() 

        return render(request,'/company_profile')  
    return render(request, 'company/company_profile.html', {'company_profile': company_profile})

#POST NEW JOB
def post_job(request):
    try:
        company_profile = CompanyProfile.objects.get(user=request.user)
    except:
        if CompanyProfile.DoesNotExist:
            return redirect('create_company_profile')
    if request.method == 'GET':
        return render(request, 'company/post_job.html')
    elif request.method == 'POST':
        company_id = request.user.id  
        try:
            comp_profile = CompanyProfile.objects.get(user=company_id)
        except CompanyProfile.DoesNotExist:
            return HttpResponse('Company profile not found', status=404)
         
        jobtitle = request.POST.get('jobtitle')
        salrange = request.POST.get('salrange')
        cat = request.POST.get('cat')
        jdetails = request.POST.get('jdetails')
        is_active = request.POST.get('is_active') == 'on'
        location = request.POST.get('location')
        application_deadline = request.POST.get('application_deadline')
        contact_email = request.POST.get('contact_email')
        contact_phone = request.POST.get('contact_phone')
        job_type = request.POST.get('job_type')
        experience_required = request.POST.get('experience_required')
        job_summary = request.POST.get('job_summary')
        required_skills = request.POST.get('required_skills')

        Jobs.objects.create(
            company=comp_profile,
            jobtitle=jobtitle,
            salrange=salrange,
            cat=cat,
            jdetails=jdetails,
            is_active=is_active,
            location=location,
            application_deadline=application_deadline,
            contact_email=contact_email,
            contact_phone=contact_phone,
            job_type=job_type,
            experience_required=experience_required,
            job_summary=job_summary,
            required_skills=required_skills,
        )

        return redirect('company_view')
    return render(request, 'company/post_job.html')


#EDIT EXISTING JOB
def edit_job(request, jid):
    job = get_object_or_404(Jobs, id=jid)

    if request.method == 'GET':
        context = {'data': job}
        return render(request, 'company/editjob.html', context)

    if request.method == 'POST':
        job.jobtitle = request.POST.get('jobtitle')
        job.salrange = request.POST.get('salrange')
        job.cat = request.POST.get('cat')
        job.jdetails = request.POST.get('jdetails')
        job.is_active = request.POST.get('is_active') == 'on'
        job.location = request.POST.get('location')
        job.application_deadline = request.POST.get('application_deadline')
        job.contact_email = request.POST.get('contact_email')
        job.contact_phone = request.POST.get('contact_phone')
        job.job_type = request.POST.get('job_type')
        job.experience_required = request.POST.get('experience_required')
        job.job_summary = request.POST.get('job_summary')
        job.required_skills = request.POST.get('required_skills')
        job.save()
        
        return redirect('/company_view')

    return render(request, 'company/editjob.html', {'data': job})

#DELETE
def delete_job(request, jid):
    job = get_object_or_404(Jobs, id=jid)
    job.delete()
    return redirect('/company_view')

        
def application_form(request, jid, cid):       
    job = Jobs.objects.get(id=jid)
    company = CompanyProfile.objects.get(id=cid)

    if request.user.is_authenticated:

        if request.method == "GET":
            context = {
                'job': job,
                'company': company
            }
            return render(request, 'applicationform.html', context)

        elif request.method == "POST":
            applicant_name = request.POST['applicant_name']
            applicant_email = request.POST['applicant_email']
            cover_letter = request.POST['cover_letter']
            resume = request.FILES.get('resume')
            applicant, created = User.objects.get_or_create(username=applicant_email, defaults={'email': applicant_email})
            job_application = UserJobApplication(
                comp=company,
                applicant=applicant,
                job=job,
                cover_letter=cover_letter,
                resume=resume
            )
            job_application.save()
            return redirect('/applicationsubmit')  

        context = {
            'job': job,
            'company': company
        }
        return render(request, 'applicationform.html', context)
    else:
        return redirect('login_view')



def applicationsubmit(request):
    sub='Application Status'
    msg='Application Submited Sucessfully ...!!'
    frm='kurheavinash2019@gmail.com'
    u=User.objects.filter(id=request.user.id)
    to=u[0].email
    send_mail(
        sub,
        msg,
        frm,
        [to],
        fail_silently='False'
    )
    return render(request,'applicationsubmit.html')



def appliedjobuserview(request):
    if request.method == "GET":
        context = {}
        aj = UserJobApplication.objects.filter(applicant_id=request.user)
        context['data'] = aj
        return render(request, 'applied_jobs.html', context)
    
def delete_application(request, aid):
    application = get_object_or_404(UserJobApplication, id=aid)
    if request.method == "POST":
        application.delete()
        return redirect('/appliedjobuserview')
    
def update_application(request, aid, jid):
    application = UserJobApplication.objects.filter(id=aid)
    job_applications = UserJobApplication.objects.filter(job_id=jid)
    if request.method == "GET":
        return render(request, 'update_application.html', {'data': application})
    elif request.method == "POST":
        cover_letter = request.POST['cover_letter']
        resume = request.FILES.get('resume')
        for job_application in job_applications:
            job_application.cover_letter = cover_letter
            job_application.resume = resume
            job_application.save()
        return redirect('/appliedjobuserview')



def see_application_for_company(request):
    comp = CompanyProfile.objects.get(user=request.user.id)
    rci=comp.id
    applications=UserJobApplication.objects.filter(comp_id=rci)
    print(applications)
    return render(request,'company/see_applications.html',{'data':applications})

def update_application_status(request, jid):
    applications = UserJobApplication.objects.filter(id=jid)
    context = {}
    context['data'] = applications
    
    if request.method == "GET":
        return render(request, 'company/update_application_status.html', context)
    elif request.method == "POST":
        status = request.POST.get('status', '')
        for application in applications:
            application.status = status
            application.save() 
    
            sub='Application Status Was Changed'
            msg = f'Your application status was changed to {application.status}. Please visit the site to view the status.'
            frm='kurheavinash2019@gmail.com'
            u=User.objects.filter(id=request.user.id)
            to=u[0].email
            send_mail(
                sub,
                msg,
                frm,
                [to],
                fail_silently='False'
            )
            return redirect('see_application_for_company')

       
def delete_application_for_company(request,jid):
        applications = UserJobApplication.objects.filter(id=jid)
        applications.delete()
        return redirect('see_application_for_company')

def premium_form_view(request):
    premium_user = Premiums.objects.filter(user=request.user).first()
    
    return render(request, 'company/premium.html', {'premium_user': premium_user})

def paymentsuccess(request):
    if not request.user.is_authenticated:
        return redirect('login')

    sub = 'Premium Subscription Activated'
    msg = 'Your payment was successful, and your Premium subscription is now active.'
    frm = 'kurheavinash2019@gmail.com'
    u = request.user
    to = u.email

    send_mail(
        sub,
        msg,
        frm,
        [to],
        fail_silently=False
    )

    premium_user, created = Premiums.objects.get_or_create(user=request.user)
    if created:
        premium_user.premium_end_date = timezone.now() + timedelta(days=30)  # 30 days premium subscription
        premium_user.is_active = True
        premium_user.save()
    return render(request, 'company/paymentsuccess.html', {'premium_user': premium_user})