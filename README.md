Baciu Marius-Cristian 343C3


GitHub repository: https://github.com/CristiBM/IDP_Project
DockerHub: https://hub.docker.com/repository/docker/bmcristi/idp_project_findatutor


Launching the server:
    docker-compose build
    docker-compose up

The web app can be accessed after 15 seconds at https://127.0.0.1:5000

In order to directly connect to the mysql server:
    docker exec -it project_db_1 mysql -uroot -proot
