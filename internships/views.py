from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from reportlab.pdfgen import canvas

from employers.models import EmployerProfile
from matching.views import calculate_match_score, get_matched_opportunities
from notifications.models import Notification
from notifications.email_service import send_system_email

from students.models import (
    StudentProfile,
    AcademicQualification,
    WorkExperience,
    Referee
)

from .forms import InternshipOpportunityForm, InterviewScheduleForm
from .models import Application, InternshipOpportunity


def build_absolute_url(request, view_name, *args):

    return request.build_absolute_uri(
        reverse(
            view_name,
            args=args
        )
    )


@login_required
def opportunity_list(request):

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if student is None:
        messages.error(
            request,
            'Please complete your student profile first.'
        )
        return redirect('create_student_profile')

    query = request.GET.get('q', '').strip()

    matched_results = get_matched_opportunities(student)

    if query:

        search_term = query.lower()

        matched_results = [
            result
            for result in matched_results
            if search_term in result['opportunity'].title.lower()
            or search_term in result['opportunity'].location.lower()
            or search_term in result['opportunity'].required_skills.lower()
            or search_term in result['opportunity'].employer.company_name.lower()
        ]

    for result in matched_results:

        result['already_applied'] = Application.objects.filter(
            student=student,
            opportunity=result['opportunity']
        ).exists()

    return render(
        request,
        'internships/opportunity_list.html',
        {
            'matched_results': matched_results,
            'query': query,
        }
    )


@login_required
def opportunity_detail(request, opportunity_id):

    opportunity = get_object_or_404(
        InternshipOpportunity,
        id=opportunity_id
    )

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    already_applied = False
    score = 0
    matched_skills = []
    missing_skills = []
    strengths = []
    explanations = []

    if student:

        already_applied = Application.objects.filter(
            student=student,
            opportunity=opportunity
        ).exists()

        score, analysis = calculate_match_score(
            student,
            opportunity
        )

        matched_skills = analysis.get('matched_skills', [])
        missing_skills = analysis.get('missing_skills', [])
        strengths = analysis.get('strengths', [])
        explanations = analysis.get('explanations', [])

    return render(
        request,
        'internships/opportunity_detail.html',
        {
            'opportunity': opportunity,
            'already_applied': already_applied,
            'score': score,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'strengths': strengths,
            'explanations': explanations,
        }
    )


@login_required
def apply_opportunity(request, opportunity_id):

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if student is None:
        messages.error(
            request,
            'Please complete your student profile first.'
        )
        return redirect('create_student_profile')

    opportunity = get_object_or_404(
        InternshipOpportunity,
        id=opportunity_id
    )

    if opportunity.status != 'open':
        messages.warning(
            request,
            'This opportunity is currently closed.'
        )
        return redirect('opportunity_list')

    already_applied = Application.objects.filter(
        student=student,
        opportunity=opportunity
    ).exists()

    if already_applied:

        messages.info(
            request,
            'You already applied for this opportunity.'
        )

    else:

        application = Application.objects.create(
            student=student,
            opportunity=opportunity
        )

        employer_user = opportunity.employer.user

        employer_message = (
            f'A new student has applied for your opportunity.\n\n'
            f'Student: {student.full_name or student.user.username}\n'
            f'Email: {student.user.email}\n'
            f'Phone: {student.phone_number}\n'
            f'Opportunity: {opportunity.title}'
        )

        Notification.objects.create(
            user=employer_user,
            message=employer_message
        )

        send_system_email(
            subject=f'New Application - {opportunity.title}',
            message=employer_message,
            recipient_list=[
                employer_user.email
            ],
            button_text='Review Application',
            button_url=build_absolute_url(
                request,
                'application_detail',
                application.id
            )
        )

        messages.success(
            request,
            'Application submitted successfully.'
        )

    return redirect('opportunity_list')


@login_required
def my_applications(request):

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if student is None:
        messages.error(
            request,
            'Please complete your student profile first.'
        )
        return redirect('create_student_profile')

    applications = Application.objects.filter(
        student=student
    ).order_by('-applied_at')

    return render(
        request,
        'internships/my_applications.html',
        {
            'applications': applications
        }
    )


@login_required
def my_interviews(request):

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    if student is None:
        messages.error(
            request,
            'Please complete your student profile first.'
        )
        return redirect('create_student_profile')

    interviews = Application.objects.filter(
        student=student,
        status='interview_scheduled'
    ).order_by('interview_date')

    return render(
        request,
        'internships/my_interviews.html',
        {
            'interviews': interviews
        }
    )


