from django.contrib import admin
from authentication.models import AuthUser, APIKey

# Register your models here.
admin.site.register(AuthUser)
admin.site.register(APIKey)