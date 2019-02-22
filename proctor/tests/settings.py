TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

SECRET_KEY = 'fake-secret-key-used-for-testing-only'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django_email',
)

SUBWH_HOST = 'fake-settings-value'
SUBWH_LDAP_USERNAME = 'fake-settings-username'
SUBWH_LDAP_PASSWORD = 'fake-settings-pw'

PRODUCT_GROUP = 'fake-group'
PROJECT_NAME = 'fake-project'
HOSTNAME = 'fake-host'

PROCTOR_API_ROOT = 'fake-proctor-api-url'
PROCTOR_TESTS = [
    'fake_proctor_test_in_settings',
]
