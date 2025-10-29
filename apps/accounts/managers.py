from typing import Optional
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet


class CustomUserManager(BaseUserManager):

    def email_validator(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError(
                "You must provide a valid email address"
            )

    def validate_user(
            self,
            first_name: str, last_name: str, email: str, password: str
    ) -> Optional[ValidationError]:

        if not first_name:
            raise ValueError(
                "Users must submit a first name"
            )

        if not last_name:
            raise ValueError(
                "Users must submit a last name"
            )

        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValueError(
                "Base User Account: An email address is required"
            )

        if not password:
            raise ValueError(
                "User must have a password"
            )

        return None

    def create_user(
            self,
            first_name: str, last_name: str, email: str, password: str,
            **kwargs
    ) -> QuerySet:

        self.validate_user(
            first_name, last_name, email, password
        )
        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            **kwargs
        )
        user.set_password(password)
        user.save()
        return user

    def validate_superuser(self, **kwargs) -> dict:

        kwargs.setdefault('is_staff', True)
        if kwargs.get('is_staff') is not True:
            raise ValueError(
                "Superusers must have is_staff=True"
            )
        return kwargs

    def create_superuser(
            self,
            first_name: str, last_name: str, email: str, password: str,
            **kwargs
    ) -> QuerySet:

        kwargs = self.validate_superuser(**kwargs)
        user = self.create_user(
            first_name, last_name, email, password, **kwargs
        )
        return user
