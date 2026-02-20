from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Profile, Job, Application
from django.contrib.admin.views.decorators import staff_member_required
import json
from .forms import CustomUserCreationForm, ProfileForm,RegisterProfileForm
from .utils import calculate_ats_score, get_skill_match
from django.views.decorators.http import require_POST



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

        if user_form.is_valid():
            user = user_form.save()

            if profile_form.is_valid():
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()

                login(request, user)

                if profile.user_type == "recruiter":
                    return redirect("recruiter_dashboard")
                else:
                    return redirect("student_dashboard")
            else:
                user.delete()  # rollback if profile fails
                messages.error(request, profile_form.errors)

        else:
            messages.error(request, user_form.errors)

    else:
        user_form = CustomUserCreationForm()
        profile_form = RegisterProfileForm()

    return render(request, "register.html", {
        "user_form": user_form,
        "profile_form": profile_form
    })
# ---------------- STUDENT LOGIN ----------------

def student_login(request):
    if request.method == "POST":
        identifier = request.POST.get("username")  # can be email or username
        password = request.POST.get("password")

        # Try to resolve identifier as email first, otherwise treat as username
        try:
            user_obj = User.objects.get(email=identifier)
            username = user_obj.username
        except User.DoesNotExist:
            username = identifier

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("student_dashboard")
        else:
            messages.error(request, "Invalid credentials")

    return render(request, "student_login.html")

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

    return render(request, 'dashboard.html', {
        'profile': profile,
        'jobs_with_score': jobs_with_score
    })
# ==========================
# STUDENT DASHBOARD
# ==========================
@login_required
def student_dashboard(request):
    profile = request.user.profile
    jobs = Job.objects.all()

    jobs_with_score = []
    for job in jobs:
        # if the student already applied with a resume, prefer that resume for scoring
        app = Application.objects.filter(user=request.user, job=job, status='applied').first()
        ats_score = calculate_ats_score(profile, job, resume_file=(app.resume if app else None))
        breakdown = get_skill_match(profile, job, resume_file=(app.resume if app else None))
        recommendation = "Apply" if ats_score >= 70 else "Consider Improving Resume"
        already_applied = Application.objects.filter(user=request.user, job=job, status='applied').exists()
        jobs_with_score.append({
            'job': job,
            'score': ats_score,
            'recommendation': recommendation,
            'already_applied': already_applied,
            'matched_skills': breakdown['matched'],
            'missing_skills': breakdown['missing'],
            'used_resume': breakdown['used_resume']
        })

    return render(request, "student_dashboard.html", {"jobs_with_score": jobs_with_score, "profile": profile})
# ==========================
#jats calculation
# ==========================

