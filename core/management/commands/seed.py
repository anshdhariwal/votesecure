import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Voter, Election, Position, Candidate, CandidateGoal, Vote


class Command(BaseCommand):
    help = 'Seed the database with demo data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...\n')

        # ── Superuser ──
        if not Voter.objects.filter(email='admin@vote.com').exists():
            Voter.objects.create_superuser(
                email='admin@vote.com',
                password='Admin@1234',
                first_name='Admin',
                last_name='User',
                date_of_birth='1990-01-15',
                gender='Male',
                phone='+91 98765 43210',
            )
            self.stdout.write(self.style.SUCCESS('  [OK] Superuser created: admin@vote.com / Admin@1234'))
        else:
            self.stdout.write('  -> Superuser already exists.')

        # ── Active Election ──
        now = timezone.now()
        election, created = Election.objects.get_or_create(
            title='Lok Sabha General Elections 2025',
            defaults={
                'description': 'The 18th general elections to constitute the Lok Sabha. '
                               'All eligible Indian citizens aged 18 and above can exercise their democratic right.',
                'start_date': now - timedelta(days=7),
                'end_date': now + timedelta(days=30),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  [OK] Election created: Lok Sabha 2025'))
        else:
            self.stdout.write('  -> Election already exists.')

        # ── Positions ──
        position_data = [
            ('Prime Minister', 0),
            ('President', 1),
            ('Vice President', 2),
            ('Chief Minister', 3),
            ('Member of Parliament', 4),
        ]

        positions = []
        for title, order in position_data:
            pos, _ = Position.objects.get_or_create(
                election=election, title=title,
                defaults={'order': order}
            )
            positions.append(pos)

        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(positions)} positions created/verified'))

        # ── Candidates (3 per position) ──
        candidates_data = {
            'Prime Minister': [
                ('Aarav Mehta', 'BJP', 'Veteran leader with 30 years of governance experience. Architect of Digital India and economic reforms.',
                 'Building a self-reliant India through technology, infrastructure, and social welfare programs.',
                 ['Digital Infrastructure for Rural India', 'Clean Energy by 2030', 'Universal Healthcare Coverage']),
                ('Priya Iyer', 'INC', 'Progressive leader focused on inclusive growth, education reform, and environmental sustainability.',
                 'A compassionate India that leads in education, health, and green innovation.',
                 ['Education Budget Doubled', 'National Employment Guarantee', 'Climate Action Framework']),
                ('Rohan Sharma', 'AAP', 'Anti-corruption crusader with proven governance track record in state-level administration.',
                 'Transparent governance with zero tolerance for corruption and citizen-centric policy making.',
                 ['Free Quality Education K-12', 'Anti-Corruption Task Force', 'Affordable Housing for All']),
            ],
            'President': [
                ('Deepa Narayan', 'BJP', 'Constitutional expert and former Supreme Court judge with impeccable integrity.',
                 'Upholding the Constitution while modernizing governance frameworks.',
                 ['Constitutional Reform Commission', 'Judicial Independence Strengthening', 'National Integration Council']),
                ('Vikram Patel', 'INC', 'Distinguished diplomat and former UN representative championing global cooperation.',
                 'India as a beacon of democracy and multilateral cooperation on the world stage.',
                 ['Strengthen Democratic Institutions', 'Global Peace Advocacy', 'Cultural Heritage Preservation']),
                ('Ananya Krishnan', 'Independent', 'Award-winning social activist and Nobel nominee for grassroots democracy initiatives.',
                 'A presidency rooted in social justice and grassroots empowerment.',
                 ['Grassroots Democracy Programs', 'Tribal Rights Protection', 'National Women Commission Reform']),
            ],
            'Vice President': [
                ('Rajesh Gupta', 'BJP', 'Seasoned parliamentarian with expertise in legislative reform and federalism.',
                 'Efficient parliamentary proceedings and stronger center-state relations.',
                 ['Parliamentary Modernization', 'Federal Cooperation Framework', 'Legislative Efficiency Act']),
                ('Sunita Devi', 'INC', 'Women rights advocate and education reformer with national recognition.',
                 'Empowering women through legislative action and social reform.',
                 ['Women Empowerment Bills', 'Educational Quality Standards', 'Social Justice Enhancement']),
                ('Karthik Reddy', 'AAP', 'Tech entrepreneur turned politician focused on governance innovation.',
                 'Data-driven governance and transparent legislative process.',
                 ['E-Governance Expansion', 'Open Data Policy', 'Youth in Parliament Initiative']),
            ],
            'Chief Minister': [
                ('Arun Singh', 'BJP', 'Dynamic leader with successful state-level developmental track record.',
                 'Smart cities, industrialization, and agricultural modernization.',
                 ['Smart City Development', 'Industrial Corridor Expansion', 'Agricultural Technology Adoption']),
                ('Meera Joshi', 'INC', 'Grassroots organizer with expertise in rural development and welfare.',
                 'Bridging the urban-rural divide through inclusive development.',
                 ['Rural Infrastructure Development', 'Water Security Program', 'Skill Development Centers']),
                ('Farhan Khan', 'AAP', 'Urban planning expert focused on sustainable city development.',
                 'Livable cities with clean air, green spaces, and efficient transport.',
                 ['Clean Air Initiative', 'Public Transport Revolution', 'Affordable Housing Scheme']),
            ],
            'Member of Parliament': [
                ('Nisha Patel', 'BJP', 'Constituency worker dedicated to bringing development funds to local communities.',
                 'Transforming constituency through infrastructure and employment generation.',
                 ['Local Infrastructure Fund', 'Employment Generation Programs', 'Healthcare Access Improvement']),
                ('Amit Das', 'INC', 'Social worker focused on education and healthcare in underserved areas.',
                 'Every child educated, every family healthy — building from the ground up.',
                 ['Community Health Centers', 'School Quality Improvement', 'Micro-Enterprise Support']),
                ('Lakshmi Rao', 'AAP', 'Environmental activist pushing for sustainable development legislation.',
                 'Green development that balances economic growth with environmental protection.',
                 ['River Cleanup Mission', 'Green Industrial Policy', 'Renewable Energy Incentives']),
            ],
        }

        candidate_count = 0
        for position in positions:
            if position.title in candidates_data:
                for name, party, bio, manifesto, goals in candidates_data[position.title]:
                    candidate, created = Candidate.objects.get_or_create(
                        position=position,
                        full_name=name,
                        defaults={
                            'affiliation': party,
                            'bio': bio,
                            'manifesto': manifesto,
                            'is_active': True,
                        }
                    )
                    if created:
                        candidate_count += 1
                        for i, goal in enumerate(goals):
                            CandidateGoal.objects.get_or_create(
                                candidate=candidate, goal=goal,
                                defaults={'order': i}
                            )

        self.stdout.write(self.style.SUCCESS(f'  [OK] {candidate_count} candidates created with goals'))

        # ── Regular Voters ──
        voter_data = [
            ('Arjun', 'Kumar', '1998-03-15', 'Male'),
            ('Sneha', 'Reddy', '1995-07-22', 'Female'),
            ('Rahul', 'Verma', '2000-01-10', 'Male'),
            ('Kavya', 'Nair', '1997-11-05', 'Female'),
            ('Aditya', 'Chopra', '1999-06-30', 'Male'),
            ('Divya', 'Menon', '1996-09-18', 'Female'),
            ('Siddharth', 'Jain', '2001-02-14', 'Male'),
            ('Pooja', 'Bhat', '1994-12-25', 'Female'),
            ('Nikhil', 'Saxena', '1998-08-08', 'Male'),
            ('Riya', 'Kapoor', '2000-04-20', 'Female'),
        ]

        voters = []
        for i, (first, last, dob, gender) in enumerate(voter_data, 1):
            email = f'voter{i}@vote.com'
            voter, created = Voter.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'date_of_birth': dob,
                    'gender': gender,
                    'phone': f'+91 9{random.randint(1000000000, 9999999999)}'[:15],
                }
            )
            if created:
                voter.set_password('Voter@1234')
                voter.save()
            voters.append(voter)

        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(voters)} voter accounts ready (password: Voter@1234)'))

        # ── Cast votes for first 5 voters ──
        voting_voters = voters[:5]
        votes_created = 0

        for voter in voting_voters:
            for position in positions:
                if not Vote.objects.filter(voter=voter, position=position).exists():
                    candidates = list(position.candidates.filter(is_active=True))
                    if candidates:
                        chosen = random.choice(candidates)
                        Vote.objects.create(
                            voter=voter,
                            candidate=chosen,
                            position=position,
                            election=election,
                        )
                        votes_created += 1

        self.stdout.write(self.style.SUCCESS(f'  [OK] {votes_created} votes cast by 5 voters'))

        self.stdout.write(self.style.SUCCESS('\n[DONE] Seeding complete! Run: python manage.py runserver'))
        self.stdout.write(self.style.SUCCESS('   Login as admin: admin@vote.com / Admin@1234'))
        self.stdout.write(self.style.SUCCESS('   Login as voter: voter1@vote.com / Voter@1234'))
