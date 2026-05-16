from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("requests", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Approval",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("decision", models.CharField(choices=[("approved", "Approved"), ("rejected", "Rejected")], max_length=10)),
                ("comment", models.TextField(blank=True, default="")),
                ("decided_at", models.DateTimeField(auto_now_add=True)),
                ("approver", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approvals_made", to=settings.AUTH_USER_MODEL)),
                ("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="approvals", to="requests.internalrequest")),
            ],
            options={
                "verbose_name": "Approval",
                "verbose_name_plural": "Approvals",
                "ordering": ["-decided_at"],
            },
        ),
    ]
