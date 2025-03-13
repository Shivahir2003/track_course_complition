from django.apps import AppConfig


class TrackCourseComplitionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'track_course_complition'
    verbose_name = 'track_course_details'

    plugin_app = {
        'url_config': {
            'lms.djangoapp': {
                'namespace': 'track_course_details',
                'regex': '^track_course/',
                'relative_path': 'urls',
            }
        }
    }