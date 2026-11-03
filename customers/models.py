from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Automatically creates a dedicated PostgreSQL schema when a tenant is saved
    auto_create_schema = True

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

class Domain(DomainMixin):
    pass