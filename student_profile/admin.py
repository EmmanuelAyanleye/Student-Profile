from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AdminStaff, Student

class AdminStaffAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'title', 'role', 'is_active', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('title', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),  # include is_superuser
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'title', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )

    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except Exception as e:
            self.message_user(request, f"Error saving user: {str(e)}", level='ERROR')

    def delete_model(self, request, obj):
        try:
            obj.delete()
        except Exception as e:
            self.message_user(request, f"Error deleting user: {str(e)}", level='ERROR')

admin.site.register(AdminStaff, AdminStaffAdmin)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('surname', 'other_names', 'matric_number', 'department', 'level')
    list_filter = ('level', 'department')
    search_fields = ('surname', 'other_names', 'matric_number')
    fieldsets = (
        ('Basic Information', {
            'fields': ('surname', 'other_names', 'date_of_birth', 'level', 'department', 'matric_number', 'session', 'photo')
        }),
        ('Contact Information', {
            'fields': ('home_address', 'place_of_origin')
        }),
        ('Student Description', {
            'fields': ('skin_tone', 'weight', 'height', 'please_state_others')
        }),
        ('Parents/Guardian Information', {
            'fields': ('parent_surname', 'parent_other_names', 'parent_email', 'parent_phone')
        }),
        ('Health Information', {
            'fields': ('allergies', 'blood_group', 'genotype', 'if_more_stone')
        }),
        ('Achievements', {
            'fields': ('achievement_1', 'achievement_2', 'achievement_3', 'achievement_4', 'achievement_5', 'achievement_6', 'other_achievement_info')
        }),
        ('Images', {
            'fields': ('image_1', 'image_2', 'image_3', 'image_4', 'image_5', 'image_6')
        }),
    )