from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Create or update demo admin and viewer users with auth tokens."

    def handle(self, *args, **options):
        admin = self._upsert_user(
            username=settings.DEMO_USERNAME,
            password=settings.DEMO_PASSWORD,
            email=settings.DEMO_EMAIL,
            is_staff=True,
        )
        viewer = self._upsert_user(
            username=settings.DEMO_VIEWER_USERNAME,
            password=settings.DEMO_VIEWER_PASSWORD,
            email=settings.DEMO_VIEWER_EMAIL,
            is_staff=False,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Admin '{admin.username}' (role=admin). "
                f"Token: {Token.objects.get(user=admin).key}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Viewer '{viewer.username}' (role=viewer). "
                f"Token: {Token.objects.get(user=viewer).key}"
            )
        )

        # Retire legacy demo username if present.
        User = get_user_model()
        legacy = User.objects.filter(username="demo").first()
        if legacy and legacy.username != settings.DEMO_USERNAME:
            legacy.is_active = False
            legacy.save(update_fields=["is_active"])
            self.stdout.write("Deactivated legacy user 'demo'.")

    def _upsert_user(self, *, username, password, email, is_staff):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        user.email = email
        user.set_password(password)
        user.is_staff = is_staff
        user.save()
        Token.objects.get_or_create(user=user)
        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} user '{username}' (staff={is_staff}).")
        return user
