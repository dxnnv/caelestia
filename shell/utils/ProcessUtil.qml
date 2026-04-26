pragma Singleton

import QtQuick
import Quickshell

QtObject {
    /**
     * Run a command and return a Promise<{ code, stdout, stderr }>.
     * args: string[]
     * opts: { cwd?: string, env?: var (object map), input?: string, mergeStderr?: bool }
     */
    function run(args, opts) {
        opts = opts || {};
        return new Promise(resolve => {
            const proc = Qt.createQmlObject('import Quickshell; Process { }', this);
            const out = Qt.createQmlObject('import Quickshell; StdioCollector {}', proc);
            const err = Qt.createQmlObject('import Quickshell; StdioCollector {}', proc);

            proc.command = args;
            if (opts.cwd)
                proc.workingDirectory = opts.cwd;
            if (opts.env)
                proc.environment = opts.env;
            if (opts.mergeStderr === true)
                proc.redirectStderrToStdout = true;

            proc.stdout = out;
            proc.stderr = err;

            if (opts.input !== undefined && opts.input !== null)
                proc.stdinText = String(opts.input);

            let outDone = false, errDone = false, exited = false;
            let exitCode = null;

            function tryFinish() {
                if (outDone && errDone && exited) {
                    const result = {
                        code: exitCode,
                        stdout: out.text,
                        stderr: err.text
                    };
                    out.destroy();
                    err.destroy();
                    proc.destroy();
                    resolve(result);
                }
            }

            out.onStreamFinished.connect(() => {
                outDone = true;
                tryFinish();
            });
            err.onStreamFinished.connect(() => {
                errDone = true;
                tryFinish();
            });

            proc.onFinished.connect(code => {
                exitCode = code;
                exited = true;
                tryFinish();
            });

            proc.running = true;
        });
    }

    /** Run command with options via `bash -lc`*/
    function sh(cmd, opts) {
        return run(["bash", "-lc", cmd], opts);
    }

    /** Run command with options, throw on non-zero, and return stdout string */
    function must(args, opts) {
        return run(args, opts).then(r => {
            if (r.code !== 0)
                throw new Error(`Process failed (${r.code}): ${r.stderr || r.stdout}`);
            return r.stdout;
        });
    }

    /** Run command with options via `bash -lc`, throw on non-zero, and return stdout string */
    function requireSh(cmd, opts) {
        return must(["bash", "-lc", cmd], opts);
    }
}
