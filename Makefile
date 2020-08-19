run-air:
	docker run \
	-d -p 8080:8080 \
	-v /home/osboxes/sandbox/dea-airflow/dags:/usr/local/airflow/dags \
	-v /home/osboxes/sandbox/dea-airflow/plugins:/usr/local/airflow/plugins \
	--env FERNET_KEY \
	--name dea-airflow_webserver_1 \
	puckel/docker-airflow
start-air:
	docker start dea-airflow_webserver_1
stop-air:
	docker stop dea-airflow_webserver_1
rm-air:
	docker rm dea-airflow_webserver_1
bash-air:
	docker exec   --env FERNET_KEY  -ti dea-airflow_webserver_1 bash
