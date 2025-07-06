build:
	cd client && docker build -t client:dev .
	cd server && docker build -t server:dev .
	
run:
	docker run --name client -d -p 3000:3000 client:dev
	docker run --name server -d -p 3003:3003 server:dev

down:
	docker rm -f client
	docker rm -f server

docker-down-all:
	docker rm -f $(docker ps -aq)

restart: down build run

run-portainer:
	docker run -d -p 9000:9000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest