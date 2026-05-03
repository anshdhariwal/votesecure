from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('signup/', views.signup_step1, name='signup_step1'),
    path('signup/password/', views.signup_step2, name='signup_step2'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('change-password/', views.change_password, name='change_password'),
    path('home/', views.voter_home, name='voter_home'),
    path('vote/', views.vote_page, name='vote'),
    path('vote/candidate/<int:candidate_id>/', views.candidate_detail, name='candidate_detail'),
    path('candidates/', views.voter_candidates, name='voter_candidates'),
    path('results/', views.results_page, name='results'),
]
