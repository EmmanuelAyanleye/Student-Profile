from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from .forms import AdminStaffForm, ModifyMemberForm, StudentSignupForm
from .models import AdminStaff, Student
from collections import defaultdict
from django.db.models import Q
from datetime import datetime

from .forms import StudentForm, StudentAchievementFormSet, StudentImageFormSet, StudentAchievementForm, StudentImageForm
from django.forms import modelformset_factory

from .models import StudentAchievement, StudentImage

from django.conf import settings
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.http import HttpResponse
from PIL import Image
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Add a custom decorator to check if user is admin
def admin_required(view_func):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "You must be logged in as an admin to access this page.")
            return redirect('login')
    return wrap

# Add a custom decorator to check if user is staff
def staff_required(view_func):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'staff':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "You must be logged in as a staff to access this page.")
            return redirect('login')
    return wrap

def home(request):
    return render(request, 'index.html')    

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if user.role == 'admin':
                    return redirect('dashboard')
                else:
                    return redirect('staff')
            else:
                messages.error(request, 'Invalid email or password')
                # Stay on admin form if login fails
                context = {
                    'active_form': 'admin'
                }
                return render(request, 'login.html', context)
        except Exception as e:
            messages.error(request, str(e))
            context = {
                'active_form': 'admin'
            }
            return render(request, 'login.html', context)
    
    # For GET request, show all messages by default on admin form
    context = {
        'active_form': 'admin'
    }
    return render(request, 'login.html', context)

def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('login')

def student_login(request):
    if request.method == 'POST':
        matric_number = request.POST.get('matric_number')
        password = request.POST.get('password')
        
        try:
            student = Student.objects.get(matric_number=matric_number, password=password)
            # Store student info in session
            request.session['student_id'] = student.id
            request.session['student_name'] = f"{student.surname} {student.other_names}"
            return redirect('student_dashboard')
        except Student.DoesNotExist:
            messages.error(request, 'Invalid matric number or password')
        except Exception as e:
            messages.error(request, str(e))
        
        # Stay on student form if login fails
        context = {
            'active_form': 'student'
        }
        return render(request, 'login.html', context)

def student_dashboard(request):
    if 'student_id' not in request.session:
        messages.error(request, "Please login first")
        return redirect('login')
    
    student = get_object_or_404(Student, id=request.session['student_id'])
    context = {
        'student': student,
    }
    return render(request, 'student_dashboard.html', context)

def student_profile_view(request):
    if 'student_id' not in request.session:
        messages.error(request, "Please login first")
        return redirect('login')
    
    student = get_object_or_404(Student, id=request.session['student_id'])
    context = {
        'student': student,
    }
    return render(request, 'student_profile_view.html', context)

def student_logout(request):
    if 'student_id' in request.session:
        del request.session['student_id']
    if 'student_name' in request.session:
        del request.session['student_name']
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('login')

def student_signup(request):
    if request.method == 'POST':
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"Registration successful! You have been registered with matric number {student.matric_number}. An admin will complete your profile soon.")
            return redirect('student_signup')
        else:
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = StudentSignupForm()
    
    context = {
        'form': form,
    }
    return render(request, 'student_signup.html', context)


@login_required
@admin_required
def dashboard(request):
    departments = [choice[0] for choice in Student.DEPARTMENT_CHOICES]

    context = {
        'user': request.user,
        'departments': departments,
    }
    return render(request, 'dashboard.html', context)

@login_required
@admin_required
def view_students(request):
    selected_dept = request.GET.get('department', None)
    students_by_level = {}
    levels = [100, 200, 300, 400]

    # Use all departments from the model choices
    departments = [choice[0] for choice in Student.DEPARTMENT_CHOICES]

    # Fetch students based on department filter
    if selected_dept:
        students = Student.objects.filter(department__iexact=selected_dept.replace('_', ' '))
    else:
        students = Student.objects.all()

    # Group students by level
    for level in levels:
        students_by_level[level] = students.filter(level=str(level)).order_by('surname')
    
    context = {
        'students_by_level': students_by_level,
        'levels': levels,
        'departments': departments,
        'selected_dept': selected_dept,
        'department_name': selected_dept.replace('_', ' ') if selected_dept else 'All Departments'
    }
    return render(request, 'view_student.html', context)

