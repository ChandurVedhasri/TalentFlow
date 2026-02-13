def calculate_ats_score(profile, job):
    profile_skills = profile.get_skills()
    profile_certs = profile.get_certifications()

    job_skills = job.get_required_skills()
    job_certs = job.get_required_certifications()

    score = 0

    # Skills match (40%)
    if job_skills:
        matched_skills = len(set(profile_skills) & set(job_skills))
        skill_score = (matched_skills / len(job_skills)) * 40
    else:
        skill_score = 0
    score += skill_score

    # CGPA match (30%)
    edu_score = min((profile.cgpa / job.min_cgpa) * 30, 30) if job.min_cgpa else 0
    score += edu_score

    # Experience match (20%)
    exp_score = min((profile.experience / job.min_experience) * 20, 20) if job.min_experience else 0
    score += exp_score

    # Certifications match (10%)
    if job_certs:
        matched_cert = len(set(profile_certs) & set(job_certs))
        cert_score = (matched_cert / len(job_certs)) * 10
    else:
        cert_score = 0
    score += cert_score

    return round(score, 2)
