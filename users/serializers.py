"""Kullanıcı serializer'ları — /auth/me ve ileride kullanıcı yönetimi için."""

from rest_framework import serializers

from tenants.models import Tenant

from .models import User


class KullaniciSerializer(serializers.ModelSerializer):
    """Oturum açan kullanıcının bilgisi (parola/hash dışarı sızmaz).

    ``tenant`` pk'ya ek olarak ``tenant_ad`` salt-okunur alanıyla topbar'da
    gerçek firma adı gösterilir (frontend ek istek atmaz).
    """

    tenant_ad = serializers.CharField(source="tenant.name", read_only=True, default=None)
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        return "super_admin" if obj.is_superuser else obj.role

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name",
            "role", "tenant", "tenant_ad",
        )
        read_only_fields = fields


class TenantSecimSerializer(serializers.ModelSerializer):
    """GET /api/v1/tenants/ listesi — yalnızca id/slug/ad (yalnızca süper admin)."""

    class Meta:
        model = Tenant
        fields = ("id", "name", "slug", "is_active")
        read_only_fields = fields


class TenantSerializer(serializers.ModelSerializer):
    """Süper admin firma (tenant) yönetimi — tam CRUD + limitler."""

    class Meta:
        model = Tenant
        fields = (
            "id", "name", "slug", "is_active",
            "max_users", "max_projects", "max_storage_gb",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class KullaniciYonetimSerializer(serializers.ModelSerializer):
    """Süper admin kullanıcı yönetimi — parola yazılabilir, tenant/rol atanır.

    - ``password`` yalnızca yazılabilir; okunmaz (hash dışarı sızmaz).
    - Oluştururken parola verilmezse kullanılamaz parola atanır.
    - Güncellerken parola boş bırakılırsa mevcut parola korunur.
    """

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={"input_type": "password"},
        help_text="Yalnızca yazılabilir; boş bırakılırsa mevcut parola korunur.",
    )

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name",
            "role", "tenant", "is_active", "password",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            self._parola_dogrula(password, user)
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            self._parola_dogrula(password, instance)
            instance.set_password(password)
        instance.save()
        return instance

    @staticmethod
    def _parola_dogrula(password, user):
        """AUTH_PASSWORD_VALIDATORS standardını API'ye uygula (serializer
        save'de Django validasyonu çalışmaz; FAZ 7Q ile aynı desen)."""
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError

        try:
            validate_password(password, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages})

