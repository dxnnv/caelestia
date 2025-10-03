import signal
import subprocess
from argparse import Namespace

from caelestia.utils.paths import c_cache_dir


def filter_log(lines, *, end="\n"):
    for line in lines:
        if f"Cannot open: file://{c_cache_dir}/imagecache/" not in line:
            print(line, end, flush=True)


class Command:
    args: Namespace

    def __init__(self, args: Namespace) -> None:
        self.args = args

    def run(self) -> None:
        if self.args.show:
            ipc = self.shell("ipc", "show").replace("target ", "").replace("function ", "")
            print(ipc, end="")
            return

        if self.args.log:
            args = ["log"]
            if self.args.log_rules:
                args += ["-r", self.args.log_rules]
            filter_log(self.shell(*args).splitlines(True), end="")
            return

        if self.args.kill:
            # Kill the shell
            self.shell("kill")
            return

        if self.args.message:
            print(self.shell("ipc", "call", *self.args.message), end="")
            return

        # Start the shell
        args = ["qs", "-c", "caelestia", "-n"]
        if self.args.log_rules:
            args += ["--log-rules", self.args.log_rules]

        if self.args.daemon:
            subprocess.run(args, check=True)
            return

        shell = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        try:
            if shell.stdout is not None:
                filter_log(iter(shell.stdout.readline, ""), end="")
            shell.wait()
        except KeyboardInterrupt:
            try:
                shell.send_signal(signal.SIGINT)
            except Exception:
                pass
        finally:
            if shell.poll() is None:
                shell.terminate()
                try:
                    shell.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    shell.kill()

    def shell(self, *args: str) -> str:
        return subprocess.check_output(["qs", "-c", "caelestia", *args], text=True)
