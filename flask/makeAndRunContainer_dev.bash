docker build -t ulozto-downloader-web .
docker run -p 80:5000 -v /mnt/e/Downloads/ulozto:/media --name ulozto-downloader-dev -d ulozto-downloader-web 