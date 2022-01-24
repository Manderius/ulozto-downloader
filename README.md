# Web pro Ulož.to downloader

Webserver pro stahovač z [Ulož.to](http://ulozto.cz) vycházející z projektu [Ulož.to downloader](https://github.com/setnicka/ulozto-downloader#ulo%C5%BEto-downloader) (credits to Jirka Setnicka) Kromě níže zmíněných omezení umí vše, co [Ulož.to downloader](https://github.com/setnicka/ulozto-downloader#ulo%C5%BEto-downloader) umí. Server spouští původní projekt v podprocesu a poté z něj čte výstup.

Tuto verzi jsem napsal pro docker na mém rpi 4 sloužícím mimo jiné jako NAS. Backend je psaný v ve flasku. Kontejner vytvoří apache server, na kterém jej spustí.

## Omezení
* Do konzole lze zapsat input pouze jednou
* Nedokáže zobrazit captcha kódy - spoléhá na jejich automatické louskání

## Klíčové vlastnosti
* Zahrnuje všechny vlastnosti z původního projektu
* Podporuje paralelní stahování
* Umí zastavit stahování

## Instalace
Pomocí Dockerfile stačí vytvořit image a následně jej spustit
```shell
$ sudo docker build -t uld .
docker run -p 80:5000
```
## Použití
V config.json v `paths` jsou uloženy cesty ke složkám do nichž se může stahovat, nicméně k nim musí mít uživatel `www-data` práva k zápisu.

## Screenshoty
![Ukázka stahování](https://raw.githubusercontent.com/Kvasa52/ulozto-downloader/master/zadaniDat.png)
![Ukázka stahování](https://raw.githubusercontent.com/Kvasa52/ulozto-downloader/master/stahovani.png)
(pozadí ve druhém screenu je zopakované pouze kvůli metodě screenshotu)
