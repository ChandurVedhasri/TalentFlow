import os


def _extract_resume_text(resume_path):
    text = ""
    if not resume_path or not os.path.exists(resume_path):
        return text

    _, ext = os.path.splitext(resume_path)
    ext = ext.lower()

    # PDF
    if ext == '.pdf':
        try:
            import PyPDF2
            with open(resume_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + ' '
        except Exception:
            # PyPDF2 not available or extraction failed; fall through to OCR attempt
            pass

        # If no text extracted by PyPDF2, attempt OCR on the PDF (useful for scanned PDFs)
        if not text:
            try:
                from pdf2image import convert_from_path
                import pytesseract
                # convert to images (requires poppler on PATH)
                images = convert_from_path(resume_path)
                for img in images:
                    try:
                        page_text = pytesseract.image_to_string(img)
                        if page_text:
                            text += page_text + ' '
                    except Exception:
                        continue
            except Exception:
                # OCR libraries not available or failed; return whatever (possibly empty)
                pass

    # DOCX
    elif ext in ('.docx', '.doc'):
        try:
            import docx
            doc = docx.Document(resume_path)
            for p in doc.paragraphs:
                text += p.text + ' '
        except Exception:
            return text

    # Plain text or other
    else:
        try:
            with open(resume_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception:
            return text

    return text


def _is_resume_like(text):
    """Very small heuristic to decide if extracted text looks like a resume.

    Returns True when text is long enough and contains multiple resume-related keywords.
    """
    if not text:
        return False
    t = text.lower()
    # reject very short files
    if len(t) < 150:
        return False

    # count reasonably long lines to ensure document structure
    lines = [l for l in text.splitlines() if len(l.strip()) > 20]
    line_count = len(lines)

    keywords = [
        'experience', 'education', 'skills', 'projects', 'contact',
        'linkedin', 'resume', 'curriculum vitae', 'objective', 'summary',
        'bachelor', 'master', 'degree'
    ]
    found = sum(1 for kw in keywords if kw in t)

    # stronger heuristic: prefer longer files with multiple meaningful lines
    if (len(t) >= 400 and found >= 2 and line_count >= 4) or (found >= 4 and len(t) >= 200):
        return True
    return False


def calculate_ats_score(profile, job, resume_file=None):
    """Calculate ATS score by matching job skills against resume text.

    Falls back to `profile.get_skills()` when no resume text is available.
    Keeps existing CGPA/experience/certification components.
    """
    profile_skills = profile.get_skills()
    profile_certs = profile.get_certifications()

    job_skills = job.get_required_skills()
    job_certs = job.get_required_certifications()

    # Try to extract resume text if present on profile
    resume_text = ""
    try:
        # If a resume_file (Application.resume or uploaded file) is provided, prefer it
        resume_path = None
        if resume_file:
            resume_path = getattr(resume_file, 'path', None)
        # otherwise fall back to profile.resume
        if not resume_path and hasattr(profile, 'resume') and profile.resume:
            resume_path = getattr(profile.resume, 'path', None)

        if resume_path:
            resume_text = _extract_resume_text(resume_path)
            # Only treat file as resume if heuristic passes
            if not _is_resume_like(resume_text):
                resume_text = ""
    except Exception:
        resume_text = ""

    score = 0

    # Skills match (40%) - prefer resume-based matching
    skill_score = 0
    if job_skills:
        if resume_text and resume_text.strip():
            # Match on word boundaries to avoid substring false positives
            import re
            resume_lower = resume_text.lower()
            matched_skills = 0
            for s in job_skills:
                if not s or len(s.strip()) <= 2:
                    continue
                pattern = r"\b" + re.escape(s.strip().lower()) + r"\b"
                if re.search(pattern, resume_lower):
                    matched_skills += 1

            # If resume looked like resume but no skills matched, fallback to profile skills
            if matched_skills == 0:
                matched_skills = len(set(profile_skills) & set(job_skills))

            skill_score = (matched_skills / len(job_skills)) * 40
        else:
            matched_skills = len(set(profile_skills) & set(job_skills))
            skill_score = (matched_skills / len(job_skills)) * 40
    score += skill_score

    # CGPA match (30%)
    edu_score = min((profile.cgpa / job.min_cgpa) * 30, 30) if getattr(job, 'min_cgpa', None) else 0
    score += edu_score

    # Experience match (20%)
    exp_score = min((profile.experience / job.min_experience) * 20, 20) if getattr(job, 'min_experience', None) else 0
    score += exp_score

    # Certifications match (10%)
    cert_score = 0
    if job_certs:
        matched_cert = len(set(profile_certs) & set(job_certs))
        cert_score = (matched_cert / len(job_certs)) * 10
    score += cert_score

    # Debug logging to help diagnose scoring issues
    try:
        debug_path = os.path.join(os.getcwd(), 'ats_debug.log')
        user_ident = 'anonymous'
        try:
            if profile and hasattr(profile, 'user') and profile.user:
                user_ident = getattr(profile.user, 'username', str(getattr(profile.user, 'id', 'user')))
        except Exception:
            user_ident = 'anonymous'

        job_ident = getattr(job, 'id', None)
        job_title = getattr(job, 'title', '')

        resume_info = {
            'resume_path': resume_path if 'resume_path' in locals() else None,
            'resume_text_len': len(resume_text) if resume_text else 0,
            'is_resume_like': _is_resume_like(resume_text) if resume_text else False,
        }

        # try to record matched skills counts
        try:
            import re as _re
            resume_lower = resume_text.lower() if resume_text else ''
            matched_resume = 0
            for s in job_skills or []:
                if not s or len(s.strip()) <= 2:
                    continue
                pattern = r"\b" + _re.escape(s.strip().lower()) + r"\b"
                if resume_text and _re.search(pattern, resume_lower):
                    matched_resume += 1
            matched_profile = len(set(profile_skills) & set(job_skills)) if profile_skills and job_skills else 0
        except Exception:
            matched_resume = 0
            matched_profile = len(set(profile_skills) & set(job_skills)) if profile_skills and job_skills else 0

        with open(debug_path, 'a', encoding='utf-8') as df:
            from datetime import datetime as _dt
            df.write(f"[{_dt.utcnow().isoformat()}] user={user_ident} job_id={job_ident} title={job_title}\n")
            df.write(f"  resume_path={resume_info['resume_path']} resume_len={resume_info['resume_text_len']} is_resume_like={resume_info['is_resume_like']}\n")
            df.write(f"  matched_resume={matched_resume} matched_profile={matched_profile} job_skills_count={len(job_skills) if job_skills else 0}\n")
            df.write(f"  skill_score={skill_score:.2f} edu_score={edu_score:.2f} exp_score={exp_score:.2f} cert_score={cert_score:.2f} total_score={round(score,2):.2f}\n\n")
    except Exception:
        pass

    return round(score, 2)


def get_skill_match(profile, job, resume_file=None):
    """Return matched and missing skills between a resume/profile and a job.

    Returns dict: {matched: [...], missing: [...], used_resume: bool, resume_snippet: str}
    """
    profile_skills = profile.get_skills() if profile else []
    job_skills = job.get_required_skills() or []

    # Determine resume text (prefer provided resume_file)
    resume_text = ""
    used_resume = False
    try:
        resume_path = None
        if resume_file:
            resume_path = getattr(resume_file, 'path', None)
        if not resume_path and profile and hasattr(profile, 'resume') and profile.resume:
            resume_path = getattr(profile.resume, 'path', None)

        if resume_path:
            resume_text = _extract_resume_text(resume_path)
            if _is_resume_like(resume_text):
                used_resume = True
            else:
                resume_text = ""
    except Exception:
        resume_text = ""

    matched = []
    missing = []

    import re
    resume_lower = resume_text.lower() if resume_text else ''

    for s in job_skills:
        if not s or len(s.strip()) <= 1:
            continue
        token = s.strip()
        pattern = r"\b" + re.escape(token.lower()) + r"\b"
        matched_here = False
        if used_resume and resume_text:
            if re.search(pattern, resume_lower):
                matched_here = True
        else:
            # fallback to profile skills
            if token in profile_skills or token.lower() in [p.lower() for p in profile_skills]:
                matched_here = True

        if matched_here:
            matched.append(token)
        else:
            missing.append(token)

    snippet = (resume_text[:800] + '...') if resume_text else ''
    return {
        'matched': matched,
        'missing': missing,
        'used_resume': used_resume,
        'resume_snippet': snippet
    }
