from django.db import models
from django.utils.text import slugify
import uuid

from base.models import BaseModel
from provider.generate.enum import ProviderEnum
from authentication.models import AuthUser
from provider.helpers import encrypt_value, decrypt_value

# Create your models here.

class ProviderAPIKey(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(AuthUser, related_name="auth_user", on_delete=models.CASCADE)
    provider = models.CharField(max_length=100, default=ProviderEnum.GROQ.name)
    api_key = models.CharField(max_length=255) 
    slug = models.SlugField(unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.provider}"

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(f"{self.user.username}-{self.provider}")

        # Encrypt the API key before saving
        if self.api_key:
            self.api_key = encrypt_value(self.api_key)

        super(ProviderAPIKey, self).save(*args, **kwargs)

    def get_decrypted_api_key(self):
        return decrypt_value(self.api_key)