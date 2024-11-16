from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.core.validators import RegexValidator
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
import secrets
from django.conf import settings

from base.models import BaseModel
from main.email import send_email


class CustomUserManager(BaseUserManager):
    def create_user(
        self, username, email, firstname, lastname, password=None, **extra_fields
    ):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            firstname=firstname,
            lastname=lastname,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, username, email, firstname, lastname, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(
            username, email, firstname, lastname, password, **extra_fields
        )


class AuthUser(AbstractBaseUser, PermissionsMixin):
    auth_provider = models.CharField(max_length=20, default="email")
    username = models.CharField(
        max_length=150,
        unique=True,
        # validators=[
        #     RegexValidator(
        #         regex=r"^\w+$",
        #         message="Username must contain only letters, numbers, or underscores",
        #     )
        # ],
    )
    email = models.EmailField(unique=True, db_index=True)
    firstname = models.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z]+$", message="Firstname must contain only letters"
            )
        ],
    )
    lastname = models.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s]+$",
                message="Lastname must contain only letters and spaces",
            )
        ],
    )
    is_staff = models.BooleanField(
        "staff status",
        default=False,
        help_text="Designates whether the user can log into this admin site.",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email", "firstname", "lastname"]

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(firstname__iregex=r"^[a-zA-Z]+$"), name="firstname_valid"
            ),
            models.CheckConstraint(
                check=models.Q(lastname__iregex=r"^[a-zA-Z\s]+$"), name="lastname_valid"
            ),
        ]

    def __str__(self):
        return self.username


class APIKey(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, default="Default")
    key = models.CharField(max_length=128, unique=True)
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}"


@receiver(post_save, sender=AuthUser)
def create_api_key(sender, instance, created, **kwargs):
    if created:
        # Generate a secure random API key
        api_key = secrets.token_urlsafe(32)
        APIKey.objects.create(name="Default", user=instance, key=api_key)


class Newsletter(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)

    def __str__(self) -> str:
        return self.email


@receiver(post_save, sender=Newsletter)
def send_thank_you_email(sender, instance, created, **kwargs):
    if created:
        # Only send the email when a new instance is created
        subject = "🎉 Thank You for Subscribing to LLM Gateway! 🎉"
        text_content = (
            "Hi there,\n\n"
            "Thank you for subscribing to our newsletter. Stay tuned for exciting updates and insights!\n\n"
            "Best regards,\nThe LLM Gateway Team"
        )
        html_template = "emails/newsletter_thank_you.html"
        context = {
            "support_mail": "support@llmgateway.com",
            "email": instance.email,
            "year": "2024",
            "website_link": settings.PLATFORM_URL,
        }

        # Use the reusable send_mail function
        send_email(
            recipients=[instance.email],
            subject=subject,
            plain_text_message=text_content,
            html_template=html_template,
            context=context,
        )
