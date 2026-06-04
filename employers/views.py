from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .forms import EmployerProfileForm
from .models import EmployerProfile

from internships.models import InternshipOpportunity, Application
from matching.views import calculate_match_score


@login_required
def create_employer_profile(request):

    existing_profile = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if existing_profile:
        return redirect('employer_profile')

    if request.method == 'POST':

        form = EmployerProfileForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            employer = form.save(commit=False)
            employer.user = request.user
            employer.save()

            messages.success(
                request,
                'Employer profile created successfully.'
            )

            return redirect('employer_profile')

    else:

        form = EmployerProfileForm()

    return render(
        request,
        'employers/create_profile.html',
        {'form': form}
    )


@login_required
def employer_profile(request):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        return redirect('create_employer_profile')

    opportunities = InternshipOpportunity.objects.filter(
        employer=employer
    )

    applications = Application.objects.filter(
        opportunity__employer=employer
    )

    total_applications = applications.count()
    accepted_count = applications.filter(status='accepted').count()
    rejected_count = applications.filter(status='rejected').count()
    shortlisted_count = applications.filter(status='shortlisted').count()
    pending_count = applications.filter(status='pending').count()
    interview_scheduled_count = applications.filter(
        status='interview_scheduled'
    ).count()

    acceptance_rate = 0

    if total_applications > 0:
        acceptance_rate = round(
            (accepted_count / total_applications) * 100,
            1
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

    top_candidate = None

    if ranked_applications:
        top_candidate = ranked_applications[0]

    recent_applications = applications.order_by(
        '-applied_at'
    )[:5]

    context = {
        'profile': employer,
        'total_opportunities': opportunities.count(),
        'open_opportunities': opportunities.filter(status='open').count(),
        'closed_opportunities': opportunities.filter(status='closed').count(),
        'total_applications': total_applications,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'shortlisted_count': shortlisted_count,
        'pending_count': pending_count,
        'interview_scheduled_count': interview_scheduled_count,
        'acceptance_rate': acceptance_rate,
        'top_candidate': top_candidate,
        'ranked_applications': ranked_applications[:5],
        'recent_applications': recent_applications,
    }

    return render(
        request,
        'employers/profile.html',
        context
    )


@login_required
def edit_employer_profile(request):

    employer = EmployerProfile.objects.filter(
        user=request.user
    ).first()

    if employer is None:
        return redirect('create_employer_profile')

    if request.method == 'POST':

        form = EmployerProfileForm(
            request.POST,
            request.FILES,
            instance=employer
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Employer profile updated successfully.'
            )

            return redirect('employer_profile')

    else:

        form = EmployerProfileForm(
            instance=employer
        )

    return render(
        request,
        'employers/edit_profile.html',
        {'form': form}
    )

@login_required
def company_detail(request, employer_id):

    employer = EmployerProfile.objects.filter(
        id=employer_id
    ).first()

    if employer is None:
        messages.error(request, 'Company not found.')
        return redirect('opportunity_list')

    opportunities = InternshipOpportunity.objects.filter(
        employer=employer,
        status='open'
    ).order_by('-created_at')

    return render(
        request,
        'employers/company_detail.html',
        {
            'employer': employer,
            'opportunities': opportunities,
        }
    )