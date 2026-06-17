
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import pdfplumber

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from internships.models import (
    Application,
    InternshipOpportunity
)

from matching.views import calculate_match_score

from .forms import (
    StudentProfileForm,
    AcademicQualificationForm,
    WorkExperienceForm,
    RefereeForm
)

from .models import (
    StudentProfile,
    AcademicQualification,
    WorkExperience,
    Referee
)


TECH_SKILLS = [

    'python',
    'django',
    'flask',
    'javascript',
    'react',
    'html',
    'css',
    'bootstrap',
    'sql',
    'mysql',
    'postgresql',
    'sqlite',
    'git',
    'github',
    'linux',
    'windows',
    'networking',
    'cybersecurity',
    'java',
    'c',
    'c++',
    'php',
    'laravel',
    'api',
    'rest api',
    'machine learning',
    'ai',
    'data analysis',
    'excel',
    'power bi',
    'figma',
    'ui/ux',
]


def extract_skills_from_cv(cv_path):

    extracted = set()

    try:

        full_text = ''

        with pdfplumber.open(cv_path) as pdf:

            for page in pdf.pages:

                text = page.extract_text()

                if text:
                    full_text += text.lower() + ' '

        for skill in TECH_SKILLS:

            if skill.lower() in full_text:
                extracted.add(skill)

    except Exception as error:

        print("CV Extraction Error:", error)

    return ', '.join(sorted(extracted))


@login_required
def create_student_profile(request):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile:
        return redirect('student_profile')

    if request.method == 'POST':

        form = StudentProfileForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            student_profile = form.save(commit=False)
            student_profile.user = request.user
            student_profile.save()

            if student_profile.cv:

                extracted_skills = extract_skills_from_cv(
                    student_profile.cv.path
                )

                student_profile.extracted_skills = extracted_skills
                student_profile.save()

            messages.success(
                request,
                'Profile created successfully.'
            )

            return redirect('student_dashboard')

    else:

        form = StudentProfileForm()

    return render(
        request,
        'students/create_profile.html',
        {
            'form': form
        }
    )


@login_required
def edit_student_profile(request):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    if request.method == 'POST':

        form = StudentProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():

            student_profile = form.save()

            if student_profile.cv:

                extracted_skills = extract_skills_from_cv(
                    student_profile.cv.path
                )

                student_profile.extracted_skills = extracted_skills
                student_profile.save()

            messages.success(
                request,
                'Profile updated successfully.'
            )

            return redirect('student_dashboard')

    else:

        form = StudentProfileForm(
            instance=profile
        )

    return render(
        request,
        'students/edit_profile.html',
        {
            'form': form
        }
    )


@login_required
def student_profile(request):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    return redirect('student_dashboard')


@login_required
def add_academic_qualification(request):

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if student is None:
        return redirect('create_student_profile')

    if request.method == 'POST':

        form = AcademicQualificationForm(
            request.POST
        )

        if form.is_valid():

            qualification = form.save(
                commit=False
            )

            qualification.student = student
            qualification.save()

            messages.success(
                request,
                'Academic qualification added successfully.'
            )

            return redirect('student_dashboard')

    else:

        form = AcademicQualificationForm()

    return render(
        request,
        'students/add_academic_qualification.html',
        {
            'form': form,
            'title': 'Add Academic Qualification',
            'submit_label': 'Save Qualification',
        }
    )


@login_required
def edit_qualification(request, qualification_id):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    qualification = get_object_or_404(
        AcademicQualification,
        id=qualification_id,
        student=profile
    )

    if request.method == 'POST':

        form = AcademicQualificationForm(
            request.POST,
            instance=qualification
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Academic qualification updated successfully.'
            )

            return redirect('student_dashboard')

    else:
        form = AcademicQualificationForm(instance=qualification)

    return render(
        request,
        'students/add_academic_qualification.html',
        {
            'form': form,
            'title': 'Edit Academic Qualification',
            'submit_label': 'Update Qualification',
        }
    )


@login_required
def delete_qualification(request, qualification_id):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    qualification = get_object_or_404(
        AcademicQualification,
        id=qualification_id,
        student=profile
    )

    qualification.delete()

    messages.success(
        request,
        'Academic qualification deleted successfully.'
    )

    return redirect('student_dashboard')


