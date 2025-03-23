from django.contrib import admin
from .models import Fish, FishBase, User

# Register your models here.

admin.site.register(User)
admin.site.register(Fish)
admin.site.register(FishBase)
