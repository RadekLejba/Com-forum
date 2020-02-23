superuser:
	docker-compose run web python manage.py createsuperuser

run:
	docker-compose run --service-ports web

test:
	docker-compose run web python manage.py test

test_posting:
	docker-compose run web python manage.py test posting

migrations:
	docker-compose run web python manage.py makemigrations
	docker-compose run web python manage.py migrate
