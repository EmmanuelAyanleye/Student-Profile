from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.utils import timezone

class AdminStaffManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('title', 'Mr')
        return self.create_user(email, password, **extra_fields)

class AdminStaff(AbstractUser):
    TITLE_CHOICES = [
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Miss', 'Miss'),
        ('Doctor', 'Doctor'),
        ('Amb', 'Ambassador'),
    ]
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]

    username = None
    email = models.EmailField(unique=True)
    title = models.CharField(max_length=10, choices=TITLE_CHOICES)
    role = models.CharField(max_length=5, choices=ROLE_CHOICES)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='adminstaff_set',
        help_text='The groups this user belongs to.'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='adminstaff_set',
        help_text='Specific permissions for this user.'
    )

    objects = AdminStaffManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['title', 'role']

    class Meta:
        swappable = 'AUTH_USER_MODEL'

    def save(self, *args, **kwargs):
        if self.role == 'admin':
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)


class Student(models.Model):
    LEVEL_CHOICES = [
        ('100', '100'),
        ('200', '200'),
        ('300', '300'),
        ('400', '400'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('SOCIOLOGY', 'SOCIOLOGY'),
        ('ECONOMICS', 'ECONOMICS'),
        ('POLITICAL SCIENCE', 'POLITICAL SCIENCE'),
        ('COMPUTER SCIENCE', 'COMPUTER SCIENCE'),
        ('MASS COMMUNICATION', 'MASS COMMUNICATION'),
        ('ACCOUNTING & FINANCE', 'ACCOUNTING & FINANCE'),
        ('PUBLIC ADMINISTRATION', 'PUBLIC ADMINISTRATION'),
        ('BUSSINESS ADMINSTRATION', 'BUSSINESS ADMINSTRATION'),
        ('HUMAN RESOURCE MANAGEMENT', 'HUMAN RESOURCE MANAGEMENT'),
        ('INTERNATIONAL RELATION & DIPLOMACY', 'INTERNATIONAL RELATION & DIPLOMACY'),
        ('ENVIRONMENTAL HEALTH MANAGEMENT', 'ENVIRONMENTAL HEALTH MANAGEMENT'),
        ('COMMUNITY HEALTH MANAGEMENT', 'COMMUNITY HEALTH MANAGEMENT'),
        ('NURSING', 'NURSING'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    surname = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100)
    date_of_birth = models.DateField(blank=True, null=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, blank=True)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, blank=True)
    matric_number = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255, blank=True)
    session = models.CharField(max_length=20, blank=True)
    home_address = models.CharField(max_length=255, blank=True)
    place_of_origin = models.CharField(max_length=100, blank=True)
    
    # Student Description
    skin_tone = models.CharField(max_length=50, blank=True)
    weight = models.CharField(max_length=50, blank=True)
    height = models.CharField(max_length=50, blank=True)
    please_state_others = models.TextField(blank=True)
    
    # Parents/Guardian Information
    parent_surname = models.CharField(max_length=100, blank=True)
    parent_other_names = models.CharField(max_length=100, blank=True)
    parent_email = models.EmailField(blank=True)
    parent_phone = models.CharField(max_length=20, blank=True)
    
    # Health Information
    allergies = models.CharField(max_length=255, blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    genotype = models.CharField(max_length=10, blank=True)
    if_more_stone = models.TextField(blank=True)
    
    # Achievements
    achievement_1 = models.FileField(upload_to='achievements/', blank=True, null=True)
    achievement_2 = models.FileField(upload_to='achievements/', blank=True, null=True)
    achievement_3 = models.FileField(upload_to='achievements/', blank=True, null=True)
    achievement_4 = models.FileField(upload_to='achievements/', blank=True, null=True)
    achievement_5 = models.FileField(upload_to='achievements/', blank=True, null=True)
    achievement_6 = models.FileField(upload_to='achievements/', blank=True, null=True)
    other_achievement_info = models.TextField(blank=True)
    
    # Images for more information
    image_1 = models.ImageField(upload_to='student_images/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='student_images/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='student_images/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='student_images/', blank=True, null=True)
    image_5 = models.ImageField(upload_to='student_images/', blank=True, null=True)
    image_6 = models.ImageField(upload_to='student_images/', blank=True, null=True)
    
    # Main photo
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.surname} {self.other_names}"
    
    class Meta:
        ordering = ['level', 'surname']

class StudentImage(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='student_images/')
    label = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.student.surname} - {self.label}"

    class Meta:
        verbose_name_plural = "Student Images"


class StudentAchievement(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='achievements')
    file = models.FileField(upload_to='student_achievements/')
    label = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Achievement - {self.label}"

    class Meta:
        verbose_name_plural = "Student Achievements"
