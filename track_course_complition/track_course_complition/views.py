from completion.models import BlockCompletion
from django.contrib.auth.models import User
from django.shortcuts import render
from opaque_keys.edx.keys import CourseKey, UsageKey

from common.djangoapps.student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.courseware.block_render import get_block
from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.grades.api import CourseGradeFactory


@api_view(["GET", "POST"])
def get_course_details(request):
    """
        get user details, course details and course outline, course grade
        
        Arguments:
            request (HttpRequest)
        
        Required Parameters:
            course_id,user_email
        
        Returns:
            In Get : render add track course completion page
            In Post : get user email and course id and return course details, 
                user details and course outline, course grade
    """

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
        if course.start and course.end:
            course_details = {
                "name": course.display_name,
                "start": course.start.strftime("%d-%m-%Y %I:%M %p"),
                "end": course.end.strftime("%d-%m-%Y %I:%M %p"),
            }
        else:
            course_details = {
            "name": course.display_name,
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
    """
        mark course block as completed
        
        Arguments:
            request (HttpRequest)
        
        Required Parameters:
            course_id,user_email,block_id
        
        Returns:
            In Post : get user email, block_id, course id and mark block as completed
    """
    # get block_id, course_id and user email 
    course_id = request.POST.get("course_id")
    user_email = request.POST.get("user_email")
    block_id = request.POST.get("block_id")
    message = {}
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        user = None

    # get block to mark complete 
    block_usage_key = UsageKey.from_string(block_id)
    course_key = CourseKey.from_string(course_id)
    course = modulestore().get_course(course_key, depth=3)
    field_data_cache = FieldDataCache.cache_for_block_descendents(course.id,user,course,depth=2)
    block = get_block(user,request,block_usage_key,field_data_cache,)

    if BlockCompletion.objects.filter(context_key=course_id, user=user, block_key=block_usage_key):
        message = {"success": "block is already completed"}

    # mark block as complete
    if block_usage_key.block_type == 'chapter':
        for subsection in block.get_children():
            for unit in subsection.get_children():
                for problem in unit.get_children():
                    try:
                        BlockCompletion.objects.submit_completion(
                            user=user, 
                            block_key=problem.usage_key,
                            completion=1.0
                        )
                        message = {"success": "block is completed successfully"}
                    except BlockCompletion:
                        message = {"error": "something went wrong try again"}
    elif block_usage_key.block_type == 'sequential':
        for unit in block.get_children():
            for problem in unit.get_children():
                try:
                    BlockCompletion.objects.submit_completion(
                        user=user, 
                        block_key=problem.usage_key,
                        completion=1.0
                    )
                    message = {"success": "block is completed successfully"}
                except BlockCompletion:
                    message = {"error": "something went wrong try again"}
    elif block_usage_key.block_type == 'vertical':
        for problem in block.get_children():
            try:
                BlockCompletion.objects.submit_completion(
                    user=user, 
                    block_key=problem.usage_key,
                    completion=1.0
                )
                message = {"success": "block is completed successfully"}
            except BlockCompletion:
                message = {"error": "something went wrong try again"}
    else :
        message = {"error": "something went wrong try again"}


    return Response(message)

@api_view(["POST"])
def set_grade(request):
    """
        set grade in for subsection
        
        Arguments:
            request (HttpRequest)
        
        Required Parameters:
            course_id,user_email,subsection_id, grade
        
        Returns:
            In Post : get user email, block_id, course id, grade and update grade
    """
    # get grade, user email, course id subsection id
    user_email = request.POST.get('user_email')
    course_id = request.POST.get('course_id')
    grade = request.POST.get('grade')
    subsection_id = request.POST.get('section_id')
    max_value = 1

    # get course, user, and subsection block
    course_key = CourseKey.from_string(course_id)
    course = modulestore().get_course(course_key, depth=3)
    user = User.objects.get(email=user_email)
    field_data_cache = FieldDataCache.cache_for_block_descendents(course.id,user,course,depth=2)
    subsetion_usage_key = UsageKey.from_string(subsection_id)
    block = get_block(user,request,subsetion_usage_key,field_data_cache,)

    grade_dict = {'value': grade, 'max_value': max_value, 'user_id': user.id}

    # set grade for given subsection
    for unit in block.get_children():
        if int(grade) != 0:
            score = (len(unit.get_children())/int(grade))
            grade_dict = {'value': score, 'max_value': max_value, 'user_id': user.id}

        for problem in unit.get_children():
            problem.runtime.publish(problem, 'grade', grade_dict)

    message = {"success": "grade reseted succesfully"}

    return Response(message)
