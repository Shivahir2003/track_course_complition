from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.grades.api import override_subsection_grade
from lms.djangoapps.grades.constants import GradeOverrideFeatureEnum
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response



from opaque_keys.edx.keys import CourseKey, UsageKey
from xmodule.modulestore.django import modulestore
from completion.models import BlockCompletion


@api_view(["GET", "POST"])
def get_course_details(request):
    if request.method == "POST":
        
        # get course id and user email
        course_id = request.POST.get("course_id")
        user_email = request.POST.get("user_email")

        # get user object
        try:
            student = User.objects.get(email=user_email)
        except User.DoesNotExist:
            student = None

        # get course from modulestore and check enrollment
        course_key = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_key, depth=3)
        course_usage_key = modulestore().make_course_usage_key(course_key)
        is_enrolled = CourseEnrollment.is_enrolled(student, course.id)

        unit_data = {}
        sub_section_data = {}
        section_data = {}
        course_outline = []
        units_data_list = []
        sub_sections_data_list = []
        total_grades_list = []

        block_data = get_course_blocks(
            student,
            course_usage_key,
            allow_start_dates_in_future=True,
            include_completion=True,
        )
        
        # get course outline data
        for section in course.get_children():
            sub_section_count = len(section.get_children())
            for sub_section in section.get_children():
                unit_count = len(sub_section.get_children())
                for unit in sub_section.get_children():
                    unit_complete = block_data.get_xblock_field(
                        unit.usage_key, "complete", False
                    )
                    complete_count = 0
                    incomplete_count = 0
                    if unit_complete:
                        complete_count += 1
                    else:
                        incomplete_count += 1

                    unit_data = {
                        "id": str(unit.usage_key),
                        "name": unit.display_name,
                        "has_completed": unit_complete,
                    }
                    units_data_list.append(unit_data)
                sub_section_complete = block_data.get_xblock_field(sub_section.usage_key, "complete", False)
                sub_section_data = {
                    "id": str(sub_section.usage_key),
                    "name": sub_section.display_name,
                    "unit_count": unit_count,
                    "units": units_data_list.copy(),
                    "has_completed": sub_section_complete,
                }
                units_data_list.clear()
                sub_sections_data_list.append(sub_section_data)
            section_complete = block_data.get_xblock_field(section.usage_key, "complete", False)
            section_data = {
                "id": str(section.usage_key),
                "name": section.display_name,
                "subsection_count": sub_section_count,
                "subsections": sub_sections_data_list.copy(),
                "has_completed": section_complete,
            }
            sub_sections_data_list.clear()
            course_outline.append(section_data)

        # get subsection grade
        grade = CourseGradeFactory().read(student, course)
        subsection_grades_list = list(grade.chapter_grades.values())
        for grade_list in subsection_grades_list:
            sub_sections_data = grade_list.get("sections")
            for sub_section_grade in sub_sections_data:
                gr = sub_section_grade.graded_total
                earned_grade = 0
                possible_grade = 0
                if gr.graded:
                    earned_grade = gr.earned
                    possible_grade = gr.possible
                is_graded = gr.graded
                total_grades = {
                    "sub_section_name": sub_section_grade.display_name,
                    "earned_grade": earned_grade,
                    "possible_grade": possible_grade,
                    "is_graded": is_graded,
                    "id": str(sub_section_grade.location),
                }
                total_grades_list.append(total_grades)

        user_details = {
            "username": student.username,
            "email": student.email,
            "first_name": student.first_name,
            "last_name": student.last_name,
        }
        course_details = {
            "name": course.display_name,
            "start": course.start.strftime("%d-%m-%Y %I:%M %p"),
            "end": course.end.strftime("%d-%m-%Y %I:%M %p"),
        }
        data = {
            "is_enrolled": is_enrolled,
            "user_details": user_details,
            "course_details": course_details,
            "course_outline": course_outline,
            "course_grades": total_grades_list,
        }
        return Response(data, status=status.HTTP_200_OK)
    return render(request, "user_data_template.html")


@api_view(["POST"])
def complete_block(request):

    course_id = request.POST.get("course_id")
    user_email = request.POST.get("user_email")
    block_id = request.POST.get("block_id")
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        user = None

    block_usage_key = UsageKey.from_string(block_id)

    if BlockCompletion.objects.filter(context_key=course_id, user=user, block_key=block_usage_key):
        message = {"success": "block is already completed"}
    else:
        try:
            BlockCompletion.objects.submit_completion(user=user, block_key=block_usage_key, completion=1.0)
            message = {"success": "block is completed successfully"}
        except BlockCompletion:
            message = {"error": "something went wrong try again"}
    return Response(message)


@api_view(["POST"])
def set_grade(request):
    user_email = request.POST.get('user_email')
    course_id = request.POST.get('course_id')
    grade = request.POST.get('grade')
    subsection_id = request.POST.get('section_id')

    course_key = CourseKey.from_string(course_id)
    block_usage_key = UsageKey.from_string(subsection_id)
    user = User.objects.get(email=user_email)
    feature=GradeOverrideFeatureEnum.proctoring

    override_subsection_grade(
        user.id,
        course_key,
        block_usage_key,
        earned_all=0.0,
        earned_graded=grade,
        feature=feature,
        overrider=None,
        comment=None,
    )
    message = {"success": "grade reseted succesfully"}

    return Response(message)
