from django.db import models
import mongoengine

# Create your models here.
class Student(mongoengine.Document):
    name = mongoengine.StringField(max_length=16)
    age = mongoengine.IntField(default=1)