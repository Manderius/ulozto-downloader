from .const import CLI_STATUS_STARTLINE, DOWNPOSTFIX, DOWN_CHUNK_SIZE
from . import utils
from .torrunner import TorRunner
from .segfile import SegFileLoader, SegFileMonitor
from .page import Page
import colors
import requests
import os
import sys
import multiprocessing as mp
import time
from datetime import timedelta, datetime
from types import FunctionType


class Downloader:
    cli_initialized: bool
    terminating: bool
    processes: slice
    captcha_process: mp.Process
    monitor: mp.Process
    captcha_solve_func: FunctionType
    download_url_queue: mp.Queue
    parts: int

    def __init__(self, captcha_solve_func):
        self.captcha_solve_func = captcha_solve_func
        self.cli_initialized = False
        self.monitor = None

    def terminate(self):
        self.terminating = True

        utils._print('Terminating download. Please wait for stopping all processes.')
        if hasattr(self, "captcha_process") and self.captcha_process is not None:
            self.captcha_process.terminate()
        utils._print('Terminate download processes')
        if hasattr(self, "processes") and self.processes is not None:
            for p in self.processes:
                p.terminate()
        utils._print('Download terminated.')
        if hasattr(self, "monitor") and self.monitor is not None:
            self.monitor.terminate()
        utils._print('End download monitor')

    def _captcha_print_func_wrapper(self, text):
        utils.print_captcha_status(text)

    def _captcha_breaker(self, page):
        msg = ""
        if page.isDirectDownload:
            msg = "Solve direct dlink .."
        else:
            msg = "Solve CAPTCHA dlink .."

        for url in self.captcha_download_links_generator:
            # utils.print_captcha_status(msg)
            self.download_url_queue.put(url)

    @staticmethod
    def _save_progress(filename, path, parts, size, interval_sec):

        m = SegFileMonitor(path, utils.print_saved_status, interval_sec)

        t_start = time.time()
        s_start = m.size()
        last_bps = [(s_start, t_start)]

        while True:
            time.sleep(interval_sec)
            s = m.size()
            t = time.time()

            total_bps = (s - s_start) / (t - t_start)

            # Average now bps for last 10 measurements
            if len(last_bps) >= 10:
                last_bps = last_bps[1:]
            (s_last, t_last) = last_bps[0]
            now_bps = (s - s_last) / (t - t_last)
            last_bps.append((s, t))

            remaining = (size - s) / total_bps if total_bps > 0 else 0

            utils.report_saved_status(filename,
                                    (s / 1024 ** 2),
                                    (size / 1024 ** 2),
                                    (s / size * 100),
                                    (total_bps / 1024 ** 2),
                                    (now_bps / 1024 ** 2),
                                    timedelta(seconds=round(remaining)),
                                    parts)


    @staticmethod
    def _download_part(part, download_url_queue):
        """Download given part of the download.

            Arguments:
                part (dict): Specification of the part to download
        """

        id = part.id
        utils.print_part_status(id, "Starting download")

        part.started = time.time()
        part.now_downloaded = 0

        try:
            # Note the stream=True parameter
            r = requests.get(part.download_url, stream=True, allow_redirects=True, headers={
                "Range": "bytes={}-{}".format(part.pfrom + part.downloaded, part.pto),
                "Connection": "close",
            }, timeout=9)
        except Exception:
            part.download_url = download_url_queue.get()
            return Downloader._download_part(part, download_url_queue)

        if r.status_code == 429:
            utils.print_part_status(id, colors.yellow(
                "Status code 429 Too Many Requests returned... will try again in few seconds"))
            time.sleep(5)
            return Downloader._download_part(part, download_url_queue)

        if r.status_code != 206 and r.status_code != 200:
            utils.print_part_status(id, colors.red(
                f"Status code {r.status_code} returned: {part.pfrom + part.downloaded}/{part.pto}"))
            sys.exit(1)

        # reimplement as multisegment write file class
        try:
            for chunk in r.iter_content(chunk_size=DOWN_CHUNK_SIZE):
                if chunk:  # filter out keep-alive new chunks
                    part.write(chunk)
                    part.now_downloaded += len(chunk)
                    elapsed = time.time() - part.started

                    # Print status line downloaded and speed
                    # speed in bytes per second:
                    speed = part.now_downloaded / elapsed if elapsed > 0 else 0
                    # remaining time in seconds:
                    remaining = (part.size - part.downloaded) / speed if speed > 0 else 0

                    utils.print_part_status(id, "{:.2f}%\t{:.2f}/{:.2f} MB\tspeed: {:.2f} KB/s\telapsed: {}\tremaining: {}".format(
                        round(part.downloaded / part.size * 100, 2),
                        round(part.downloaded / 1024**2,
                            2), round(part.size / 1024**2, 2),
                        round(speed / 1024, 2),
                        str(timedelta(seconds=round(elapsed))),
                        str(timedelta(seconds=round(remaining))),
                    ))
        except Exception as ex:
            time.sleep(3)
            return Downloader._download_part(part, download_url_queue)

        # close part file files
        part.close()

        # reuse download link if need
        download_url_queue.put(part.download_url)

    @staticmethod
    def _get_best_parts_amount(sizeBytes):
        import math
        size = sizeBytes / 1024 ** 2
        startup = 3.3
        speed = 0.165
        amount = math.sqrt(size / (startup * speed))
        return math.floor(amount) if size > 10 else 3

    @staticmethod
    def get_expected_time(sizeBytes):
        size = sizeBytes / 1024 ** 2
        startup = 3.3
        speed = 0.165
        amount = Downloader._get_best_parts_amount(sizeBytes)
        return amount * startup + size / amount / speed

    def download(self, url, parts, target_dir=""):
        """Download file from Uloz.to using multiple parallel downloads.
            Arguments:
                url (str): URL of the Uloz.to file to download
                parts (int): Number of parts that will be downloaded in parallel (default: 10)
                target_dir (str): Directory where the download should be saved (default: current directory)
        """
        self.url = url
        self.parts = 0
        self.processes = []
        self.captcha_process = None
        self.target_dir = target_dir
        self.terminating = False
        self.isLimited = False
        self.isCaptcha = False

        started = time.time()
        previously_downloaded = 0

        # 1. Prepare downloads
        utils._print("Starting downloading for url '{}'".format(url))
        # 1.1 Get all needed information
        utils._print("Getting info (filename, filesize, ...)")

        try:
            tor = TorRunner()
            page = Page(url, target_dir, 0, tor)
            page.parse()
            parts = Downloader._get_best_parts_amount(page.size)
            self.parts = parts
            page.parts = parts

        except RuntimeError as e:
            utils._print(colors.red('Cannot download file: ' + str(e)))
            sys.exit(1)

        # Do check - only if .udown status file not exists get question
        output_filename = os.path.join(target_dir, page.filename)
        if os.path.isfile(output_filename) and not os.path.isfile(output_filename+DOWNPOSTFIX):
            utils._print(colors.yellow(
                "WARNING: File '{}' already exists, overwrite it? [y/n] ".format(output_filename)), end="")
            if input().strip() != 'y':
                sys.exit(1)

        if page.quickDownloadURL is not None:
            utils._print("You are VERY lucky, this is QUICK direct download without CAPTCHA, downloading as 1 quick part :)")
            self.download_type = "fullspeed direct download (without CAPTCHA)"
            download_url = page.quickDownloadURL
            self.captcha_solve_func = None

        if page.slowDownloadURL is not None:
            self.isLimited = True
            if page.isDirectDownload:
                utils._print("You are lucky, this is slow direct download without CAPTCHA :)")
                self.download_type = "slow direct download (without CAPTCHA)"
            else:
                self.isCaptcha = True
                utils._print(
                    "CAPTCHA protected download - CAPTCHA challenges will be displayed\n")
                self.download_type = "CAPTCHA protected download"
            self.captcha_download_links_generator = page.captcha_download_links_generator(
                captcha_solve_func=self.captcha_solve_func,
                print_func=self._captcha_print_func_wrapper
            )
            download_url = next(self.captcha_download_links_generator)

        head = requests.head(download_url, allow_redirects=True)
        total_size = int(head.headers['Content-Length'])
        try:
            file_data = SegFileLoader(output_filename, total_size, parts)
            downloads = file_data.make_writers()
        except Exception as e:
            utils._print(colors.red(
                f"Failed: Can not create '{output_filename}' error: {e} "))
            self.terminate()
            sys.exit()

        # 2. Initialize cli status table interface
        # if windows, use 'cls', otherwise use 'clear'
        # os.system('cls' if os.name == 'nt' else 'clear')
        self.cli_initialized = True
        page.cli_initialized = True  # for tor in Page
        utils._print(colors.blue("File:\t\t") + colors.bold(page.filename), y=1)
        utils._print(colors.blue("URL:\t\t") + page.url, y=2)
        utils._print(colors.blue("Download type:\t") + self.download_type, y=3)
        utils._print(colors.blue("Size / parts: \t") +
              colors.bold(f"{round(total_size / 1024**2, 2)}MB => " +
              f"{file_data.parts} x {round(file_data.part_size / 1024**2, 2)}MB"), y=4)
        utils._print(colors.blue("Start time: \t") + datetime.now().strftime("%H:%M"),  y=5)
        utils._print(colors.blue("Estimated download time: ") + str(timedelta(seconds=round(Downloader.get_expected_time(total_size) * 1.05))), y=6)

        # fill placeholder before download started
        # for part in downloads:
        #     if page.isDirectDownload:
        #         utils.print_part_status(part.id, "Waiting for direct link...")
        #     else:
        #         utils.print_part_status(part.id, "Waiting for CAPTCHA...")

        # Prepare queue for recycling download URLs
        self.download_url_queue = mp.Queue(maxsize=0)

        # limited must use TOR and solve links or captcha
        if self.isLimited:
            # Reuse already solved links
            self.download_url_queue.put(download_url)

            # Start CAPTCHA breaker in separate process
            self.captcha_process = mp.Process(
                target=self._captcha_breaker, args=(page,)
            )

        cpb_started = False
        page.alreadyDownloaded = 0

        # save status monitor
        self.monitor = mp.Process(target=Downloader._save_progress, args=(
            page.filename, file_data.filename, file_data.parts, file_data.size, 1))
        self.monitor.start()

        # 3. Start all downloads fill self.processes
        for part in downloads:
            if self.terminating:
                return
            id = part.id

            if part.downloaded == part.size:
                utils.print_part_status(id, colors.green(
                    "Already downloaded from previous run, skipping"))
                page.alreadyDownloaded += 1
                continue

            if self.isLimited:
                if not cpb_started:
                    self.captcha_process.start()
                    cpb_started = True
                part.download_url = self.download_url_queue.get()
            else:
                part.download_url = download_url

            # Start download process in another process (parallel):
            p = mp.Process(target=Downloader._download_part,
                           args=(part, self.download_url_queue))
            p.start()
            self.processes.append(p)

        if self.isLimited:
            # no need for another CAPTCHAs
            self.captcha_process.terminate()
            if self.isCaptcha:
                utils.print_captcha_status(
                    "All downloads started, no need to solve another CAPTCHAs..")
            else:
                utils.print_captcha_status(
                    "All downloads started, no need to solve another direct links..")

        # 4. Wait for all downloads to finish
        success = True
        for p in self.processes:
            p.join()
            if p.exitcode != 0:
                success = False

        # result end status
        if not success:
            utils._print(colors.red("Failure of one or more downloads, exiting"))
            sys.exit(1)

        elapsed = time.time() - started
        # speed in bytes per second:
        speed = (total_size - previously_downloaded) / elapsed if elapsed > 0 else 0
        utils._print(colors.green("All downloads finished"))
        utils._print("Stats: Downloaded {}{} MB in {} (average speed {} MB/s)".format(
            round((total_size - previously_downloaded) / 1024**2, 2),
            "" if previously_downloaded == 0 else (
                "/"+str(round(total_size / 1024**2, 2))
            ),
            str(timedelta(seconds=round(elapsed))),
            round(speed / 1024**2, 2)
        ))
        utils.report_saved_status(page.filename, total_size / 1024**2, total_size / 1024**2, 100, round(speed / 1024**2, 2), 0, 'Hotovo', self.parts)
        # remove resume .udown file
        udown_file = output_filename + DOWNPOSTFIX
        if os.path.exists(udown_file):
            utils._print(f"Delete file: {udown_file}")
            os.remove(udown_file)
        ucache_file = page.linkCache.cachefile
        if os.path.exists(ucache_file):
            utils._print(f"Delete file: {ucache_file}")
            os.remove(ucache_file)
