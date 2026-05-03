import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decorators import voter_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from .models import Voter, Election, Position, Candidate, CandidateGoal, Vote
from .forms import SignupStep1Form, SignupStep2Form, LoginForm, ForgotPasswordForm


def homepage(request):
    """Public homepage showing active election info."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('voter_home')

    active_election = Election.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).first()
    total_voters = Voter.objects.filter(is_staff=False).count()
    total_votes = Vote.objects.count()
    context = {
        'active_election': active_election,
        'total_voters': total_voters,
        'total_votes': total_votes,
    }
    return render(request, 'core/homepage.html', context)


def signup_step1(request):
    """Signup step 1: personal details. Stores data in session."""
    if request.user.is_authenticated:
        return redirect('voter_home')

    if request.method == 'POST':
        form = SignupStep1Form(request.POST)
        if form.is_valid():
            request.session['signup_data'] = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'date_of_birth': form.cleaned_data['date_of_birth'].isoformat(),
                'gender': form.cleaned_data['gender'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data['phone'],
            }
            return redirect('signup_step2')
    else:
        initial = request.session.get('signup_data', {})
        form = SignupStep1Form(initial=initial)

    return render(request, 'core/signup_step1.html', {'form': form})


def signup_step2(request):
    """Signup step 2: set password. Creates the Voter account."""
    if request.user.is_authenticated:
        return redirect('voter_home')

    signup_data = request.session.get('signup_data')
    if not signup_data:
        return redirect('signup_step1')

    if request.method == 'POST':
        form = SignupStep2Form(request.POST)
        if form.is_valid():
            try:
                from datetime import date as date_cls
                dob = date_cls.fromisoformat(signup_data['date_of_birth'])
                user = Voter.objects.create_user(
                    email=signup_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=signup_data['first_name'],
                    last_name=signup_data['last_name'],
                    date_of_birth=dob,
                    gender=signup_data['gender'],
                    phone=signup_data['phone'],
                )
                # Clean up session data
                del request.session['signup_data']
                login(request, user)
                messages.success(request, 'Account created successfully! Welcome to VoteSecure.')
                return redirect('voter_home')
            except Exception as e:
                # Clean up session on failure too
                request.session.pop('signup_data', None)
                messages.error(request, f'Registration failed: {str(e)}')
                return redirect('signup_step1')
    else:
        form = SignupStep2Form()

    return render(request, 'core/signup_step2.html', {
        'form': form,
        'signup_data': signup_data,
    })


def login_view(request):
    """Login with email and password."""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('voter_home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                
                if user.is_staff or user.is_superuser:
                    return redirect('admin_dashboard')
                    
                next_url = request.GET.get('next', 'voter_home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """Log out user (POST only for CSRF protection)."""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out.')
    return redirect('homepage')


def forgot_password(request):
    """Forgot password — sends reset email (console backend in dev)."""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if Voter.objects.filter(email=email).exists():
                # In production, send actual reset email
                messages.success(request, 'Password reset link has been sent to your email.')
            else:
                messages.error(request, 'No account found with this email address.')
    else:
        form = ForgotPasswordForm()

    return render(request, 'core/forgot_password.html', {'form': form})


@voter_required
def change_password(request):
    """Allow logged-in users to change their password directly."""
    from django.contrib.auth import update_session_auth_hash
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user) # Keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('voter_home')
            
    return render(request, 'core/change_password.html')


@voter_required
def voter_home(request):
    """Voter dashboard — shows election status and voting state."""
    election = Election.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).first()

    # Also check for the most recent completed election if no active one
    if not election:
        election = Election.objects.filter(
            end_date__lt=timezone.now()
        ).order_by('-end_date').first()

    has_voted = False
    votes_cast = []
    time_remaining = None

    if election:
        has_voted = Vote.objects.filter(
            voter=request.user, election=election
        ).exists()

        if has_voted:
            votes_cast = Vote.objects.filter(
                voter=request.user, election=election
            ).select_related('candidate', 'position')

        if election.is_active:
            time_remaining = election.end_date - timezone.now()

    # Success toast after voting
    if request.GET.get('voted') == '1':
        messages.success(request, 'Your vote has been recorded securely!')

    winners = []
    if election and election.status == 'completed':
        from django.db.models import Count
        for position in election.positions.all():
            winner = position.candidates.annotate(
                vote_count=Count('votes')
            ).order_by('-vote_count').first()
            if winner and winner.vote_count > 0:
                winners.append({
                    'position': position.title,
                    'candidate': winner
                })

    context = {
        'election': election,
        'has_voted': has_voted,
        'votes_cast': votes_cast,
        'time_remaining': time_remaining,
        'winners': winners,
    }
    return render(request, 'core/home.html', context)


@login_required
def voter_candidates(request):
    """List of all candidates for voters."""
    positions = Position.objects.all().prefetch_related('candidates__party')
    
    # Check if there is a concluded election to show winners
    latest_election = Election.objects.order_by('-end_date').first()
    
    context = {
        'positions': positions,
        'latest_election': latest_election,
    }
    return render(request, 'core/candidates.html', context)


@voter_required
def vote_page(request):
    """Vote page — shows ballot or processes vote submission."""
    election = Election.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).first()

    if not election:
        messages.error(request, 'No active election at this time.')
        return redirect('voter_home')

    # Check if already voted
    if Vote.objects.filter(voter=request.user, election=election).exists():
        messages.info(request, 'You have already cast your vote in this election.')
        return redirect('voter_home')

    if request.method == 'POST':
        # AJAX vote submission
        try:
            data = json.loads(request.body)
            votes_data = data.get('votes', {})

            if not votes_data:
                return JsonResponse({'error': 'No votes submitted.'}, status=400)

            # Validate election is still active
            if not election.is_active:
                return JsonResponse({'error': 'This election has ended.'}, status=400)

            # Double-check hasn't voted
            if Vote.objects.filter(voter=request.user, election=election).exists():
                return JsonResponse({'error': 'You have already voted.'}, status=400)

            # Validate all positions are filled
            positions = election.positions.all()
            position_ids = set(str(p.id) for p in positions)
            submitted_ids = set(votes_data.keys())

            if position_ids != submitted_ids:
                return JsonResponse({'error': 'You must vote for all positions.'}, status=400)

            # Atomically create all vote records
            with transaction.atomic():
                for position_id_str, candidate_id_str in votes_data.items():
                    position = get_object_or_404(Position, id=int(position_id_str), election=election)
                    candidate = get_object_or_404(Candidate, id=int(candidate_id_str), position=position, is_active=True)

                    Vote.objects.create(
                        voter=request.user,
                        candidate=candidate,
                        position=position,
                        election=election,
                    )

            return JsonResponse({'success': True})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request data.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # GET — render the ballot
    positions = election.positions.prefetch_related('candidates').all()
    context = {
        'election': election,
        'positions': positions,
    }
    return render(request, 'core/vote.html', context)


@voter_required
def candidate_detail(request, candidate_id):
    """Returns candidate details as JSON for the modal overlay."""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    goals = list(candidate.goals.values_list('goal', flat=True))
    data = {
        'id': candidate.id,
        'full_name': candidate.full_name,
        'party_name': candidate.party.name if candidate.party else None,
        'party_logo': candidate.party.logo.url if candidate.party and candidate.party.logo else None,
        'affiliation': candidate.affiliation,
        'bio': candidate.bio,
        'manifesto': candidate.manifesto,
        'photo': candidate.photo.url if candidate.photo else None,
        'position': candidate.position.title,
        'goals': goals,
    }
    return JsonResponse(data)


def results_page(request):
    """Public results page — shows tallies for the most recent completed/active election."""
    election = Election.objects.filter(
        end_date__lt=timezone.now()
    ).order_by('-end_date').first()

    if not election:
        # Show active election if no completed ones
        election = Election.objects.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()

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

            # Calculate percentages and rank
            for entry in candidates_data:
                entry['percentage'] = round(
                    (entry['vote_count'] / position_total * 100) if position_total > 0 else 0, 1
                )

            candidates_data.sort(key=lambda x: x['vote_count'], reverse=True)

            # Assign ranks
            for i, entry in enumerate(candidates_data):
                entry['rank'] = i + 1

            positions_with_results.append({
                'position': position,
                'ranked_candidates': candidates_data,
                'total_votes': position_total,
                'winner': candidates_data[0] if candidates_data else None,
            })

            total_votes_cast = Vote.objects.filter(election=election).values('voter').distinct().count()

    turnout = round((total_votes_cast / total_eligible * 100) if total_eligible > 0 else 0, 1)

    context = {
        'election': election,
        'positions_with_results': positions_with_results,
        'total_votes_cast': total_votes_cast,
        'total_eligible': total_eligible,
        'turnout': turnout,
    }
    return render(request, 'core/results.html', context)


def custom_404(request, exception):
    """Custom 404 error page."""
    return render(request, '404.html', status=404)
