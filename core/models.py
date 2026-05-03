from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.text import slugify
import os


# ── Custom Manager ───────────────────────────────────────────────────────────
class VoterManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


# ── Custom User (Voter) ──────────────────────────────────────────────────────
class Voter(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')
    ])
    phone = models.CharField(max_length=15)
    admin_role = models.CharField(max_length=100, default='Secure Clearance')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'date_of_birth']

    objects = VoterManager()

    class Meta:
        verbose_name = 'Voter'

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.email


# ── Election ─────────────────────────────────────────────────────────────────
class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    @property
    def status(self):
        from django.utils import timezone
        now = timezone.now()
        if now < self.start_date:
            return 'upcoming'
        elif now > self.end_date:
            return 'completed'
        return 'active'

    def __str__(self):
        return self.title


# ── Position ─────────────────────────────────────────────────────────────────
class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE,
                                 related_name='positions')
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.election.title} — {self.title}"


# ── Party ───────────────────────────────────────────────────────────────────
class Party(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='parties/', blank=True, null=True)
    
    class Meta:
        verbose_name_plural = 'Parties'

    def __str__(self):
        return self.name


# ── Candidate ────────────────────────────────────────────────────────────────
def candidate_photo_path(instance, filename):
    """Renames the uploaded photo to match the candidate's full name."""
    ext = filename.split('.')[-1]
    name = slugify(instance.full_name)
    return f'candidates/{name}.{ext}'


class Candidate(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE,
                                 related_name='candidates')
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='candidates')
    full_name = models.CharField(max_length=150)
    affiliation = models.CharField(max_length=150, blank=True)
    photo = models.ImageField(upload_to=candidate_photo_path, blank=True, null=True)
    bio = models.TextField(blank=True)
    manifesto = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_winner(self):
        """Checks if this candidate won their position in the election."""
        election = self.position.election
        if election.status != 'completed':
            return False
            
        # Count votes for all candidates in this position
        from django.db.models import Count
        candidates = self.position.candidates.annotate(
            vote_count=Count('votes')
        ).order_by('-vote_count')
        
        if not candidates.exists():
            return False
            
        winner = candidates.first()
        # Ensure they actually have votes
        if winner.vote_count == 0:
            return False
            
        return self.id == winner.id

    def __str__(self):
        return f"{self.full_name} ({self.position.title})"


# ── CandidateGoal ─────────────────────────────────────────────────────────────
class CandidateGoal(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE,
                                  related_name='goals')
    goal = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.candidate.full_name}: {self.goal[:50]}"


# ── Vote ─────────────────────────────────────────────────────────────────────
class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE,
                              related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE,
                                  related_name='votes')
    position = models.ForeignKey(Position, on_delete=models.CASCADE,
                                 related_name='votes')
    election = models.ForeignKey(Election, on_delete=models.CASCADE,
                                 related_name='votes')
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('voter', 'position')]

    def __str__(self):
        return f"{self.voter.email} → {self.candidate.full_name} ({self.position.title})"