def job_list(request):
    profile = request.user.profile
    jobs = Job.objects.all()
    jobs_with_score = []

    for job in jobs:
        app = Application.objects.filter(user=request.user, job=job, status='applied').first()
        ats_score = calculate_ats_score(profile, job, resume_file=(app.resume if app else None))
        breakdown = get_skill_match(profile, job, resume_file=(app.resume if app else None))
        apply_recommendation = "Apply" if ats_score >= 70 else "Consider Improving Resume"
        already_applied = Application.objects.filter(user=request.user, job=job, status='applied').exists()
        jobs_with_score.append({
            'job': job,
            'score': ats_score,
            'recommendation': apply_recommendation,
            'already_applied': already_applied,
            'matched_skills': breakdown['matched'],
            'missing_skills': breakdown['missing'],
            'used_resume': breakdown['used_resume']
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
    profile = request.user.profile
    jobs = Job.objects.all()

    jobs_with_score = []
    for job in jobs:
        app = Application.objects.filter(user=request.user, job=job, status='applied').first()
        ats_score = calculate_ats_score(profile, job, resume_file=(app.resume if app else None))
        breakdown = get_skill_match(profile, job, resume_file=(app.resume if app else None))
        recommendation = "Apply" if ats_score >= 70 else "Consider Improving Resume"
        jobs_with_score.append({
            'job': job,
            'score': ats_score,
            'recommendation': recommendation,
            'matched_skills': breakdown['matched'],
            'missing_skills': breakdown['missing'],
            'used_resume': breakdown['used_resume']
        })

    return render(request, "view_jobs.html", {"jobs_with_score": jobs_with_score})


@login_required
def view_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # profile may not exist for non-students; guard access
    try:
        profile = request.user.profile
    except Exception:
        profile = None

    # consider only applications with status 'applied' as active applications
    already_applied = Application.objects.filter(user=request.user, job=job, status='applied').exists()

    # if user has applied earlier, prefer application resume for scoring
    app = None
    try:
        app = Application.objects.filter(user=request.user, job=job, status='applied').first()
    except Exception:
        app = None

    score = calculate_ats_score(profile, job, resume_file=(app.resume if app else None)) if profile else 0
    breakdown = get_skill_match(profile, job, resume_file=(app.resume if app else None)) if profile else {'matched': [], 'missing': [], 'used_resume': False}
    recommendation = "Apply" if score >= 70 else "Consider Improving Resume"

    return render(request, 'view_jobs.html', {
        'job': job,
        'already_applied': already_applied,
        'score': score,
        'recommendation': recommendation,
        'matched_skills': breakdown['matched'],
        'missing_skills': breakdown['missing'],
        'used_resume': breakdown['used_resume']
    })


@login_required
def apply_external(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # create application record if not exists
    app, created = Application.objects.get_or_create(user=request.user, job=job)
    app.status = 'applied'
    app.withdrawn_at = None
    app.save()

    # redirect to external link if provided, otherwise back to job page
    if job.application_link:
        return redirect(job.application_link)
    return redirect('view_job', job_id=job.id)


# ==========================
# APPLY JOB (STUDENT)
# ==========================
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Ensure student has provided a resume either uploaded previously or in this form
    profile = request.user.profile
    uploaded_resume = request.FILES.get('resume')
    if not uploaded_resume and not getattr(profile, 'resume', None):
        messages.error(request, "Please upload a resume before applying.")
        return redirect('view_job', job_id=job.id)

    app, created = Application.objects.get_or_create(job=job, user=request.user)
    # if resume uploaded in this apply form, save it on the application; otherwise attach profile.resume
    if uploaded_resume:
        app.resume = uploaded_resume
        app.save()
    elif getattr(profile, 'resume', None):
        # copy profile resume reference to application (optional)
        app.resume = profile.resume
        app.save()

    # set application status to applied (in case it was withdrawn earlier)
    app.status = 'applied'
    app.withdrawn_at = None
    app.save()

    messages.success(request, "Applied successfully")
    return redirect("student_dashboard")

@login_required
def student_applications(request):
    profile = request.user.profile
    applications = Application.objects.filter(user=request.user).select_related('job')

    apps_with_score = []
    for app in applications:
        score = calculate_ats_score(profile, app.job, resume_file=(app.resume if getattr(app, 'resume', None) else None))
        breakdown = get_skill_match(profile, app.job, resume_file=(app.resume if getattr(app, 'resume', None) else None))
        recommendation = "Apply" if score >= 70 else "Improve Resume"
        apps_with_score.append({
            'application': app,
            'score': score,
            'recommendation': recommendation,
            'matched_skills': breakdown['matched'],
            'missing_skills': breakdown['missing'],
            'used_resume': breakdown['used_resume']
        })

    return render(request, 'student_applications.html', {
        'applications': apps_with_score
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
        title = request.POST.get('title', '').strip()
        # accept either 'skills' or 'required_skills' from the form to be more robust
        raw_skills = request.POST.get('skills') or request.POST.get('required_skills', '')
        description = request.POST.get('description', '').strip()

        # normalize comma-separated skills into a JSON string (list)
        skills_list = [s.strip() for s in raw_skills.split(',') if s.strip()]
        required_skills_json = json.dumps(skills_list)
        application_link = request.POST.get('application_link', '').strip()

        # avoid creating exact duplicate jobs for the same recruiter
        exists = Job.objects.filter(
            recruiter=request.user,
            title__iexact=title,
            description__iexact=description,
            required_skills=required_skills_json
        ).exists()
        if not exists:
            Job.objects.create(
                recruiter=request.user,
                title=title,
                required_skills=required_skills_json,
                description=description,
                application_link=application_link
            )
        else:
            messages.info(request, "An identical job already exists and was not created.")
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


@login_required
@require_POST
def remove_profile(request):
    """Clear the current user's profile data (do not delete the User object).

    This avoids breaking code that assumes a Profile object exists while
    providing a way for users to remove personal data.
    """
    profile = request.user.profile

    # reset basic fields
    profile.user_type = 'student'
    profile.bio = ''
    profile.headline = ''
    profile.location = ''
    profile.website = ''
    profile.cgpa = 0
    profile.experience = 0

    # clear JSON fields
    try:
        profile.set_skills([])
    except Exception:
        profile.skills = '[]'
    try:
        profile.set_certifications([])
    except Exception:
        profile.certifications = '[]'
    try:
        profile.set_links({})
    except Exception:
        profile.other_links = '{}'

    # remove uploaded files if present (don't raise if missing)
    try:
        if profile.profile_picture:
            profile.profile_picture.delete(save=False)
    except Exception:
        pass
    try:
        if profile.resume:
            profile.resume.delete(save=False)
    except Exception:
        pass

    profile.save()
    messages.success(request, "Profile data cleared.")
    return redirect('student_dashboard')



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


@login_required
def withdraw_application(request, application_id):
    app = get_object_or_404(Application, id=application_id, user=request.user)
    if request.method == 'POST':
        app.status = 'withdrawn'
        app.withdrawn_at = timezone.now()
        app.save()
        messages.success(request, 'Application withdrawn.')
    return redirect('student_applications')


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

        # Social / external links
        linkedin = request.POST.get('linkedin', '').strip()
        github = request.POST.get('github', '').strip()
        portfolio = request.POST.get('portfolio', '').strip()
        other_raw = request.POST.get('other_links', '').strip()

        links = {}
        if linkedin:
            links['linkedin'] = linkedin
        if github:
            links['github'] = github
        if portfolio:
            links['portfolio'] = portfolio
        # other_links can be comma-separated "label:url" pairs
        if other_raw:
            extras = []
            for part in other_raw.split(','):
                p = part.strip()
                if ':' in p:
                    label, url = p.split(':', 1)
                    extras.append({'label': label.strip(), 'url': url.strip()})
                else:
                    extras.append({'label': p, 'url': p})
            links['other'] = extras
        profile.set_links(links)

        # Profile picture
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()
        messages.success(request, "Profile updated successfully!")
        # Redirect users to their appropriate dashboard based on role
        if getattr(profile, 'user_type', '') == 'recruiter':
            return redirect('recruiter_dashboard')
        return redirect('student_dashboard')

    # prefill form
    context = {
        'profile': profile,
        'skills_str': ', '.join(profile.get_skills()),
        'certs_str': ', '.join(profile.get_certifications())
    }
    return render(request, 'edit_profile.html', context)


# ==========================
# ATS Debug (admin-only)
# ==========================
@staff_member_required
def ats_debug(request):
    """Admin page that shows recent entries from ats_debug.log and allows filtering by username."""
    log_path = os.path.join(os.getcwd(), 'ats_debug.log')
    entries = []
    raw = ''
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                raw = f.read()
        except Exception:
            raw = ''

    if raw:
        # Split entries by double newline (as written by logger)
        blocks = [b.strip() for b in raw.split('\n\n') if b.strip()]
        # keep latest first
        blocks.reverse()
        user_filter = request.GET.get('user')
        for b in blocks[:200]:
            if user_filter:
                if f"user={user_filter}" in b:
                    entries.append(b)
            else:
                entries.append(b)

    return render(request, 'ats_debug.html', {'entries': entries, 'log_path': log_path})


@login_required
def resume_preview(request):
    """Show extracted resume text (snippet) for the current user profile and latest application resume."""
    profile = request.user.profile
    # prefer profile resume; if student has recent application resume, prefer that
    resume_file = None
    try:
        # check most recent application resume
        app = Application.objects.filter(user=request.user).order_by('-id').first()
        if app and getattr(app, 'resume', None):
            resume_file = app.resume
    except Exception:
        resume_file = None

    # fallback to profile resume
    if not resume_file and getattr(profile, 'resume', None):
        resume_file = profile.resume

    resume_text = ''
    used_resume = False
    if resume_file:
        try:
            resume_path = getattr(resume_file, 'path', None)
            if resume_path:
                resume_text = _extract_resume_text(resume_path)
                if _is_resume_like(resume_text):
                    used_resume = True
                else:
                    # if not resume-like, show empty and invite reupload
                    resume_text = ''
        except Exception:
            resume_text = ''

    # also show profile skills as fallback info
    profile_skills = profile.get_skills()

    return render(request, 'resume_preview.html', {
        'resume_text': resume_text,
        'used_resume': used_resume,
        'profile_skills': profile_skills,
        'resume_file': resume_file
    })