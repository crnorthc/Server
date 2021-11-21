from django.contrib.auth.models import User
from django.db import models


class Admin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=43, primary_key=True)
    email = models.EmailField(null=False)
    level = models.IntegerField()

    class Meta:
        db_table = 'admin'