import re
from rest_framework import serializers
from .models import AuthUser, APIKey


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ("id", "username", "email", "firstname", "lastname", "password")
        extra_kwargs = {"password": {"write_only": True, "min_length": 8}}

    def validate_username(self, value):
        # Additional validation for username
        if not value.isalnum() and not all(x in "_ " for x in value):
            raise serializers.ValidationError(
                "Username must contain only letters, numbers, or underscores."
            )
        return value

    def validate_firstname(self, value):
        # Validate that firstname contains only letters
        if not value.isalpha():
            raise serializers.ValidationError("Firstname must contain only letters.")
        return value

    def validate_lastname(self, value):
        # Validate that lastname contains only letters
        if not value.isalpha():
            raise serializers.ValidationError("Lastname must contain only letters.")
        return value

    def validate_email(self, value):
        # Validate the email format using a regular expression.
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid Email format")

        return value

    def create(self, validated_data):
        # Create a new user instance with a hashed password
        user = AuthUser(
            username=validated_data["username"],
            email=validated_data["email"],
            firstname=validated_data["firstname"],
            lastname=validated_data["lastname"],
        )
        user.set_password(validated_data["password"])  # Hash the password
        user.save()
        return user

    def update(self, instance, validated_data):
        # Update user information, handling the password correctly
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.firstname = validated_data.get("firstname", instance.firstname)
        instance.lastname = validated_data.get("lastname", instance.lastname)

        # Hash new password if it's provided
        if "password" in validated_data:
            instance.set_password(validated_data["password"])

        instance.save()
        return instance


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ["key", "user"]