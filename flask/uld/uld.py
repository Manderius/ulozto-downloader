import json
import os
import subprocess
import sys
import signal

from ansi2html import Ansi2HTMLConverter
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField)
from wtforms.validators import InputRequired
from datetime import datetime


class URLForm(FlaskForm):
    url = StringField("", [InputRequired()])
    submit = SubmitField("Odeslat")


class JsonReader():
    def __init__(self) -> None:
        workingDir = os.path.abspath(os.path.dirname(__file__))
        self.configPath = os.path.join(workingDir, "config.json")
        self.read()

    @property
    def instance(self):
        self.read()
        return self._instance

    def read(self):
        # print(os.getcwd())
        self._instance = None
        try:
            f = open(self.configPath)
            self._instance = json.loads(f.read())
            f.close()
        except:
            print(os.listdir())
            print("server can't access config.json")

    def save(self):
        of = open(self.configPath, "w")
        of.write(json.dumps(self._instance, indent=4))
        of.close()


class ProcessHandler():
    def __init__(self) -> None:
        self.process = None
        self.currentOutput = {"start": [], "middle": {}, "end": []}
        self.url = None
        self.status = {}

    def startProcess(self, url, path, processId):
        self.url = url
        self.id = processId
        workingDir = os.path.abspath(os.path.dirname(__file__))
        self.currentOutput = {"start": [], "middle": {}, "end": []}
        self.setStatus({'filename': url, 'downloadedSize': 0, 'totalSize': 0, 'percent': 0, 'avgSpeed': 0,
                    'currSpeed': 0, 'remainingTime': '0:00:00'})
        self.process = subprocess.Popen(
            [f"exec python {os.path.join(workingDir, 'ulozto-downloader.py')} --auto-captcha --output {path} --id {processId} {url}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, close_fds=True)

    def terminateProcess(self):
        self.process.send_signal(signal.SIGINT)

    def addLine(self, line, y):
        if y == 0:
            if len(self.currentOutput["middle"]) == 0:
                self.currentOutput["start"].append(line)
            else:
                self.currentOutput["end"].append(line)
        else:
            self.currentOutput["middle"][y] = [line]

    def parseLine(line):
        line = line.decode("utf-8")
        y = line.split(" ")[1]
        newLine = " ".join(line.split(" ")[3:])
        return y, newLine

    def read(self):
        if self.currentOutput == {}:
            return ""
        start = "\n".join(self.currentOutput["start"])
        middle = "\n".join(["\n".join(i[1]) for i in sorted(
            list(self.currentOutput["middle"].items()))])
        end = "\n".join(self.currentOutput["end"])
        return f"{datetime.now()}\n{start}\n{middle}\n{end}"

    def input(self, string):
        if self.process != None:
            try:
                self.process.stdin.write(string)
                self.process.stdin.flush()
                self.process.stdin.close()
            except:
                print("pipe is closed")
        else:
            print("process isn't started")

    def setStatus(self, status):
        self.status = status

    def getStatus(self):
        return self.status


app = Flask(__name__)
app.config["SECRET_KEY"] = "WA<+5y/f6dPr-q6s"
jsonReader = JsonReader()
conv = Ansi2HTMLConverter()
processHandlers = {}

path = '/var/www/uld'

try:
    os.chdir(path)
    print("Current working directory: {0}".format(os.getcwd()))
except FileNotFoundError:
    print("Directory: {0} does not exist".format(path))
except NotADirectoryError:
    print("{0} is not a directory".format(path))
except PermissionError:
    print("You do not have permissions to change to {0}".format(path))


@app.route('/', methods=['GET', 'POST'])
def index():
    form = URLForm()
    flashFormErrors(form)
    if form.validate_on_submit():
        jsonReader._instance["defaults"]["url"] = form.url.data
        jsonReader.save()
        return redirect(url_for("startdownload"))

    form.url.data = jsonReader.instance["defaults"]["url"]
    return render_template("index.html", form=form, title="Zadejte adresu souboru")


def generateId():
    import string
    import random
    alphabet = string.ascii_lowercase + string.digits
    id = ''.join(random.choices(alphabet, k=8))
    while id in processHandlers:
        id = ''.join(random.choices(alphabet, k=8))
    return id

@app.route('/download/<id>', methods=['GET', 'POST'])
def download(id):
    if request.method == 'POST':
        if id in processHandlers:
            processHandlers[id].input(request.form["consoleInput"].encode("utf-8"))

    return render_template("download.html", title="Probíhá stahování souboru",
        allowSecond=True, titleSecondary="Console", id=str(id))


@app.route('/startdownload', methods=['GET', 'POST'])
def startdownload():
    url = jsonReader.instance["defaults"]["url"]
    path = jsonReader.instance["paths"][0]

    for p in processHandlers:
        #print(processHandlers[p].url)
        if processHandlers[p].url == url:
            return redirect(url_for("download", id=processHandlers[p].id))

    newId = generateId()
    processHandler = ProcessHandler()
    processHandler.startProcess(url, path, newId)
    processHandlers[newId] = processHandler
    return redirect(url_for("download", id=newId))

@app.route('/cancelDownload/<id>', methods=['GET', 'POST'])
def deleteDownload(id):
    if id in processHandlers:
        processHandlers[id].terminateProcess()
        processHandlers.pop(id)

    return redirect(url_for("index"))


@app.route('/line/<id>', methods=['POST'])
def line(id):
    input_json = request.get_json(force=True)
    processHandlers[id].addLine(f"{id}"+input_json["message"], input_json["y"])
    return ""

@app.route('/status/<id>', methods=['GET', 'POST'])
def status(id):
    if request.method == 'POST':
        input_json = request.get_json(force=True)
        processHandlers[id].setStatus(input_json)
        return ""
    
    return processHandlers[id].getStatus()

@app.route('/status', methods=['GET'])
def status_all():
    result = [a for a in map(lambda v: v.getStatus(), processHandlers.values())]
    return json.dumps(result)

@app.route('/text/<id>', methods=['GET'])
def text(id):
    if id not in processHandlers:
        return "Download id doesn't exists"
    ansi = processHandlers[id].read()
    html = conv.convert(ansi).replace('\\n', '<br>')
    return html


@app.route('/about')
def about():
    return render_template("about.html", title="About")


def flashFormErrors(form):
    for field, errors in form.errors.items():
        for e in errors:
            flash(e, "warning")


if __name__ == "__main__":
    app.run(debug=True)
