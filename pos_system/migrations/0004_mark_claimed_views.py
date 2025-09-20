from django.db import migrations
from datetime import timedelta

def mark_claimed_views(apps, schema_editor):
    ProductView = apps.get_model('pos_system', 'ProductView')
    RewardClaim = apps.get_model('pos_system', 'RewardClaim')

    for claim in RewardClaim.objects.all():
        views = ProductView.objects.filter(
            product__business=claim.business,
            viewed_at__gte=claim.requested_at - timedelta(days=30),
            viewed_at__lte=claim.requested_at,
            claimed=False
        )
        views_to_claim = views.order_by('viewed_at')[:claim.views_count]
        for view in views_to_claim:
            view.claimed = True
            view.claimed_at = claim.requested_at
            view.claim = claim
            view.save()

class Migration(migrations.Migration):

    dependencies = [
        ('pos_system', '0003_productview_device_type_productview_referrer_and_more'),  # <-- Replace with your actual last migration
    ]

    operations = [
        migrations.RunPython(mark_claimed_views),
    ]