@login_required
@admin_required
def delete_student(request, id):
    student = get_object_or_404(Student, id=id)
    
    if request.method == 'POST':
        # Perform the deletion
        student.delete()
        return redirect('view_students') 
    
    return HttpResponse("Method not allowed", status=405)

@login_required
@admin_required
def student_details(request, id):
    student = get_object_or_404(Student, pk=id)
    
    context = {
        'student': student,
    }
    return render(request, 'student_details.html', context)

@login_required
@admin_required
def upload(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        achievement_formset = StudentAchievementFormSet(request.POST, request.FILES, queryset=StudentAchievement.objects.none())
        image_formset = StudentImageFormSet(request.POST, request.FILES, queryset=StudentImage.objects.none())

        if form.is_valid() and achievement_formset.is_valid() and image_formset.is_valid():
            # Save student
            student = form.save()
            
            # Save achievements
            for achievement_form in achievement_formset:
                if achievement_form.cleaned_data and achievement_form.cleaned_data.get('file'):
                    achievement = achievement_form.save(commit=False)
                    achievement.student = student
                    achievement.save()
            
            # Save images
            for image_form in image_formset:
                if image_form.cleaned_data and image_form.cleaned_data.get('image'):
                    image = image_form.save(commit=False)
                    image.student = student
                    image.save()
            
            messages.success(request, "Student information uploaded successfully!")
            return redirect('upload')
        else:
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = StudentForm()
        # Create formsets with 6 empty forms for new upload
        AchievementFormSet = modelformset_factory(StudentAchievement, form=StudentAchievementForm, extra=6, max_num=6, can_delete=False)
        ImageFormSet = modelformset_factory(StudentImage, form=StudentImageForm, extra=6, max_num=6, can_delete=False)
        
        achievement_formset = AchievementFormSet(queryset=StudentAchievement.objects.none())
        image_formset = ImageFormSet(queryset=StudentImage.objects.none())

    context = {
        'form': form,
        'achievement_formset': achievement_formset,
        'image_formset': image_formset,
    }
    return render(request, 'upload.html', context)

@login_required
@admin_required
def modify(request, id):
    student = get_object_or_404(Student, pk=id)
    
    # Get existing achievements and images count
    existing_achievements = student.achievements.all()
    existing_images = student.images.all()
    
    # Calculate extra forms needed to make total of 6
    achievement_extra = max(0, 6 - existing_achievements.count())
    image_extra = max(0, 6 - existing_images.count())
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        
        # Initialize formsets with proper queryset and extra
        AchievementFormSet = modelformset_factory(
            StudentAchievement, 
            form=StudentAchievementForm, 
            extra=achievement_extra, 
            max_num=6, 
            can_delete=True
        )
        
        ImageFormSet = modelformset_factory(
            StudentImage, 
            form=StudentImageForm, 
            extra=image_extra, 
            max_num=6, 
            can_delete=True
        )
        
        achievement_formset = AchievementFormSet(
            request.POST, 
            request.FILES, 
            queryset=existing_achievements,
            prefix='achievements'
        )
        
        image_formset = ImageFormSet(
            request.POST, 
            request.FILES, 
            queryset=existing_images,
            prefix='images'
        )

        if form.is_valid() and achievement_formset.is_valid() and image_formset.is_valid():
            student_instance = form.save(commit=False)
            
            # Handle password update if provided
            password = form.cleaned_data.get('password')
            if password:
                student_instance.password = password
            
            student_instance.save()
            
            # Save achievement formset
            achievements = achievement_formset.save(commit=False)
            for achievement in achievements:
                # Only save if file or label is provided
                if achievement.file or achievement.label:
                    achievement.student = student_instance
                    achievement.save()
                else:
                    # Delete if marked for deletion or empty
                    if achievement.pk and achievement_formset.can_delete:
                        achievement.delete()
            
            # Handle explicitly deleted achievements
            for achievement in achievement_formset.deleted_objects:
                achievement.delete()
            
            # Save image formset
            images = image_formset.save(commit=False)
            for image in images:
                # Only save if image or label is provided
                if image.image or image.label:
                    image.student = student_instance
                    image.save()
                else:
                    # Delete if marked for deletion or empty
                    if image.pk and image_formset.can_delete:
                        image.delete()
            
            # Handle explicitly deleted images
            for image in image_formset.deleted_objects:
                image.delete()
            
            messages.success(request, "Student information updated successfully.")
            return redirect('modify', id=student.id)
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            # Display formset errors
            for i, achievement_form in enumerate(achievement_formset.forms):
                if achievement_form.errors:
                    for field, errors in achievement_form.errors.items():
                        if field not in ['DELETE', 'id']:
                            for error in errors:
                                messages.error(request, f"Achievement {i+1} - {field}: {error}")
            
            for i, image_form in enumerate(image_formset.forms):
                if image_form.errors:
                    for field, errors in image_form.errors.items():
                        if field not in ['DELETE', 'id']:
                            for error in errors:
                                messages.error(request, f"Image {i+1} - {field}: {error}")
    else:
        form = StudentForm(instance=student)
        
        # Initialize formsets for GET request
        AchievementFormSet = modelformset_factory(
            StudentAchievement, 
            form=StudentAchievementForm, 
            extra=achievement_extra, 
            max_num=6, 
            can_delete=True
        )
        
        ImageFormSet = modelformset_factory(
            StudentImage, 
            form=StudentImageForm, 
            extra=image_extra, 
            max_num=6, 
            can_delete=True
        )
        
        achievement_formset = AchievementFormSet(
            queryset=existing_achievements,
            prefix='achievements'
        )
        
        image_formset = ImageFormSet(
            queryset=existing_images,
            prefix='images'
        )
    
    context = {
        'form': form,
        'student': student,
        'achievement_formset': achievement_formset,
        'image_formset': image_formset,
    }
    return render(request, 'modify.html', context)


@login_required
@admin_required
def upload_admin(request):
    if request.method == 'POST':
        form = AdminStaffForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.username = form.cleaned_data['email']
                if form.cleaned_data['role'] == 'admin':
                    user.is_staff = True  # Give admin access to Django admin site
                user.save()
                messages.success(request, f"{user.get_role_display()} added successfully!")
                return redirect('upload_admin')
            except Exception as e:
                messages.error(request, str(e))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AdminStaffForm()
    
    return render(request, 'add-admin.html', {'form': form})

@login_required
@admin_required
def modify_admin(request, id):
    admin_or_staff = get_object_or_404(AdminStaff, id=id)
    
    if request.method == 'POST':
        # Update the admin/staff details with the new data from the form
        title = request.POST.get('title')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')  # Optional, can be updated if provided
        role = request.POST.get('role')

        # Update the fields
        admin_or_staff.title = title
        admin_or_staff.first_name = first_name
        admin_or_staff.last_name = last_name
        admin_or_staff.email = email
        if password:
            admin_or_staff.set_password(password)  # Only set password if provided
        admin_or_staff.role = role
        
        # Save the updated object
        admin_or_staff.save()
        
        messages.success(request, 'Admin/Staff details updated successfully!')
        return redirect('modify_admin', id=admin_or_staff.id)

    # Render the page with the current data if GET request
    context = {
        'admin_or_staff': admin_or_staff,
    }
    return render(request, 'modify-admin.html', context)

@login_required
@admin_required
def view_admin(request):
    departments = [choice[0] for choice in Student.DEPARTMENT_CHOICES]
    admins = AdminStaff.objects.filter(role='admin')
    staff = AdminStaff.objects.filter(role='staff')
    
    context = {
        'admins': admins,
        'staff': staff,
        'departments': departments,
    }
    return render(request, 'view-admin.html', context)

@login_required
@admin_required
def admin_details(request, id):
    # Fetch specific admin or staff member by ID
    admin_or_staff = get_object_or_404(AdminStaff, id=id)
    
    context = {
        'admin_or_staff': admin_or_staff,
    }
    
    return render(request, 'admin-details.html', context)

@login_required
@admin_required
def delete_admin_or_staff(request, id):
    # Fetch the admin or staff member by ID
    admin_or_staff = get_object_or_404(AdminStaff, id=id)
    
    if request.method == 'POST':
        # Perform the deletion
        admin_or_staff.delete()
        return redirect('view_admin')  # Redirect to the list page or a success page
    
    return HttpResponse("Method not allowed", status=405)

@login_required
@staff_required
def staff(request):
    departments = [
        'SOCIOLOGY', 'ECONOMICS', 'POLITICAL SCIENCE', 'COMPUTER SCIENCE',
        'MASS COMMUNICATION', 'ACCOUNTING & FINANCE', 'PUBLIC ADMINISTRATION',
        'BUSSINESS ADMINSTRATION', 'HUMAN RESOURCE MANAGEMENT',
        'INTERNATIONAL RELATION & DIPLOMACY', 'ENVIRONMENTAL HEALTH MANAGEMENT',
        'COMMUNITY HEALTH MANAGEMENT', 'NURSING'
    ]
    context = {
        'user': request.user,
        'departments': departments
    }
    return render(request, 'staff.html', context)

@login_required
@staff_required
def staff_view_students(request):
    selected_dept = request.GET.get('department')
    
    students_by_level = {}
    levels = [100, 200, 300, 400]
    
    for level in levels:
        # Build the query
        query = Q(level=str(level))
        if selected_dept:
            # Make the department search case-insensitive
            query &= Q(department__iexact=selected_dept)
        
        # Get students for this level and department
        students = Student.objects.filter(query).order_by('surname')
        students_by_level[level] = students

    context = {
        'levels': levels,
        'students_by_level': students_by_level,
        'selected_dept': selected_dept,
        'departments': [
            'SOCIOLOGY', 'ECONOMICS', 'POLITICAL SCIENCE', 'COMPUTER SCIENCE',
            'MASS COMMUNICATION', 'ACCOUNTING & FINANCE', 'PUBLIC ADMINISTRATION',
            'BUSSINESS ADMINSTRATION', 'HUMAN RESOURCE MANAGEMENT',
            'INTERNATIONAL RELATION & DIPLOMACY', 'ENVIRONMENTAL HEALTH MANAGEMENT',
            'COMMUNITY HEALTH MANAGEMENT', 'NURSING'
        ]
    }
    
    return render(request, 'staff-view-students.html', context)

@login_required
@staff_required
def staff_student_details(request, id):
    student = get_object_or_404(Student, pk=id)
    context = {
        'student': student,
    }
    return render(request, 'staff-student-details.html', context)

@login_required
@staff_required
def staff_search_students(request):
    search_term = request.GET.get('term', '')
    if search_term:
        # Enhanced search query
        students = Student.objects.filter(
            Q(surname__icontains=search_term) |
            Q(other_names__icontains=search_term) |
            Q(matric_number__icontains=search_term) |
            Q(department__icontains=search_term) |
            Q(level__icontains=search_term)  # Added level search
        ).order_by('level', 'surname')

        students_by_level = {}
        levels = [100, 200, 300, 400]
        
        for level in levels:
            students_by_level[level] = students.filter(level=str(level))

        context = {
            'levels': levels,
            'students_by_level': students_by_level,
            'is_search': True,
            'search_term': search_term,
            'departments': [
                'SOCIOLOGY', 'ECONOMICS', 'POLITICAL SCIENCE', 'COMPUTER SCIENCE',
                'MASS COMMUNICATION', 'ACCOUNTING & FINANCE', 'PUBLIC ADMINISTRATION',
                'BUSSINESS ADMINSTRATION', 'HUMAN RESOURCE MANAGEMENT',
                'INTERNATIONAL RELATION & DIPLOMACY', 'ENVIRONMENTAL HEALTH MANAGEMENT',
                'COMMUNITY HEALTH MANAGEMENT', 'NURSING'
            ]
        }
        return render(request, 'staff-view-students.html', context)
    
    return redirect('staff_view_students')

@login_required
@staff_required
def profile(request):
    context = {
        'user': request.user
    }
    return render(request, 'profile.html', context)

@login_required
@permission_required('student_profile.can_modify_members', raise_exception=True)
def modify_member(request, member_id):
    member = get_object_or_404(AdminStaff, id=member_id)
    if request.method == 'POST':
        form = ModifyMemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member details updated successfully!')
            return redirect('view_admin')
    else:
        form = ModifyMemberForm(instance=member)
    
    return render(request, 'modify_member.html', {'form': form, 'member': member})

def search_students(request):
    departments = [choice[0] for choice in Student.DEPARTMENT_CHOICES]
    term = request.GET.get('term', '')
    if not term:
        return redirect('view_students')
    
    # Get all students matching the search term
    students = Student.objects.filter(
        Q(surname__icontains=term) |
        Q(other_names__icontains=term) |
        Q(matric_number__icontains=term) |
        Q(department__icontains=term) |
        Q(level__icontains=term)
    ).order_by('level', 'surname')
    
    # Group students by level as in view_students
    students_by_level = {}
    levels = [100, 200, 300, 400]
    
    for level in levels:
        students_by_level[level] = students.filter(level=str(level))
    
    context = {
        'students_by_level': students_by_level,
        'levels': levels,
        'search_term': term,
        'departments': departments,
        'is_search': True
    }
    
    return render(request, 'view_student.html', context)

def export_student_pdf(request, id):
    # Get student
    student = get_object_or_404(Student, pk=id)
    
    # Create response object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.surname} {student.other_names} details.pdf"'
    
    # Create PDF object
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Add logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Espam Logo.png')
    if os.path.exists(logo_path):
        p.drawImage(logo_path, width/2 - 50, height - 150, width=100, height=100)
    
    # Add header text
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height - 180, "ESPAM FORMATION UNIVERSITY")
    
    p.setFont("Helvetica", 9)
    p.drawCentredString(width/2, height - 200, "Address: Sacouba Anavie Campus, Porto-Novo, Republic of Benin.")
    p.drawCentredString(width/2, height - 215, "Phone: +22946436904, +2348035637035, +22956885802")
    p.drawCentredString(width/2, height - 230, "Email: espamformationunicampus2@gmail.com")
    
    # Add title
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width/2, height - 260, "STUDENT PROFILE REPORT")
    
    # Draw line under title
    p.line(50, height - 270, width - 50, height - 270)
    
    # Initialize y position (start below header)
    y_pos = height - 300
    
    # Add student photo at the top right
    if student.photo:
        try:
            # Try to get the absolute file path
            if hasattr(student.photo, 'path'):
                photo_path = student.photo.path
            else:
                # If path attribute doesn't work, try constructing it
                photo_path = os.path.join(settings.MEDIA_ROOT, str(student.photo))
            
            # Check if file exists before drawing
            if os.path.exists(photo_path):
                p.drawImage(photo_path, width - 150, y_pos - 80, width=100, height=100)
        except Exception as e:
            # Silently skip if photo can't be loaded
            pass
    
    # Add student details in sections (on the left, avoiding photo area)
    p.setFont("Helvetica-Bold", 11)
    
    # Basic Information
    p.drawString(50, y_pos, "BASIC INFORMATION")
    p.setFont("Helvetica", 9)
    details = [
        f"Surname: {student.surname}",
        f"Other Names: {student.other_names}",
        f"Matric Number: {student.matric_number}",
        f"Date of Birth: {student.date_of_birth}",
        f"Level: {student.level}",
        f"Department: {student.department}",
        f"Session: {student.session}",
        f"Home Address: {student.home_address or 'N/A'}",
        f"Place of Origin: {student.place_of_origin or 'N/A'}",
    ]
    
    y_pos -= 20
    for detail in details:
        p.drawString(60, y_pos, detail)
        y_pos -= 12
    
    # Student's Description
    y_pos -= 10
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y_pos, "STUDENT'S DESCRIPTION")
    p.setFont("Helvetica", 9)
    y_pos -= 15
    
    description_details = [
        f"Skin Tone: {student.skin_tone or 'N/A'}",
        f"Weight: {student.weight or 'N/A'}",
        f"Height: {student.height or 'N/A'}",
        f"Other Information: {student.please_state_others or 'N/A'}",
    ]
    
    for detail in description_details:
        p.drawString(60, y_pos, detail)
        y_pos -= 12
    
    # Parents/Guardian Information
    y_pos -= 10
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y_pos, "PARENTS/GUARDIAN INFORMATION")
    p.setFont("Helvetica", 9)
    y_pos -= 15
    
    parent_details = [
        f"Parent Surname: {student.parent_surname or 'N/A'}",
        f"Parent Other Names: {student.parent_other_names or 'N/A'}",
        f"Parent Email: {student.parent_email or 'N/A'}",
        f"Parent Phone: {student.parent_phone or 'N/A'}",
    ]
    
    for detail in parent_details:
        p.drawString(60, y_pos, detail)
        y_pos -= 12
    
    # Health Information
    y_pos -= 10
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y_pos, "HEALTH INFORMATION")
    p.setFont("Helvetica", 9)
    y_pos -= 15
    
    health_details = [
        f"Allergies: {student.allergies or 'N/A'}",
        f"Blood Group: {student.blood_group or 'N/A'}",
        f"Genotype: {student.genotype or 'N/A'}",
        f"Other Health Info: {student.if_more_stone or 'N/A'}",
    ]
    
    for detail in health_details:
        p.drawString(60, y_pos, detail)
        y_pos -= 12
    
    # Achievements
    y_pos -= 15
    if y_pos < 150:
        p.showPage()
        y_pos = height - 50
    
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y_pos, "ACHIEVEMENTS")
    p.setFont("Helvetica", 9)
    y_pos -= 15
    
    achievements = student.achievements.all()
    if achievements:
        for achievement in achievements:
            filename = achievement.file.name.split('/')[-1] if achievement.file else 'No file'
            achievement_text = f"• {achievement.label}: {filename}"
            p.drawString(60, y_pos, achievement_text)
            y_pos -= 12
    else:
        p.drawString(60, y_pos, "No achievements uploaded")
        y_pos -= 12
    
    if student.other_achievement_info:
        p.drawString(60, y_pos, f"Other Achievement Info: {student.other_achievement_info}")
        y_pos -= 12
    
    # Images Section - starts on new page to avoid overlap
    images = student.images.all()
    if images:
        p.showPage()
        y_pos = height - 50
        
        p.setFont("Helvetica-Bold", 11)
        p.drawString(50, y_pos, "IMAGES FOR MORE INFORMATION")
        p.setFont("Helvetica", 9)
        y_pos -= 20
        
        for image in images:
            if image.image:
                try:
                    # Try to get the absolute file path
                    if hasattr(image.image, 'path'):
                        img_path = image.image.path
                    else:
                        # If path attribute doesn't work, try constructing it
                        img_path = os.path.join(settings.MEDIA_ROOT, str(image.image))
                    
                    if os.path.exists(img_path):
                        # Check if there's enough space for image
                        if y_pos < 150:
                            p.showPage()
                            y_pos = height - 50
                        
                        # Draw image label
                        label = image.label or image.image.name.split('/')[-1]
                        p.drawString(50, y_pos, f"Image: {label}")
                        y_pos -= 20
                        
                        # Draw the image
                        p.drawImage(img_path, 50, y_pos - 120, width=150, height=150)
                        y_pos -= 170
                except Exception as e:
                    pass
    
    # Add footer with standard Helvetica font
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, 30, "All rights reserved by ESPAM FORMATION UNIVERSITY.")
    p.drawCentredString(width/2, 15, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Save PDF
    p.showPage()
    p.save()
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

def export_students_pdf(request):
    # Get selected student IDs from query parameter
    student_ids = request.GET.get('ids', '').split(',')
    students = Student.objects.filter(id__in=student_ids).order_by('level', 'surname')

    if not students:
        return HttpResponse("No students selected", status=400)

    # Create response object
    if len(students) == 1:
        student = students.first()
        filename = f"{student.surname} {student.other_names} details.pdf"
    else:
        filename = "selected_students.pdf"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Create PDF object
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Add logo and header
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Espam Logo.png')
    if os.path.exists(logo_path):
        p.drawImage(logo_path, width/2 - 50, height - 150, width=100, height=100)

    # Add header text
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height - 180, "ESPAM FORMATION UNIVERSITY")

    p.setFont("Helvetica", 10)
    p.drawCentredString(width/2, height - 200, "Address: Sacouba Anavie Campus, Porto-Novo, Republic of Benin.")
    p.drawCentredString(width/2, height - 220, "Phone: +22946436904, +2348035637035, +22956885802")
    p.drawCentredString(width/2, height - 240, "Email: espamformationunicampus2@gmail.com")

    # Add title
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width/2, height - 280, "STUDENT PROFILES REPORT")

    # Initialize starting position
    y_position = height - 320

    # Loop through each student
    for student in students:
        if y_position < 150:
            p.showPage()
            y_position = height - 100

        if y_position < height - 320:
            p.line(50, y_position + 30, width - 50, y_position + 30)
            y_position -= 20

        if student.photo:
            try:
                photo_path = student.photo.path
                p.drawImage(photo_path, 50, y_position - 100, width=100, height=100)
            except:
                pass

        p.setFont("Helvetica-Bold", 12)
        details = [
            f"Surname: {student.surname}",
            f"Other Names: {student.other_names}",
            f"Matric Number: {student.matric_number}",
            f"Date of Birth: {student.date_of_birth}",
            f"Level: {student.level}",
            f"Department: {student.department}"
        ]

        for i, detail in enumerate(details):
            p.drawString(200, y_position - (i * 20), detail)

        y_position -= 150

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

