run:
	docker-compose run --service-ports web

test:
	docker-compose run web python manage.py test

migrations:
	docker-compose run web python manage.py makemigrations
	docker-compose run web python manage.py migrate
