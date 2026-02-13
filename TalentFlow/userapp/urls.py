from django.urls import path
from userapp import views

urlpatterns = [
    path('', views.index, name='index'), 
    path('student/login/', views.student_login, name='student_login'),
    path('recruiter/login/', views.recruiter_login, name='recruiter_login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path("logout/", views.user_logout, name="logout"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/applications/", views.student_applications, name="student_applications"),
    path("upload-resume/", views.upload_resume, name="upload_resume"),
    path("post-job/", views.post_job, name="post_job"),
    path("apply-job/<int:job_id>/", views.apply_job, name="apply_job"),
    path("edit-company/", views.edit_company_details, name="edit_company"),
    path("ai-chat/", views.ai_chat, name="ai_chat"),
    path('jobs/', views.view_jobs, name='view_jobs'),
    path('recruiter/dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('recruiter/post-job/', views.post_job, name='post_job'),
    path('recruiter/applications/',views.recruiter_applications,name='recruiter_applications'),
]