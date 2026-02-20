import json
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    USER_TYPES = [
        ('student', 'Student'),
        ('recruiter', 'Recruiter'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    headline = models.CharField(max_length=255, blank=True)
    skills = models.TextField(default='[]')  # JSON string
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    cgpa = models.FloatField(default=0)
    experience = models.FloatField(default=0)
    certifications = models.TextField(default='[]')  # JSON string
    other_links = models.TextField(default='{}')  # JSON string storing dict of links
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)

    def get_skills(self):
        return json.loads(self.skills)

    def set_skills(self, skills_list):
        self.skills = json.dumps(skills_list)

    def get_certifications(self):
        return json.loads(self.certifications)

    def set_certifications(self, cert_list):
        self.certifications = json.dumps(cert_list)

    def get_links(self):
        try:
            return json.loads(self.other_links)
        except Exception:
            return {}

    def set_links(self, links_dict):
        self.other_links = json.dumps(links_dict)

    def __str__(self):
        return f"{self.user.username} Profile"


class Job(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.TextField(default='[]')  # JSON string
    min_cgpa = models.FloatField(default=0)
    min_experience = models.FloatField(default=0)
    required_certifications = models.TextField(default='[]')  # JSON string
    application_link = models.URLField(blank=True, default='')

    def get_required_skills(self):
        return json.loads(self.required_skills)

    def get_required_certifications(self):
        return json.loads(self.required_certifications)


class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    resume = models.FileField(upload_to='application_resumes/', blank=True, null=True)
    status = models.CharField(max_length=20, default='applied')  # 'applied' or 'withdrawn'
    withdrawn_at = models.DateTimeField(blank=True, null=True)
