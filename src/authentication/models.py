from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.core.validators import RegexValidator
from base.models import BaseModel
import uuid

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
            **extra_fields
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
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\w+$",
                message="Username must contain only letters, numbers, or underscores",
            )
        ],
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
                regex=r"^[a-zA-Z]+$", message="Lastname must contain only letters"
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
                check=models.Q(lastname__iregex=r"^[a-zA-Z]+$"), name="lastname_valid"
            ),
        ]

    def __str__(self):
        return self.username
    
class APIKey(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=128, unique=True)
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}"