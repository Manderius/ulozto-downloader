import sys
import colors
from . import const
import requests

class ProcessID():
    id = None

def _print(text, x=0, y=0):
    dictToSend = {'message':text, "y":y, "x":x}
    _send_post(f'line/{ProcessID.id}', dictToSend, (0.2, 0.2))

def _send_post(relative_url, json, timeout=(1, 1)):
    try:
        return requests.post(f'http://localhost:5000/{relative_url}', json=json, timeout=timeout)
    except:
        return None

def print_part_status(id, text):
    #_print(colors.blue(f"[Part {id}]") + f"\t{text}", y=(id + const.CLI_STATUS_STARTLINE))
    pass


def print_captcha_status(text):
    _print(colors.yellow("[Link solve]") +
           f"\t{text}", y=(const.CLI_STATUS_STARTLINE + 2))


def print_tor_status(text, parts):
    _print(colors.yellow("[Tor  start]") +
           f"\t{text}", y=(const.CLI_STATUS_STARTLINE + 1))


def print_saved_status(text, parts):
    _print(colors.yellow(f"[Progress]\t{text}"),
           y=(const.CLI_STATUS_STARTLINE + 3))

def report_saved_status(filename, size, totalSize, percent, averageSpeed, currentSpeed, remainingTime, numParts):
    print_saved_status(
        f"{size:.2f} MB"
        f" ({percent:.2f}) %"
        f"\tavg. speed: {averageSpeed:.2f} MB/s"
        f"\tcurr. speed: {currentSpeed:.2f} MB/s"
        f"\tremaining: {remainingTime}",
        numParts
    )
    dictToSend = {'id': ProcessID.id, 'filename': filename, 'downloadedSize': size, 'totalSize': totalSize, 'percent': percent, 'avgSpeed': averageSpeed,
                    'currSpeed': currentSpeed, 'remainingTime': str(remainingTime)}
    _send_post(f'status/{ProcessID.id}', dictToSend)