@login_required
def filter_student(request, id):
    student = get_object_or_404(Student, pk=id)
    return render(request, 'filter_student.html', {'student': student})

def export_filtered_pdf(request, id):
    student = get_object_or_404(Student, pk=id)
    selected_fields = request.GET.get('fields', '').split(',')
    selected_fields = [f.strip() for f in selected_fields if f.strip()]
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.surname} {student.other_names} filtered details.pdf"'
    
    # Create PDF object
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Add header
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Espam Logo.png')
    if os.path.exists(logo_path):
        p.drawImage(logo_path, width/2 - 50, height - 150, width=100, height=100)
    
    # Add header text
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height - 180, "ESPAM FORMATION UNIVERSITY")
    
    p.setFont("Helvetica", 10)
    p.drawCentredString(width/2, height - 200, "Address: Sacouba Anavie Campus, Porto-Novo, Republic of Benin.")
    p.drawCentredString(width/2, height - 220, "Phone: +22946436904, +2348035637035, +22956885802")
    p.drawCentredString(width/2, height - 240, "Email: espamformationunicampus2@gmail.com")
    
    # Draw line under header
    p.line(50, height - 290, width - 50, height - 290)
    
    # Add title
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width/2, height - 280, "STUDENT PROFILE REPORT")
    
    # Initialize y position
    y_pos = height - 320
    
    # Add student photo if selected
    if 'photo' in selected_fields and student.photo:
        try:
            # Try to get the absolute file path
            if hasattr(student.photo, 'path'):
                photo_path = student.photo.path
            else:
                # If path attribute doesn't work, try constructing it
                photo_path = os.path.join(settings.MEDIA_ROOT, str(student.photo))
            
            # Check if file exists before drawing
            if os.path.exists(photo_path):
                p.drawImage(photo_path, 50, y_pos - 80, width=80, height=80)
                y_pos -= 100
        except:
            pass
    
    # Define all field mappings
    basic_info_fields = {
        'surname': ('Surname', student.surname),
        'other_names': ('Other Names', student.other_names),
        'date_of_birth': ('Date of Birth', student.date_of_birth),
        'level': ('Level', student.level),
        'department': ('Department', student.department),
        'matric_number': ('Matric Number', student.matric_number),
        'session': ('Session', student.session),
        'home_address': ('Home Address', student.home_address or 'N/A'),
        'place_of_origin': ('Place of Origin', student.place_of_origin or 'N/A'),
    }
    
    description_fields = {
        'skin_tone': ('Skin Tone', student.skin_tone or 'N/A'),
        'weight': ('Weight', student.weight or 'N/A'),
        'height': ('Height', student.height or 'N/A'),
        'please_state_others': ('Other Information', student.please_state_others or 'N/A'),
    }
    
    parent_fields = {
        'parent_surname': ('Parent Surname', student.parent_surname or 'N/A'),
        'parent_other_names': ('Parent Other Names', student.parent_other_names or 'N/A'),
        'parent_email': ('Parent Email', student.parent_email or 'N/A'),
        'parent_phone': ('Parent Phone', student.parent_phone or 'N/A'),
    }
    
    health_fields = {
        'allergies': ('Allergies', student.allergies or 'N/A'),
        'blood_group': ('Blood Group', student.blood_group or 'N/A'),
        'genotype': ('Genotype', student.genotype or 'N/A'),
        'if_more_stone': ('Other Health Info', student.if_more_stone or 'N/A'),
    }
    
    # Add Basic Information Section
    basic_fields_to_show = [f for f in selected_fields if f in basic_info_fields]
    if basic_fields_to_show:
        if y_pos < 150:
            p.showPage()
            y_pos = height - 50
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "BASIC INFORMATION")
        y_pos -= 20
        
        p.setFont("Helvetica", 10)
        for field in basic_fields_to_show:
            if field in basic_info_fields:
                label, value = basic_info_fields[field]
                p.drawString(50, y_pos, f"{label}: {value}")
                y_pos -= 15
        
        y_pos -= 10
    
    # Add Description Section
    description_fields_to_show = [f for f in selected_fields if f in description_fields]
    if description_fields_to_show:
        if y_pos < 150:
            p.showPage()
            y_pos = height - 50
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "STUDENT'S DESCRIPTION")
        y_pos -= 20
        
        p.setFont("Helvetica", 10)
        for field in description_fields_to_show:
            if field in description_fields:
                label, value = description_fields[field]
                p.drawString(50, y_pos, f"{label}: {value}")
                y_pos -= 15
        
        y_pos -= 10
    
    # Add Parent Information Section
    parent_fields_to_show = [f for f in selected_fields if f in parent_fields]
    if parent_fields_to_show:
        if y_pos < 150:
            p.showPage()
            y_pos = height - 50
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "PARENTS/GUARDIAN INFORMATION")
        y_pos -= 20
        
        p.setFont("Helvetica", 10)
        for field in parent_fields_to_show:
            if field in parent_fields:
                label, value = parent_fields[field]
                p.drawString(50, y_pos, f"{label}: {value}")
                y_pos -= 15
        
        y_pos -= 10
    
    # Add Health Information Section
    health_fields_to_show = [f for f in selected_fields if f in health_fields]
    if health_fields_to_show:
        if y_pos < 150:
            p.showPage()
            y_pos = height - 50
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "HEALTH INFORMATION")
        y_pos -= 20
        
        p.setFont("Helvetica", 10)
        for field in health_fields_to_show:
            if field in health_fields:
                label, value = health_fields[field]
                p.drawString(50, y_pos, f"{label}: {value}")
                y_pos -= 15
        
        y_pos -= 10
    
    # Add Achievements
    if 'other_achievement_info' in selected_fields:
        if y_pos < 150:
            p.showPage()
            y_pos = height - 50
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "ACHIEVEMENTS")
        y_pos -= 20
        
        p.setFont("Helvetica", 10)
        if student.other_achievement_info:
            p.drawString(50, y_pos, f"Notes: {student.other_achievement_info}")
            y_pos -= 15
        else:
            p.drawString(50, y_pos, "No additional achievement information")
            y_pos -= 15
        
        y_pos -= 10
    
    # Add Images Section if selected
    selected_image_ids = [f.replace('image_', '') for f in selected_fields if f.startswith('image_')]
    if selected_image_ids:
        if y_pos < 150:
            p.showPage()
            y_pos = height - 50
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "IMAGES FOR MORE INFORMATION")
        p.setFont("Helvetica", 10)
        y_pos -= 20
        
        for image in student.images.filter(id__in=selected_image_ids):
            if y_pos < 150:
                p.showPage()
                y_pos = height - 50
            
            try:
                # Try to get the absolute file path
                if hasattr(image.image, 'path'):
                    img_path = image.image.path
                else:
                    # If path attribute doesn't work, try constructing it
                    img_path = os.path.join(settings.MEDIA_ROOT, str(image.image))
                
                label = image.label or image.image.name.split('/')[-1]
                p.drawString(50, y_pos, f"Image: {label}")
                y_pos -= 20
                
                if os.path.exists(img_path):
                    p.drawImage(img_path, 50, y_pos - 120, width=150, height=150)
                    y_pos -= 170
            except Exception as e:
                pass
        
        y_pos -= 10
    
    # Add footer
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, 30, "All rights reserved by ESPAM FORMATION UNIVERSITY.")
    p.drawCentredString(width/2, 15, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Save PDF
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response