web: python manage.py collectstatic --noinput --clear && python manage.py migrate && daphne -b 0.0.0.0 -p $PORT taxi_project.asgi:application
