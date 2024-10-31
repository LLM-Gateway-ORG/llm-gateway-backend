from django.db import models
from django.utils.text import slugify

from base.models import BaseModel
from provider.chat.enum import ProviderEnum
from authentication.models import AuthUser
from provider.helpers import encrypt_value, decrypt_value

# Create your models here.

class ProviderAPIKey(BaseModel):
    user = models.ForeignKey(AuthUser, related_name="auth_user", on_delete=models.CASCADE)
    provider = models.CharField(choices=ProviderEnum.choices(), max_length=100)
    api_key = models.CharField(max_length=255) 
    slug = models.SlugField(unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.provider}"

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(f"{self.user.username}-{self.provider}")

        # Encrypt the API key before saving
        if self.api_key and not self._state.adding:  # Encrypt only on creation
            self.api_key = encrypt_value(self.api_key)

        super(ProviderAPIKey, self).save(*args, **kwargs)

    def get_decrypted_api_key(self):
        return decrypt_value(self.api_key)