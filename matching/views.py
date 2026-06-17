from django.utils import timezone

from internships.models import InternshipOpportunity

def get_recommendation_label(score):
    if score >= 90:
        return 'Excellent Match'

    if score >= 70:
        return 'Good Match'

    if score >= 50:
        return 'Fair Match'

    return 'Low Match'

def normalize_skills(skill_text):

    if not skill_text:
        return []

    separators = ['\n', ';', '|']

    for separator in separators:
        skill_text = skill_text.replace(separator, ',')

    return list({
        skill.strip().lower()
        for skill in skill_text.split(',')
        if skill.strip()
    })


def skill_matches(required_skill, student_skills):

    required_skill = required_skill.lower().strip()

    for student_skill in student_skills:

        student_skill = student_skill.lower().strip()

        if required_skill == student_skill:
            return True

        if required_skill in student_skill:
            return True

        if student_skill in required_skill:
            return True

    return False


def calculate_match_score(student, opportunity):

    manual_skills = normalize_skills(student.skills)

    cv_skills = normalize_skills(student.extracted_skills)

    student_skills = list(set(manual_skills + cv_skills))

    required_skills = normalize_skills(opportunity.required_skills)

    matched_skills = []
    missing_skills = []
    cv_detected_matches = []

    if not required_skills:
        base_score = 30
    else:
        base_score = 0

    for required_skill in required_skills:

        if skill_matches(required_skill, student_skills):

            matched_skills.append(required_skill.title())

            base_score += 20

            if skill_matches(required_skill, cv_skills):
                cv_detected_matches.append(required_skill.title())

        else:

            missing_skills.append(required_skill.title())

    score = base_score

    strengths = []

    if matched_skills:
        strengths.append(
            f"Candidate matches key required skills: {', '.join(matched_skills)}."
        )

    if cv_detected_matches:
        strengths.append(
            f"CV confirms practical exposure to: {', '.join(cv_detected_matches)}."
        )

    if student.github:
        score += 5
        strengths.append(
            "GitHub profile is available, allowing technical work verification."
        )

    if student.portfolio:
        score += 5
        strengths.append(
            "Portfolio website is available, showing project evidence."
        )

    if student.linkedin:
        score += 3
        strengths.append(
            "LinkedIn profile is available for professional background review."
        )

    if student.cv:
        score += 7
        strengths.append(
            "Professional CV is uploaded and available for employer review."
        )

    if student.location and opportunity.location:
        student_location = student.location.lower().strip()
        opportunity_location = opportunity.location.lower().strip()

        if student_location in opportunity_location or opportunity_location in student_location:
            score += 10
            strengths.append(
                f"Location preference matches this opportunity: {opportunity.location}."
            )

    if student.course:
        course_text = student.course.lower().strip()
        opportunity_text = f"{opportunity.title} {opportunity.description}".lower()

        if course_text and course_text in opportunity_text:
            score += 8
            strengths.append(
                f"Course background is relevant to this opportunity: {student.course}."
            )

    if student.bio:
        score += 3
        strengths.append(
            "Profile bio adds extra context about the candidate."
        )

    score = min(score, 100)

    explanations = []

    if matched_skills:
        explanations.append(
            f"The candidate aligns with {len(matched_skills)} required skill(s): "
            f"{', '.join(matched_skills)}."
        )

    if missing_skills:
        explanations.append(
            f"The candidate may need improvement in: {', '.join(missing_skills)}."
        )
    else:
        explanations.append(
            "No major required skill gaps were detected."
        )

    if cv_detected_matches:
        explanations.append(
            "Some matching skills were detected directly from the uploaded CV, "
            "which improves confidence in the match."
        )

    recommendation_label = get_recommendation_label(score)

    explanations.append(
        f"Overall recommendation: {recommendation_label}."
    )
    return score, {
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'strengths': strengths,
        'explanations': explanations,
        'recommendation_label': recommendation_label,
    }


def get_matched_opportunities(student):

    opportunities = InternshipOpportunity.objects.filter(
        status='open',
        deadline__gte=timezone.localdate()
    )

    matched_results = []

    for opportunity in opportunities:

        score, analysis = calculate_match_score(
            student,
            opportunity
        )

        matched_results.append({
            'opportunity': opportunity,
            'score': score,
            'matched_skills': analysis['matched_skills'],
            'missing_skills': analysis['missing_skills'],
            'strengths': analysis['strengths'],
            'explanations': analysis['explanations'],
            'recommendation_label': analysis['recommendation_label'],
        })

    matched_results.sort(
        key=lambda item: item['score'],
        reverse=True
    )

    return matched_results
