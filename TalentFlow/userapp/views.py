from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Job, Application
from .forms import CustomUserCreationForm, ProfileForm,RegisterProfileForm
from .utils import calculate_ats_score



# ==========================
# HOME
# ==========================
def index(request):
    return render(request, "index.html")


# ==========================
# REGISTER
# ==========================
def register(request):
    if request.method == "POST":
        user_form = CustomUserCreationForm(request.POST)
        profile_form = RegisterProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():

            # Save user
            user = user_form.save()
            user.email = user_form.cleaned_data['email']
            user.save()

            # Save profile
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            login(request, user)

            # 🔥 Redirect based on role
            if profile.user_type == "recruiter":
                return redirect("recruiter_dashboard")
            else:
                return redirect("student_dashboard")

        else:
            print("USER FORM ERRORS:", user_form.errors)
            print("PROFILE FORM ERRORS:", profile_form.errors)

    else:
        user_form = CustomUserCreationForm()
        profile_form = RegisterProfileForm()

    return render(request, 'register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


# ---------------- STUDENT LOGIN ----------------

def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'student_login.html')


# ---------------- RECRUITER LOGIN ----------------
def recruiter_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                messages.error(request, "Profile not found for this user.")
                return redirect('recruiter_login')

            if profile.user_type != 'recruiter':
                messages.error(request, "You are not registered as a recruiter.")
                return redirect('recruiter_login')

            login(request, user)
            return redirect('recruiter_dashboard')

        messages.error(request, "Invalid username or password")
        return redirect('recruiter_login')

    return render(request, 'recruiter_login.html')

# ==========================
# LOGOUT
# ==========================

def user_logout(request):
    logout(request)
    return redirect('index')


@login_required
def dashboard(request):
    profile = request.user.profile
    jobs = Job.objects.all()

    jobs_with_score = []
    for job in jobs:
        score = calculate_ats_score(profile, job)
        recommendation = "Apply" if score >= 70 else "Improve Resume"
        jobs_with_score.append({'job': job, 'score': score, 'recommendation': recommendation})

    return render(request, 'userapp/dashboard.html', {
        'profile': profile,
        'jobs_with_score': jobs_with_score
    })
# ==========================
# STUDENT DASHBOARD
# ==========================
@login_required
def student_dashboard(request):
    jobs = Job.objects.all()
    return render(request, "student_dashboard.html", {"jobs": jobs})
# ==========================
#jats calculation
# ==========================

def job_list(request):
    profile = request.user.profile
    jobs = Job.objects.all()
    jobs_with_score = []

    for job in jobs:
        ats_score = calculate_ats_score(profile, job)
        apply_recommendation = "Apply" if ats_score >= 70 else "Consider Improving Resume"
        jobs_with_score.append({
            'job': job,
            'score': ats_score,
            'recommendation': apply_recommendation
        })

    return render(request, 'jobs/job_list.html', {'jobs_with_score': jobs_with_score})

# ==========================
# UPLOAD RESUME (STUDENT)
# ==========================
@login_required
def upload_resume(request):
    if request.method == "POST":
        skills = request.POST.get("skills")
        resume = request.FILES.get("resume")

        profile = request.user.profile
        profile.skills = skills
        profile.resume = resume
        profile.save()

        messages.success(request, "Resume uploaded successfully")

    return render(request, "upload_resume.html")


# ==========================
# VIEW JOBS (STUDENT)
# ==========================
@login_required
def view_jobs(request):
    jobs = Job.objects.all()
    return render(request, "view_jobs.html", {"jobs": jobs})


# ==========================
# APPLY JOB (STUDENT)
# ==========================
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    Application.objects.get_or_create(
        job=job,
        user=request.user
    )

    messages.success(request, "Applied successfully")
    return redirect("student_dashboard")

@login_required
def student_applications(request):
    applications = Application.objects.filter(user=request.user)
    return render(request, 'student_applications.html', {
        'applications': applications
    })

# ===============================
# RECRUITER DASHBOARD
# ===============================
@login_required
def recruiter_dashboard(request):
    total_jobs = Job.objects.filter(recruiter=request.user).count()
    total_applications = Application.objects.filter(
        job__recruiter=request.user
    ).count()

    return render(request, 'recruiter_dashboard.html', {
        'total_jobs': total_jobs,
        'total_applications': total_applications
    })


# ===============================
# POST JOB
# ===============================
@login_required
def post_job(request):
    if request.method == 'POST':
        title = request.POST['title']
        skills = request.POST['skills']
        description = request.POST['description']

        Job.objects.create(
            recruiter=request.user,
            title=title,
            required_skills=skills,
            description=description
        )
        messages.success(request, "Job posted successfully")
        return redirect('recruiter_jobs')

    return render(request, 'post_job.html')


# ===============================
# RECRUITER JOB LIST
# ===============================
@login_required
def recruiter_jobs(request):
    jobs = Job.objects.filter(recruiter=request.user)
    return render(request, 'recruiter_jobs.html', {'jobs': jobs})



# ==========================
# VIEW APPLICATIONS (RECRUITER)
# ==========================
@login_required
def recruiter_applications(request):
    applications = Application.objects.filter(
        job__recruiter=request.user
    ).select_related('job', 'user')

    return render(
        request,
        'recruiter_applications.html',
        {'applications': applications}
    )


# ==========================
# EDIT COMPANY DETAILS
# ==========================
@login_required
def edit_company_details(request):
    profile = request.user.profile

    if request.method == "POST":
        profile.company_name = request.POST.get("company_name")
        profile.company_description = request.POST.get("company_description")
        profile.save()

        messages.success(request, "Company details updated")

    return render(request, "edit_company_details.html", {"profile": profile})


# ==========================
# AI CHAT
# ==========================
@login_required
def ai_chat(request):
    return render(request, "ai_chat.html")

@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        profile.user_type = request.POST.get('user_type', profile.user_type)
        profile.bio = request.POST.get('bio', profile.bio)
        profile.headline = request.POST.get('headline', profile.headline)
        profile.location = request.POST.get('location', profile.location)
        profile.website = request.POST.get('website', profile.website)

        try:
            profile.cgpa = float(request.POST.get('cgpa', profile.cgpa))
        except (ValueError, TypeError):
            profile.cgpa = profile.cgpa

        try:
            profile.experience = float(request.POST.get('experience', profile.experience))
        except (ValueError, TypeError):
            profile.experience = profile.experience

        # Convert comma-separated skills & certifications to JSON
        skills_raw = request.POST.get('skills', '')
        profile.set_skills([s.strip() for s in skills_raw.split(',') if s.strip()])

        cert_raw = request.POST.get('certifications', '')
        profile.set_certifications([c.strip() for c in cert_raw.split(',') if c.strip()])

        # Profile picture
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('dashboard')

    # prefill form
    context = {
        'profile': profile,
        'skills_str': ', '.join(profile.get_skills()),
        'certs_str': ', '.join(profile.get_certifications())
    }
    return render(request, 'edit_profile.html', context)