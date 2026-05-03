import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone

from core.decorators import staff_required
from core.models import Voter, Election, Position, Candidate, CandidateGoal, Vote, Party
from core.forms import ElectionForm, CandidateForm


@login_required
@staff_required
def admin_dashboard(request):
    """Admin dashboard with stats and activity feed."""
    today = timezone.now().date()
    total_voters = Voter.objects.filter(is_staff=False).count()
    total_votes = Vote.objects.count()
    votes_today = Vote.objects.filter(cast_at__date=today).count()

    active_elections = Election.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )
    active_elections_count = active_elections.count()

    upcoming_elections = Election.objects.filter(start_date__gt=timezone.now())
    upcoming_elections_count = upcoming_elections.count()

    completed_elections = Election.objects.filter(end_date__lt=timezone.now())
    completed_elections_count = completed_elections.count()

    all_elections = Election.objects.all().order_by('-created_at')
    recent_votes = Vote.objects.select_related(
        'voter', 'candidate', 'position', 'election'
    ).order_by('-cast_at')[:20]

    context = {
        'total_voters': total_voters,
        'total_votes': total_votes,
        'votes_today': votes_today,
        'active_elections_count': active_elections_count,
        'upcoming_elections_count': upcoming_elections_count,
        'completed_elections_count': completed_elections_count,
        'active_elections': active_elections,
        'all_elections': all_elections,
        'recent_votes': recent_votes,
    }
    return render(request, 'adminpanel/dashboard.html', context)


@login_required
@staff_required
def admin_edit_profile(request):
    """Update admin's own profile info."""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.admin_role = request.POST.get('admin_role', user.admin_role)
        user.save()
        messages.success(request, "Profile updated successfully.")
    
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
@staff_required
def admin_elections(request):
    """Elections CRUD — list, create, edit, delete."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            form = ElectionForm(request.POST)
            if form.is_valid():
                election = form.save()
                # Create positions from submitted list
                positions = request.POST.getlist('position_titles[]')
                for i, title in enumerate(positions):
                    if title.strip():
                        Position.objects.create(
                            election=election, title=title.strip(), order=i
                        )
                messages.success(request, f'Election "{election.title}" created successfully.')
                return redirect('admin_elections')
            else:
                messages.error(request, 'Please correct the errors below.')

        elif action == 'edit':
            election_id = request.POST.get('id')
            election = get_object_or_404(Election, id=election_id)
            form = ElectionForm(request.POST, instance=election)
            if form.is_valid():
                form.save()
                messages.success(request, f'Election "{election.title}" updated.')
                return redirect('admin_elections')

        elif action == 'conclude':
            election_id = request.POST.get('id')
            election = get_object_or_404(Election, id=election_id)
            election.end_date = timezone.now()
            election.save()
            messages.success(request, f'Election "{election.title}" has been concluded.')
            return redirect('admin_elections')

        elif action == 'delete':
            election_id = request.POST.get('id')
            election = get_object_or_404(Election, id=election_id)
            title = election.title
            election.delete()
            messages.success(request, f'Election "{title}" deleted.')
            return redirect('admin_elections')

    elections = Election.objects.all().order_by('-created_at')
    form = ElectionForm()

    # For the detail panel, get the selected election
    selected_id = request.GET.get('selected')
    selected_election = None
    if selected_id:
        selected_election = Election.objects.filter(id=selected_id).first()

    context = {
        'elections': elections,
        'form': form,
        'selected_election': selected_election,
    }
    return render(request, 'adminpanel/elections.html', context)


@login_required
@staff_required
def admin_candidates(request):
    """Candidates CRUD — list, create, edit, delete with filtering."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            form = CandidateForm(request.POST, request.FILES)
            if form.is_valid():
                candidate = form.save()
                # Save goals
                goals = request.POST.getlist('goals[]')
                for i, goal in enumerate(goals):
                    if goal.strip():
                        CandidateGoal.objects.create(
                            candidate=candidate, goal=goal.strip(), order=i
                        )
                messages.success(request, f'Candidate "{candidate.full_name}" added.')
                return redirect('admin_candidates')
            else:
                messages.error(request, 'Please correct the errors below.')

        elif action == 'edit':
            candidate_id = request.POST.get('id')
            candidate = get_object_or_404(Candidate, id=candidate_id)
            form = CandidateForm(request.POST, request.FILES, instance=candidate)
            if form.is_valid():
                form.save()
                messages.success(request, f'Candidate "{candidate.full_name}" updated.')
                return redirect('admin_candidates')

        elif action == 'delete':
            candidate_id = request.POST.get('id')
            candidate = get_object_or_404(Candidate, id=candidate_id)
            name = candidate.full_name
            candidate.delete()
            messages.success(request, f'Candidate "{name}" removed.')
            return redirect('admin_candidates')

    # Filtering
    election_id = request.GET.get('election')
    position_id = request.GET.get('position')

    candidates = Candidate.objects.select_related('position__election').all()

    if election_id:
        candidates = candidates.filter(position__election_id=election_id)
    if position_id:
        candidates = candidates.filter(position_id=position_id)

    elections = Election.objects.all()
    positions = Position.objects.all()
    parties = Party.objects.all()
    if election_id:
        positions = positions.filter(election_id=election_id)

    # Grouping by position for the UI divisions
    grouped_candidates = []
    positions_to_show = positions
    if position_id:
        positions_to_show = positions.filter(id=position_id)
    
    for pos in positions_to_show:
        pos_candidates = candidates.filter(position=pos)
        if pos_candidates.exists():
            grouped_candidates.append({
                'position': pos,
                'candidates': pos_candidates
            })

    form = CandidateForm()

    context = {
        'grouped_candidates': grouped_candidates,
        'elections': elections,
        'positions': positions,
        'parties': parties,
        'form': form,
        'selected_election': election_id,
        'selected_position': position_id,
    }
    return render(request, 'adminpanel/candidates.html', context)