@login_required
def accept_interview(request, application_id):

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    application = get_object_or_404(
        Application,
        id=application_id,
        student=student
    )

    application.interview_response = 'accepted'
    application.save()

    employer_user = application.opportunity.employer.user

    employer_message = (
        f'{student.full_name or student.user.username} has accepted the interview invitation.\n\n'
        f'Opportunity: {application.opportunity.title}\n'
        f'Date: {application.interview_date}\n'
        f'Time: {application.interview_time}'
    )

    Notification.objects.create(
        user=employer_user,
        message=employer_message
    )

    send_system_email(
        subject=f'Interview Accepted - {application.opportunity.title}',
        message=employer_message,
        recipient_list=[
            employer_user.email
        ],
        button_text='View Application',
        button_url=build_absolute_url(
            request,
            'application_detail',
            application.id
        )
    )

    messages.success(
        request,
        'Interview invitation accepted successfully.'
    )

    return redirect('my_interviews')


@login_required
def decline_interview(request, application_id):

    student = StudentProfile.objects.filter(
        user=request.user
    ).first()

    application = get_object_or_404(
        Application,
        id=application_id,
        student=student
    )

    application.interview_response = 'declined'
    application.save()

    employer_user = application.opportunity.employer.user

    employer_message = (
        f'{student.full_name or student.user.username} has declined the interview invitation.\n\n'
        f'Opportunity: {application.opportunity.title}\n'
        f'Date: {application.interview_date}\n'
        f'Time: {application.interview_time}'
    )

    Notification.objects.create(
        user=employer_user,
        message=employer_message
    )

    send_system_email(
        subject=f'Interview Declined - {application.opportunity.title}',
        message=employer_message,
        recipient_list=[
            employer_user.email
        ],
        button_text='View Application',
        button_url=build_absolute_url(
            request,
            'application_detail',
            application.id
        )
    )

    messages.warning(
        request,
        'Interview invitation declined.'
    )

    return redirect('my_interviews')


@login_required
def employer_applications(request):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    status_filter = request.GET.get('status')

    applications = Application.objects.filter(
        opportunity__employer=employer
    )

    if status_filter:
        applications = applications.filter(
            status=status_filter
        )

    ranked_applications = []

    for application in applications:

        score, analysis = calculate_match_score(
            application.student,
            application.opportunity
        )

        ranked_applications.append({
            'application': application,
            'score': score,
            'matched_skills': analysis.get('matched_skills', []),
            'missing_skills': analysis.get('missing_skills', []),
        })

    ranked_applications.sort(
        key=lambda item: item['score'],
        reverse=True
    )

    return render(
        request,
        'internships/employer_applications.html',
        {
            'ranked_applications': ranked_applications,
            'status_filter': status_filter,
        }
    )


@login_required
def application_detail(request, application_id):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    application = get_object_or_404(
        Application,
        id=application_id,
        opportunity__employer=employer
    )

    score, analysis = calculate_match_score(
        application.student,
        application.opportunity
    )

    academic_qualifications = AcademicQualification.objects.filter(
        student=application.student
    ).order_by('-end_year')

    work_experiences = WorkExperience.objects.filter(
        student=application.student
    ).order_by('-start_date')

    referees = Referee.objects.filter(
        student=application.student
    ).order_by('-created_at')

    return render(
        request,
        'internships/application_detail.html',
        {
            'application': application,
            'score': score,
            'matched_skills': analysis.get('matched_skills', []),
            'missing_skills': analysis.get('missing_skills', []),
            'strengths': analysis.get('strengths', []),
            'explanations': analysis.get('explanations', []),
            'academic_qualifications': academic_qualifications,
            'work_experiences': work_experiences,
            'referees': referees,
        }
    )


