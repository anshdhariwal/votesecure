from django.db import migrations

def normalize_logos(apps, schema_editor):
    Party = apps.get_model('core', 'Party')
    for party in Party.objects.all():
        if party.logo:
            old_name = party.logo.name
            new_name = old_name.lower()
            if old_name != new_name:
                party.logo.name = new_name
                party.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_candidate_photo'),
    ]

    operations = [
        migrations.RunPython(normalize_logos),
    ]
