from django.contrib import admin

from accounts.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "is_staff", "created_at"]
    search_fields = ["name", "email"]
    fields = ["name", "email", "is_staff"]  # a senha não é editada por aqui
