from django.db import migrations


def backfill_onboarding(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    profiles = UserProfile.objects.select_related('user').filter(user__onboarding_completed=False)
    for profile in profiles:
        user = profile.user
        avatar_name = profile.avatar.name if profile.avatar else ''
        complete = bool(
            (user.first_name or '').strip()
            and (user.last_name or '').strip()
            and (profile.address or '').strip()
            and avatar_name
            and 'placeholder' not in avatar_name
        )
        if complete:
            user.onboarding_completed = True
            user.save(update_fields=['onboarding_completed'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_customuser_onboarding_completed_userprofile_address_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_onboarding, noop),
    ]
