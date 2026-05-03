from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('elections/', views.admin_elections, name='admin_elections'),
    path('candidates/', views.admin_candidates, name='admin_candidates'),
    path('voters/', views.admin_voters, name='admin_voters'),
    path('results/', views.admin_results, name='admin_results'),
    path('export/pdf/<int:election_id>/', views.generate_pdf_report, name='pdf_report'),
    path('export/voters/csv/', views.export_voters_csv, name='export_csv'),
    path('wipe-database/', views.wipe_database, name='wipe_database'),
    path('profile/edit/', views.admin_edit_profile, name='admin_edit_profile'),
]
