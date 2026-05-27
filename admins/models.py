from django.db import models

# Create your models here.

class AdminProfile(models.Model):
    name = models.CharField(max_length=250, blank=True, null=True)
    address = models.CharField(max_length=1000, blank=True, null=True)
    phone = models.CharField(max_length=250, blank=True, null=True)
    facebook = models.URLField(max_length=250, blank=True, null=True)
    gmail = models.EmailField(unique=True)
    linkedin = models.URLField(max_length=250, blank=True, null=True)
    x = models.URLField(max_length=250, blank=True, null=True)
    github = models.URLField(max_length=250, blank=True, null=True)


    def __str__(self):
        return f"Admin Profile"

class MessageContact(models.Model):
    name = models.CharField(max_length=250, blank=True, null=True)
    email = models.EmailField()
    subject = models.TextField()
    message = models.TextField()

    def __str__(self):
        return f"Messgage Contact"
