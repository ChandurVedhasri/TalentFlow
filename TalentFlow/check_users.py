import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TalentFlow.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from userapp.models import Profile

# Check existing users
print("=" * 50)
print("CHECKING DATABASE USERS")
print("=" * 50)

users = User.objects.all()
print(f'\nTotal users in database: {users.count()}')
for user in users:
    try:
        profile = user.profile
        print(f'  - Username: {user.username}, Type: {profile.user_type}')
    except Profile.DoesNotExist:
        print(f'  - Username: {user.username}, Type: NO PROFILE')

# Test authentication
print("\n" + "=" * 50)
print("TESTING AUTHENTICATION")
print("=" * 50)

test_user = authenticate(username='student123', password='password123')
print(f'\nstudent123/password123: {"✓ SUCCESS" if test_user else "✗ FAILED"}')

test_user2 = authenticate(username='recruiter123', password='password123')
print(f'recruiter123/password123: {"✓ SUCCESS" if test_user2 else "✗ FAILED"}')

# Create test users if they don't exist
print("\n" + "=" * 50)
print("CREATING TEST USERS (if not exist)")
print("=" * 50)

try:
    student_user = User.objects.get(username='student123')
    print('\n✓ Student user already exists')
except User.DoesNotExist:
    student_user = User.objects.create_user(username='student123', password='password123', email='student@example.com')
    student_profile = Profile.objects.create(user=student_user, user_type='student', bio='I am a student')
    print('\n✓ Created student user')

try:
    recruiter_user = User.objects.get(username='recruiter123')
    print('✓ Recruiter user already exists')
except User.DoesNotExist:
    recruiter_user = User.objects.create_user(username='recruiter123', password='password123', email='recruiter@example.com')
    recruiter_profile = Profile.objects.create(user=recruiter_user, user_type='recruiter', bio='I am a recruiter')
    print('✓ Created recruiter user')

# Final test
print("\n" + "=" * 50)
print("FINAL AUTHENTICATION TEST")
print("=" * 50)

test_user = authenticate(username='student123', password='password123')
print(f'\nstudent123/password123: {"✓ SUCCESS" if test_user else "✗ FAILED"}')

test_user2 = authenticate(username='recruiter123', password='password123')
print(f'recruiter123/password123: {"✓ SUCCESS" if test_user2 else "✗ FAILED"}')

print("\n" + "=" * 50)
print("Ready to login!")
print("=" * 50)
