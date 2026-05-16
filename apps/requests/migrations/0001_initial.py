from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InternalRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_type", models.CharField(choices=[("vacation", "Vacation"), ("permission", "Permission"), ("reimbursement", "Reimbursement"), ("document", "Document Request"), ("personal_data", "Personal Data Change")], max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("in_review", "In Review"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("amount", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Internal Request",
                "verbose_name_plural": "Internal Requests",
                "ordering": ["-created_at"],
            },
        ),
    ]
