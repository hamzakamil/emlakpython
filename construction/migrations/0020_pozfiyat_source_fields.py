from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("construction", "0019_pozfiyat_donem"),
    ]

    # STABILIZASYON (2026-09-22): 0019_pozfiyat_donem zaten ice_aktarma_tarihi
    # alanini ekliyor. Bu migration yinelenen AddField iceriyordu ve sifirdan
    # kurulumda (test DB) DuplicateColumn hatasi veriyordu. Zinciri bozmamak
    # icin dosya korunup operasyonlar bos birakildi; veri kaybi yoktur.
    operations = []
