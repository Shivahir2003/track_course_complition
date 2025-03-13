from setuptools import setup
setup(

    entry_points={
        "lms.djangoapp": [
            "track_course_complition = track_course_complition.apps:TrackCourseComplitionConfig",
        ],

    }
)
