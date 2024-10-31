from django.db import models

class BaseModel(models.Model):
    """
    Base Class field added as abstraction class.
    those default field abstract all other needed class
    created_at, updated_at entry datetime
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True