sudo docker build -t ulozto-downloader-web .
docker run -p 80:5000 --name ulozto-downloader -d ulozto-downloader-web 