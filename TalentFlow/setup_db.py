#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TalentFlow.settings')
django.setup()

from django.contrib.auth.models import User
from userapp.models import Profile
from django.contrib.auth import authenticate

# Delete old test users
User.objects.filter(username__in=['student123', 'recruiter123']).delete()
print('Cleared old users')

# Create student user
student_user = User.objects.create_user(
    username='student123',
    email='student@example.com',
    password='password123'
)
student_profile = Profile.objects.create(
    user=student_user,
    user_type='student',
    bio='I am a student'
)
print('✓ Created student user: student123 / password123')

# Create recruiter user
recruiter_user = User.objects.create_user(
    username='recruiter123',
    email='recruiter@example.com', 
    password='password123'
)
recruiter_profile = Profile.objects.create(
    user=recruiter_user,
    user_type='recruiter',
    bio='I am a recruiter'
)
print('✓ Created recruiter user: recruiter123 / password123')

# Test authentication
test_student = authenticate(username='student123', password='password123')
test_recruiter = authenticate(username='recruiter123', password='password123')

print(f'\nAuthentication test:')
print(f'  student123: {"✓ OK" if test_student else "✗ FAILED"}')
print(f'  recruiter123: {"✓ OK" if test_recruiter else "✗ FAILED"}')

print('\n✓ Database setup complete!')
