run-air:
	docker run \
	-d -p 8080:8080 \
	-v $(CURDIR)/dags:/usr/local/airflow/dags \
	-v $(CURDIR)/plugins:/usr/local/airflow/plugins \
	--env FERNET_KEY \
	--name dsg-airflow_puckel \
	puckel/docker-airflow
start-air:
	docker start dsg-airflow_puckel
stop-air:
	docker stop dsg-airflow_puckel
rm-air:
	docker rm dsg-airflow_puckel
bash-air:
	docker exec --env FERNET_KEY -ti dsg-airflow_puckel bash
dcup:
	docker-compose up -d
dcdown:
	docker-compose down

