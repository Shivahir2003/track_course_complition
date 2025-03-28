from django.urls import path
from track_course_complition.views import (
        GetCourseDetails,
        CompleteCourseBlock,
        SetSubsectionGrade
    )

urlpatterns = [
    path('get_course_details',GetCourseDetails.as_view(), name='get_course_details'),
    path('complete_block',CompleteCourseBlock.as_view(),name='complete_block'),
    path('set_grade',SetSubsectionGrade.as_view(),name='set_grade')
]