@login_required
def update_application_status(request, application_id, status):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    application = get_object_or_404(
        Application,
        id=application_id,
        opportunity__employer=employer
    )

    valid_statuses = [
        'pending',
        'reviewed',
        'shortlisted',
        'interview_scheduled',
        'accepted',
        'rejected',
    ]

    if status not in valid_statuses:
        messages.error(
            request,
            'Invalid application status.'
        )
        return redirect('employer_applications')

    application.status = status
    application.save()

    status_messages = {
        'pending': 'Your application status is currently pending.',
        'reviewed': 'Your application has been reviewed by the employer.',
        'shortlisted': 'Congratulations! You have been shortlisted for this opportunity.',
        'interview_scheduled': 'Your interview has been scheduled.',
        'accepted': 'Congratulations! Your application has been accepted.',
        'rejected': 'We regret to inform you that your application was not successful.',
    }

    user_message = status_messages.get(
        status,
        f'Your application status was updated to {status}.'
    )

    full_message = (
        f'{user_message}\n\n'
        f'Opportunity: {application.opportunity.title}\n'
        f'Company: {application.opportunity.employer.company_name}'
    )

    Notification.objects.create(
        user=application.student.user,
        message=full_message
    )

    send_system_email(
        subject=f'Application Update - {application.opportunity.title}',
        message=full_message,
        recipient_list=[
            application.student.user.email
        ],
        button_text='View My Applications',
        button_url=build_absolute_url(
            request,
            'my_applications'
        )
    )

    messages.success(
        request,
        'Application status updated successfully. Student notification and email sent.'
    )

    return redirect('employer_applications')


@login_required
def schedule_interview(request, application_id):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    application = get_object_or_404(
        Application,
        id=application_id,
        opportunity__employer=employer
    )

    if request.method == 'POST':

        form = InterviewScheduleForm(
            request.POST,
            instance=application
        )

        if form.is_valid():

            interview = form.save(commit=False)

            interview.status = 'interview_scheduled'
            interview.interview_response = 'pending'
            interview.save()

            interview_message = (
                f'You have been invited for an interview.\n\n'
                f'Opportunity: {interview.opportunity.title}\n'
                f'Company: {interview.opportunity.employer.company_name}\n'
                f'Date: {interview.interview_date}\n'
                f'Time: {interview.interview_time}\n'
                f'Location / Link: {interview.interview_location}\n\n'
                f'Notes: {interview.interview_notes}'
            )

            Notification.objects.create(
                user=interview.student.user,
                message=interview_message
            )

            send_system_email(
                subject=f'Interview Scheduled - {interview.opportunity.title}',
                message=interview_message,
                recipient_list=[
                    interview.student.user.email
                ],
                button_text='Respond to Interview',
                button_url=build_absolute_url(
                    request,
                    'my_interviews'
                )
            )

            messages.success(
                request,
                'Interview scheduled successfully. Student notification and email sent.'
            )

            return redirect(
                'application_detail',
                application_id=interview.id
            )

    else:

        form = InterviewScheduleForm(
            instance=application
        )

    return render(
        request,
        'internships/schedule_interview.html',
        {
            'form': form,
            'application': application,
        }
    )


@login_required
def create_opportunity(request):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    if request.method == 'POST':

        form = InternshipOpportunityForm(
            request.POST
        )

        if form.is_valid():

            opportunity = form.save(commit=False)
            opportunity.employer = employer
            opportunity.save()

            messages.success(
                request,
                'Opportunity created successfully.'
            )

            return redirect('my_opportunities')

    else:

        form = InternshipOpportunityForm()

    return render(
        request,
        'internships/create_opportunity.html',
        {
            'form': form
        }
    )


@login_required
def my_opportunities(request):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    opportunities = InternshipOpportunity.objects.filter(
        employer=employer
    ).order_by('-created_at')

    return render(
        request,
        'internships/my_opportunities.html',
        {
            'opportunities': opportunities
        }
    )


@login_required
def edit_opportunity(request, opportunity_id):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    opportunity = InternshipOpportunity.objects.filter(
        id=opportunity_id,
        employer=employer
    ).first()

    if opportunity is None:
        messages.error(
            request,
            'Opportunity not found.'
        )
        return redirect('my_opportunities')

    if request.method == 'POST':

        form = InternshipOpportunityForm(
            request.POST,
            instance=opportunity
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Opportunity updated successfully.'
            )

            return redirect('my_opportunities')

    else:

        form = InternshipOpportunityForm(
            instance=opportunity
        )

    return render(
        request,
        'internships/edit_opportunity.html',
        {
            'form': form
        }
    )


@login_required
def delete_opportunity(request, opportunity_id):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    opportunity = InternshipOpportunity.objects.filter(
        id=opportunity_id,
        employer=employer
    ).first()

    if opportunity:

        opportunity.delete()

        messages.success(
            request,
            'Opportunity deleted successfully.'
        )

    else:

        messages.error(
            request,
            'Opportunity not found.'
        )

    return redirect('my_opportunities')


