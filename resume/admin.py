from django.contrib import admin
from .models import Profile, Education, Experience, Skill, Project

admin.site.register(Profile)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(Skill)
admin.site.register(Project)