@login_required
def add_work_experience(request):

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if student is None:
        return redirect('create_student_profile')

    if request.method == 'POST':

        form = WorkExperienceForm(
            request.POST
        )

        if form.is_valid():

            experience = form.save(
                commit=False
            )

            experience.student = student
            experience.save()

            messages.success(
                request,
                'Work experience added successfully.'
            )

            return redirect('student_dashboard')

    else:

        form = WorkExperienceForm()

    return render(
        request,
        'students/add_work_experience.html',
        {
            'form': form,
            'title': 'Add Work Experience',
            'submit_label': 'Save Experience',
        }
    )


@login_required
def edit_work(request, work_id):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    experience = get_object_or_404(
        WorkExperience,
        id=work_id,
        student=profile
    )

    if request.method == 'POST':

        form = WorkExperienceForm(
            request.POST,
            instance=experience
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Work experience updated successfully.'
            )

            return redirect('student_dashboard')

    else:
        form = WorkExperienceForm(instance=experience)

    return render(
        request,
        'students/add_work_experience.html',
        {
            'form': form,
            'title': 'Edit Work Experience',
            'submit_label': 'Update Experience',
        }
    )


@login_required
def delete_work(request, work_id):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    experience = get_object_or_404(
        WorkExperience,
        id=work_id,
        student=profile
    )

    experience.delete()

    messages.success(
        request,
        'Work experience deleted successfully.'
    )

    return redirect('student_dashboard')


@login_required
def add_referee(request):

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if student is None:
        return redirect('create_student_profile')

    if request.method == 'POST':

        form = RefereeForm(
            request.POST
        )

        if form.is_valid():

            referee = form.save(
                commit=False
            )

            referee.student = student
            referee.save()

            messages.success(
                request,
                'Referee added successfully.'
            )

            return redirect('student_dashboard')

    else:

        form = RefereeForm()

    return render(
        request,
        'students/add_referee.html',
        {
            'form': form,
            'title': 'Add Referee',
            'submit_label': 'Save Referee',
        }
    )


@login_required
def edit_referee(request, referee_id):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    referee = get_object_or_404(
        Referee,
        id=referee_id,
        student=profile
    )

    if request.method == 'POST':

        form = RefereeForm(
            request.POST,
            instance=referee
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Referee updated successfully.'
            )

            return redirect('student_dashboard')

    else:
        form = RefereeForm(instance=referee)

    return render(
        request,
        'students/add_referee.html',
        {
            'form': form,
            'title': 'Edit Referee',
            'submit_label': 'Update Referee',
        }
    )


@login_required
def delete_referee(request, referee_id):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    referee = get_object_or_404(
        Referee,
        id=referee_id,
        student=profile
    )

    referee.delete()

    messages.success(
        request,
        'Referee deleted successfully.'
    )

    return redirect('student_dashboard')


@login_required
def student_dashboard(request):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    applications = Application.objects.filter(
        student=profile
    ).order_by('-applied_at')

    total_applications = applications.count()

    shortlisted_count = applications.filter(
        status='shortlisted'
    ).count()

    interview_count = applications.filter(
        status='interview_scheduled'
    ).count()

    accepted_count = applications.filter(
        status='accepted'
    ).count()

    rejected_count = applications.filter(
        status='rejected'
    ).count()

    profile_completion = profile.get_profile_completion()
    missing_profile_items = profile.get_missing_profile_items()

    opportunities = InternshipOpportunity.objects.filter(
        status='open'
    )

    recommended_opportunities = []

    for opportunity in opportunities:

        score, analysis = calculate_match_score(
            profile,
            opportunity
        )

        recommended_opportunities.append({
            'opportunity': opportunity,
            'score': score,
            'matched_skills': analysis.get('matched_skills', []),
        })

    recommended_opportunities.sort(
        key=lambda item: item['score'],
        reverse=True
    )

    upcoming_interviews = applications.filter(
        status='interview_scheduled'
    ).order_by('interview_date')[:5]

    recent_applications = applications[:5]

    qualifications = AcademicQualification.objects.filter(
        student=profile
    ).order_by('-end_year')

    work_experiences = WorkExperience.objects.filter(
        student=profile
    ).order_by('-start_date')

    referees = Referee.objects.filter(
        student=profile
    ).order_by('-created_at')

    return render(
        request,
        'students/student_dashboard.html',
        {
            'profile': profile,

            'total_applications': total_applications,
            'shortlisted_count': shortlisted_count,
            'interview_count': interview_count,
            'accepted_count': accepted_count,
            'rejected_count': rejected_count,

            'profile_completion': profile_completion,
            'missing_profile_items': missing_profile_items,

            'recommended_opportunities': recommended_opportunities[:5],
            'upcoming_interviews': upcoming_interviews,
            'recent_applications': recent_applications,
            'qualifications': qualifications,
            'work_experiences': work_experiences,
            'referees': referees,
        }
    )