@login_required
def toggle_opportunity_status(request, opportunity_id):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    opportunity = InternshipOpportunity.objects.filter(
        id=opportunity_id,
        employer=employer
    ).first()

    if opportunity is None:
        messages.error(
            request,
            'Opportunity not found.'
        )
        return redirect('my_opportunities')

    if opportunity.status == 'open':

        opportunity.status = 'closed'

        messages.warning(
            request,
            'Opportunity closed successfully.'
        )

    else:

        opportunity.status = 'open'

        messages.success(
            request,
            'Opportunity reopened successfully.'
        )

    opportunity.save()

    return redirect('my_opportunities')


@login_required
def employer_applications_pdf(request):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        messages.error(
            request,
            'Please complete your employer profile first.'
        )
        return redirect('create_employer_profile')

    applications = Application.objects.filter(
        opportunity__employer=employer
    ).order_by('-applied_at')

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        'attachment; filename="applications_report.pdf"'
    )

    pdf = canvas.Canvas(response)
    pdf.setTitle("Employer Applications Report")

    width = 595
    height = 842

    pdf.setFillColorRGB(0.1, 0.1, 0.1)
    pdf.rect(0, height - 80, width, 80, fill=1)

    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(50, height - 50, "Employer Applications Report")

    y = height - 120

    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica", 11)

    pdf.drawString(50, y, f"Company: {employer.company_name}")
    y -= 20

    pdf.drawString(50, y, f"Generated by: {request.user.username}")
    y -= 20

    pdf.drawString(
        50,
        y,
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    y -= 35

    accepted = applications.filter(
        status='accepted'
    ).count()

    rejected = applications.filter(
        status='rejected'
    ).count()

    shortlisted = applications.filter(
        status='shortlisted'
    ).count()

    pdf.setFillColorRGB(0.95, 0.95, 0.95)
    pdf.rect(50, y - 40, 500, 40, fill=1)

    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(60, y - 15, f"Total Applications: {applications.count()}")
    pdf.drawString(230, y - 15, f"Accepted: {accepted}")
    pdf.drawString(340, y - 15, f"Shortlisted: {shortlisted}")
    pdf.drawString(470, y - 15, f"Rejected: {rejected}")

    y -= 70

    pdf.setFillColorRGB(0.2, 0.2, 0.2)
    pdf.rect(50, y, 500, 25, fill=1)

    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 9)

    pdf.drawString(60, y + 8, "Student")
    pdf.drawString(150, y + 8, "Course")
    pdf.drawString(280, y + 8, "Opportunity")
    pdf.drawString(430, y + 8, "Status")
    pdf.drawString(500, y + 8, "Date")

    y -= 25

    pdf.setFont("Helvetica", 8)

    row_color = True

    for application in applications:

        if y < 80:

            pdf.showPage()
            y = height - 80

            pdf.setFillColorRGB(0.2, 0.2, 0.2)
            pdf.rect(50, y, 500, 25, fill=1)

            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont("Helvetica-Bold", 9)

            pdf.drawString(60, y + 8, "Student")
            pdf.drawString(150, y + 8, "Course")
            pdf.drawString(280, y + 8, "Opportunity")
            pdf.drawString(430, y + 8, "Status")
            pdf.drawString(500, y + 8, "Date")

            y -= 25
            pdf.setFont("Helvetica", 8)

        if row_color:
            pdf.setFillColorRGB(0.97, 0.97, 0.97)

        else:
            pdf.setFillColorRGB(1, 1, 1)

        pdf.rect(50, y, 500, 22, fill=1)
        pdf.setFillColorRGB(0, 0, 0)

        pdf.drawString(60, y + 7, application.student.user.username[:15])
        pdf.drawString(150, y + 7, application.student.course[:18])
        pdf.drawString(280, y + 7, application.opportunity.title[:22])
        pdf.drawString(430, y + 7, application.status.capitalize())

        pdf.drawString(
            500,
            y + 7,
            application.applied_at.strftime('%Y-%m-%d')
        )

        y -= 22
        row_color = not row_color

    pdf.setFont("Helvetica-Oblique", 8)

    pdf.drawString(
        50,
        30,
        "Generated by AI Internship & Attachment Matching System"
    )

    pdf.save()

    return response
