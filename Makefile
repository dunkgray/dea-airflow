run-air:
	docker run \
	-d -p 8080:8080 \
	-v $(CURDIR)/dags:/usr/local/airflow/dags \
	-v $(CURDIR)/plugins:/usr/local/airflow/plugins \
	--env FERNET_KEY \
	--name dea-airflow_puckel \
	puckel/docker-airflow
start-air:
	docker start dea-airflow_puckel
stop-air:
	docker stop dea-airflow_puckel
rm-air:
	docker rm dea-airflow_puckel
bash-air:
	docker exec --env FERNET_KEY -ti dea-airflow_puckel bash
dcup:
	docker-compose up -d
dcdown:
	docker-compose down