@login_required
def generate_resume_pdf(request):

    profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('create_student_profile')

    academic_qualifications = profile.academic_qualifications.all()
    work_experiences = profile.work_experiences.all()
    referees = profile.referees.all()

    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = (
        f'attachment; filename="{profile.full_name}_resume.pdf"'
    )

    pdf = canvas.Canvas(response, pagesize=A4)

    width, height = A4
    y = height - 60

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(50, y, profile.full_name or profile.user.username)

    y -= 25

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        50,
        y,
        f"{profile.phone_number} | {profile.location} | {profile.user.email}"
    )

    y -= 20

    if profile.github:
        pdf.drawString(50, y, f"GitHub: {profile.github}")
        y -= 15

    if profile.linkedin:
        pdf.drawString(50, y, f"LinkedIn: {profile.linkedin}")
        y -= 15

    if profile.portfolio:
        pdf.drawString(50, y, f"Portfolio: {profile.portfolio}")
        y -= 15

    y -= 15

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Professional Summary")

    y -= 20

    pdf.setFont("Helvetica", 10)

    summary = profile.bio or "No professional summary provided."

    for line in summary.splitlines():
        pdf.drawString(50, y, line[:95])
        y -= 15

    y -= 10

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Skills")

    y -= 20

    pdf.setFont("Helvetica", 10)
    skills = profile.skills or profile.extracted_skills or "No skills provided."
    pdf.drawString(50, y, skills[:110])

    y -= 30

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Education")

    y -= 20

    pdf.setFont("Helvetica", 10)

    if academic_qualifications:

        for item in academic_qualifications:

            pdf.drawString(
                50,
                y,
                f"{item.qualification} - {item.institution_name}"
            )
            y -= 15

            pdf.drawString(
                50,
                y,
                f"{item.course_name} | {item.grade} | {item.start_year} - {item.end_year}"
            )
            y -= 20

    else:

        pdf.drawString(
            50,
            y,
            f"{profile.course} - {profile.institution}"
        )
        y -= 20

    y -= 10

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Work Experience")

    y -= 20

    pdf.setFont("Helvetica", 10)

    if work_experiences:

        for item in work_experiences:

            pdf.drawString(
                50,
                y,
                f"{item.position} - {item.organization}"
            )
            y -= 15

            pdf.drawString(
                50,
                y,
                f"{item.start_date} - {item.end_date}"
            )
            y -= 15

            pdf.drawString(
                50,
                y,
                item.responsibilities[:110]
            )
            y -= 25

    else:

        pdf.drawString(50, y, "No work experience added.")
        y -= 20

    y -= 10

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Referees")

    y -= 20

    pdf.setFont("Helvetica", 10)

    if referees:

        for item in referees:

            pdf.drawString(
                50,
                y,
                f"{item.full_name} - {item.position}, {item.organization}"
            )
            y -= 15

            pdf.drawString(
                50,
                y,
                f"{item.phone_number} | {item.email}"
            )
            y -= 20

    else:

        pdf.drawString(50, y, "Available upon request.")
        y -= 20

    pdf.setFont("Helvetica-Oblique", 8)

    pdf.drawString(
        50,
        30,
        "Generated by AI Internship & Attachment Matching System"
    )

    pdf.save()

    return response
