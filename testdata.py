import os
import django
import random
from datetime import timedelta, date
from django.utils import timezone
from django.utils.text import slugify

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voting_system.settings')
django.setup()

from core.models import Election, Position, Candidate, Party, Voter

def populate():
    print("Populating test data...")
    
    # 1. Create Election (Idempotent)
    election, created = Election.objects.get_or_create(
        title='National General Elections 2025',
        defaults={
            'description': 'The ultimate battle for the future of India.',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30)
        }
    )
    if created:
        print(f"Created Election: {election.title}")
    else:
        print(f"Election already exists: {election.title}")

    # 2. Create Positions
    pm_pos, _ = Position.objects.get_or_create(election=election, title='Prime Minister', defaults={'order': 1})
    pres_pos, _ = Position.objects.get_or_create(election=election, title='President', defaults={'order': 2})
    print("Positions verified: Prime Minister, President")

    # 3. Create Parties (Idempotent)
    parties_to_create = [
        ('BJP', 'parties/bjp.png'),
        ('INC', 'parties/inc.webp'),
        ('AAP', 'parties/aap.png'),
    ]
    
    party_objs = {}
    for name, logo in parties_to_create:
        p, created = Party.objects.get_or_create(name=name, defaults={'logo': logo})
        if not created:
            p.logo = logo
            p.save()
        party_objs[name] = p
    print("Parties verified and logos updated: BJP, INC, AAP")

    # 4. Party Mappings (Manual Mapping for Accuracy)
    party_map = {
        'Narendra Modi': 'BJP',
        'Rahul Gandhi': 'INC',
        'Arvind Kejriwal': 'AAP',
        'Droupadi Murmu': 'BJP',
        'Yashwant Sinha': 'INC',
        'Shashi Tharoor': 'INC'
    }

    # 5. Create Candidates
    candidate_groups = [
        (pm_pos, ['Narendra Modi', 'Rahul Gandhi', 'Arvind Kejriwal'], 'PM'),
        (pres_pos, ['Droupadi Murmu', 'Yashwant Sinha', 'Shashi Tharoor'], 'President')
    ]

    for position, names, label in candidate_groups:
        for name in names:
            party_acronym = party_map.get(name)
            party = Party.objects.filter(name=party_acronym).first()
            
            if not party:
                print(f"Warning: Party {party_acronym} not found for {name}. Using Independent.")
            
            photo_path = f'candidates/{slugify(name)}.jpg'
            
            c, created = Candidate.objects.get_or_create(
                position=position,
                full_name=name,
                defaults={
                    'party': party,
                    'affiliation': party.name if party else 'Independent',
                    'photo': photo_path,
                    'bio': f'Prominent leader associated with {party.name if party else "Independent"}.',
                    'manifesto': 'To build a stronger and more prosperous nation.' if label == 'PM' else 'To uphold the constitution and unity of the country.'
                }
            )
            
            if created:
                print(f"Created Candidate ({label}): {name} [{party_acronym}]")
            else:
                # Update existing records to match the new mappings
                c.party = party
                c.affiliation = party.name if party else 'Independent'
                c.photo = photo_path
                c.save()
                print(f"Updated Candidate ({label}): {name} [{party_acronym}]")

    # 6. Create Test Voters
    # Admin credentials from environment or defaults
    admin_email = os.getenv('ADMIN_EMAIL', 'ansh@vote.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'ansh')

    voter_list = [
        (admin_email, admin_password, 'Ansh', 'Admin'),
        ('voter1@example.com', 'voter123', 'Voter1', 'Test'),
        ('voter2@example.com', 'voter123', 'Voter2', 'Test'),
        ('voter3@example.com', 'voter123', 'Voter3', 'Test'),
        ('voter4@example.com', 'voter123', 'Voter4', 'Test'),
    ]

    for i, (email, password, fname, lname) in enumerate(voter_list):
        if not Voter.objects.filter(email=email).exists():
            if i == 0: # Make the first user (Ansh) a superuser
                Voter.objects.create_superuser(
                    email=email,
                    password=password,
                    first_name=fname,
                    last_name=lname,
                    date_of_birth=date(1990, 1, 1),
                    gender='Male',
                    phone='9876543210'
                )
                print(f"Created Admin Superuser: {email}")
            else:
                Voter.objects.create_user(
                    email=email,
                    password=password,
                    first_name=fname,
                    last_name=lname,
                    date_of_birth=date(1990, 1, 1),
                    gender='Male',
                    phone='9876543210'
                )
                print(f"Created Voter: {email}")
        else:
            if i == 0: # Ensure Ansh is a superuser and reset password if needed
                v = Voter.objects.get(email=email)
                v.is_staff = True
                v.is_superuser = True
                v.set_password(password) # Update to the secret password
                v.save()
                print(f"Verified/Updated Admin: {email}")
            else:
                print(f"Voter already exists: {email}")

    print("\nPopulation complete! All candidates are now mapped to their correct parties.")

if __name__ == '__main__':
    populate()