@login_required
@staff_required
def admin_voters(request):
    """Paginated voter list with search."""
    q = request.GET.get('q', '')
    voters_qs = Voter.objects.filter(is_staff=False).order_by('-date_joined')

    if q:
        voters_qs = voters_qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        )

    paginator = Paginator(voters_qs, 20)
    page_number = request.GET.get('page')
    voters = paginator.get_page(page_number)

    context = {
        'voters': voters,
        'q': q,
        'total_voters': voters_qs.count(),
    }
    return render(request, 'adminpanel/voters.html', context)


@login_required
@staff_required
def export_voters_csv(request):
    """Stream CSV of all voters."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="voters.csv"'
    writer = csv.writer(response)
    writer.writerow(['Email', 'First Name', 'Last Name', 'DOB', 'Gender', 'Phone', 'Date Joined'])

    for voter in Voter.objects.filter(is_staff=False).order_by('-date_joined'):
        writer.writerow([
            voter.email, voter.first_name, voter.last_name,
            voter.date_of_birth, voter.gender, voter.phone,
            voter.date_joined.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


@login_required
@staff_required
def admin_results(request):
    """Admin results — view results for any election."""
    election_id = request.GET.get('election_id')

    if election_id:
        election = get_object_or_404(Election, id=election_id)
    else:
        election = Election.objects.order_by('-created_at').first()

    positions_with_results = []
    total_votes_cast = 0
    total_eligible = Voter.objects.filter(is_staff=False).count()

    if election:
        for position in election.positions.all():
            candidates_data = []
            position_total = 0

            for candidate in position.candidates.filter(is_active=True):
                vote_count = Vote.objects.filter(
                    candidate=candidate, position=position, election=election
                ).count()
                position_total += vote_count
                candidates_data.append({
                    'candidate': candidate,
                    'vote_count': vote_count,
                })

            for entry in candidates_data:
                entry['percentage'] = round(
                    (entry['vote_count'] / position_total * 100) if position_total > 0 else 0, 1
                )

            candidates_data.sort(key=lambda x: x['vote_count'], reverse=True)
            for i, entry in enumerate(candidates_data):
                entry['rank'] = i + 1

            positions_with_results.append({
                'position': position,
                'ranked_candidates': candidates_data,
                'total_votes': position_total,
                'winner': candidates_data[0] if candidates_data else None,
            })

            total_votes_cast = max(total_votes_cast, position_total)

    turnout = round((total_votes_cast / total_eligible * 100) if total_eligible > 0 else 0, 1)
    all_elections = Election.objects.all().order_by('-created_at')

    context = {
        'election': election,
        'all_elections': all_elections,
        'positions_with_results': positions_with_results,
        'total_votes_cast': total_votes_cast,
        'total_eligible': total_eligible,
        'turnout': turnout,
    }
    return render(request, 'adminpanel/results.html', context)


@login_required
@staff_required
def generate_pdf_report(request, election_id):
    """Generate PDF report for an election."""
    from xhtml2pdf import pisa
    from django.template.loader import render_to_string

    election = get_object_or_404(Election, id=election_id)
    if election.status != 'completed':
        messages.error(request, "Reports can only be generated for concluded elections.")
        return redirect('admin_results')
    positions_with_results = []
    total_votes_cast = 0
    total_eligible = Voter.objects.filter(is_staff=False).count()

    for position in election.positions.all():
        candidates_data = []
        position_total = 0

        for candidate in position.candidates.filter(is_active=True):
            vote_count = Vote.objects.filter(
                candidate=candidate, position=position, election=election
            ).count()
            position_total += vote_count
            candidates_data.append({
                'candidate': candidate,
                'vote_count': vote_count,
            })

        for entry in candidates_data:
            entry['percentage'] = round(
                (entry['vote_count'] / position_total * 100) if position_total > 0 else 0, 1
            )

        candidates_data.sort(key=lambda x: x['vote_count'], reverse=True)
        for i, entry in enumerate(candidates_data):
            entry['rank'] = i + 1

        positions_with_results.append({
            'position': position,
            'ranked_candidates': candidates_data,
            'total_votes': position_total,
        })

        total_votes_cast = max(total_votes_cast, position_total)

    turnout = round((total_votes_cast / total_eligible * 100) if total_eligible > 0 else 0, 1)

    html = render_to_string('adminpanel/pdf_report.html', {
        'election': election,
        'positions': positions_with_results,
        'total_votes_cast': total_votes_cast,
        'total_eligible': total_eligible,
        'turnout': turnout,
        'generated_at': timezone.now(),
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="election-{election.id}-report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response


@login_required
@staff_required
def wipe_database(request):
    """Danger Zone: Wipe all data except admin accounts."""
    if request.method == 'POST':
        # Double-check this is a POST request to prevent accidental GET execution
        
        # Delete models in an order that respects foreign key constraints (Django usually handles this, but explicit is good)
        Vote.objects.all().delete()
        CandidateGoal.objects.all().delete()
        Candidate.objects.all().delete()
        Position.objects.all().delete()
        Election.objects.all().delete()
        
        # Delete all non-staff voters
        Voter.objects.filter(is_staff=False).delete()
        
        messages.success(request, "Database successfully wiped. All elections, candidates, votes, and voters have been permanently deleted.")
        return redirect('admin_dashboard')
        
    messages.error(request, "Invalid request to wipe database.")
    return redirect('admin_dashboard')

