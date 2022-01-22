import json
import os
import subprocess
import sys

from ansi2html import Ansi2HTMLConverter
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import (BooleanField, IntegerField, SelectField, StringField,
                     SubmitField)
from wtforms.validators import InputRequired
from datetime import datetime

class URLForm(FlaskForm):
    url = StringField("", [InputRequired()])
    parts = IntegerField('Počet částí', [InputRequired()])
    autoCaptcha = BooleanField('Povolte automatické čtení CAPTCHA')
    path = SelectField("Výběr pořadí", [InputRequired()])
    submit = SubmitField("Submit")


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
        print(os.getcwd())
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
    process = None
    currentOutput = {"start":[], "middle":{}, "end":[]}
    started = False

    def startProcess(self, url, parts, captcha=True):
        workingDir = os.path.abspath(os.path.dirname(__file__))
        self.currentOutput = {"start":[], "middle":{}, "end":[]}
        self.process = subprocess.Popen([f"python {os.path.join(workingDir, 'ulozto-downloader.py')} --auto-captcha --parts {parts} {url}"],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, close_fds=True)

    def addLine(self, line, y):
        if y == 0:
            if len(self.currentOutput["middle"]) == 0:
                self.currentOutput["start"].append(line)
            else:
                self.currentOutput["end"].append(line)
        else:
            if y not in self.currentOutput["middle"] or y > 0:
                self.currentOutput["middle"][y] = [line]
            else:
                self.currentOutput["middle"][y].append(line)

    def parseLine(line):
        line = line.decode("utf-8")
        y = line.split(" ")[1]
        newLine = " ".join(line.split(" ")[3:])
        return y, newLine

    def read(self):
        if self.currentOutput == {}: return ""
        start = "\n".join(self.currentOutput["start"])
        middle = "\n".join(["\n".join(i[1]) for i in sorted(list(self.currentOutput["middle"].items()))])
        end = "\n".join(self.currentOutput["end"])
        return f"{datetime.now()}\n{start}\n{middle}\n{end}"


app = Flask(__name__)
app.config["SECRET_KEY"] = "WA<+5y/f6dPr-q6s"
jsonReader = JsonReader()
conv = Ansi2HTMLConverter()
processHandler = ProcessHandler()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = URLForm()
    setChoices(form)
    flashFormErrors(form)
    if form.validate_on_submit():
        jsonReader._instance["defaults"]["url"] = form.url.data
        jsonReader._instance["defaults"]["auto-captcha"] = form.autoCaptcha.data
        jsonReader._instance["defaults"]["parts"] = form.parts.data
        jsonReader._instance["defaults"]["pathID"] = int(form.path.data)
        jsonReader.save()
        return redirect(url_for("download"))

    form.url.data = jsonReader.instance["defaults"]["url"]
    form.autoCaptcha.data = jsonReader.instance["defaults"]["auto-captcha"]
    form.parts.data = jsonReader.instance["defaults"]["parts"]
    return render_template("index.html", form=form, title="Zadejte data")

def setChoices(form):
    defaultID = jsonReader.instance["defaults"]["pathID"]
    paths = jsonReader.instance["paths"]
    form.path.choices = [(i, paths[i])
                         for i in range(len(paths)) if i != defaultID]
    if defaultID != "":
        form.path.choices = [(defaultID, paths[defaultID])]+form.path.choices

@app.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        if processHandler.process != None:
            try:
                processHandler.process.stdin.write(request.form["consoleInput"].encode("utf-8"))
                processHandler.process.stdin.flush()
                processHandler.process.stdin.close()
                print(request.form["consoleInput"], request.form["consoleInput"].encode("utf-8"))
            except:
                print("pipe is closed")

    parts = jsonReader.instance["defaults"]["parts"]
    url = jsonReader.instance["defaults"]["url"]

    if not processHandler.started:
        processHandler.startProcess(url, parts)
        processHandler.started = True

    return render_template("download.html", title="Probíhá stahování souboru", parts=parts, allowSecond=True, titleSecondary="Console")

@app.route('/line', methods=['POST'])
def line():
    input_json = request.get_json(force=True)
    processHandler.addLine(input_json["message"], input_json["y"])
    return ""

@app.route('/text', methods=['GET'])
def text():
    ansi = processHandler.read()
    html = conv.convert(ansi).replace('\\n','<br>')
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
