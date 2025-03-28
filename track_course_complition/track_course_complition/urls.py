from django.contrib import admin
from django.urls import path,include
from track_course_complition.views import get_course_details,complete_block,set_grade

urlpatterns = [
    path('get_course_details',get_course_details, name='get_course_details'),
    path('complete_block',complete_block,name='complete_block'),
    path('set_grade',set_grade,name='set_grade')
]
