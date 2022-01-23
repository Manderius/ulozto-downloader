FROM ubuntu 

ENV TZ=Europe/Prague
COPY ./requirements.txt ./var/www/uld/requirements.txt
RUN ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime \
        && apt-get update \
        && apt-get install -y apache2 apache2-utils python3.9 python-is-python3 python3-pip libapache2-mod-wsgi-py3 tor\
        && apt-get clean \
        && pip install -r ./var/www/uld/requirements.txt \
        # change this to correct tflite_runtime version depending on your system and python (following link is for Python 3.8 and x86-64 Linux)
        && pip install https://github.com/google-coral/pycoral/releases/download/release-frogfish/tflite_runtime-2.5.0-cp38-cp38-linux_x86_64.whl

COPY ./uld/ /var/www/uld/
COPY ./uld.conf /etc/apache2/sites-available/000-default.conf
# flask has to have permissions to save film
RUN chown -R www-data /var/www/uld \
        && chown -R www-data /media
EXPOSE 80
CMD ["apache2ctl", "-D","FOREGROUND"]
