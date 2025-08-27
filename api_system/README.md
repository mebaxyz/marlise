
(r"/system/info", SystemInfo),
class SystemInfo(JsonRequestHandler):
    def get(self):
        hwdesc = get_hardware_descriptor()
        uname  = os.uname()

        if os.path.exists("/etc/mod-release/system"):
            with open("/etc/mod-release/system") as fh:
                sysdate = fh.readline().replace("generated=","").split(" at ",1)[0].strip()
        else:
            sysdate = "Unknown"

        info = {
            "hwname": hwdesc.get('name', "Unknown"),
            "architecture": hwdesc.get('architecture', "Unknown"),
            "cpu": MODEL_CPU or hwdesc.get('cpu', "Unknown"),
            "platform": hwdesc.get('platform', "Unknown"),
            "bin_compat": hwdesc.get('bin-compat', "Unknown"),
            "model": MODEL_TYPE or hwdesc.get('model', "Unknown"),
            "sysdate": sysdate,
            "python": {
                "version" : sys.version
            },
            "uname": {
                "machine": uname.machine,
                "release": uname.release,
                "sysname": uname.sysname,
                "version": uname.version
            }
        }
        self.write(info)

(r"/system/cleanup", SystemCleanup),
class SystemCleanup(JsonRequestHandler):
    @gen.coroutine
    def post(self):
        banks       = bool(int(self.get_argument('banks')))
        favorites   = bool(int(self.get_argument('favorites')))
        hmiSettings = bool(int(self.get_argument('hmiSettings')))
        licenseKeys = bool(int(self.get_argument('licenseKeys')))
        pedalboards = bool(int(self.get_argument('pedalboards')))
        plugins     = bool(int(self.get_argument('plugins')))

        if hmiSettings and not get_hardware_descriptor().get('hmi_eeprom', False):
            hmiSettings = False

        stuffToDelete = []

        if banks:
            stuffToDelete.append(USER_BANKS_JSON_FILE)

        if favorites:
            stuffToDelete.append(FAVORITES_JSON_FILE)

        if licenseKeys:
            stuffToDelete.append(KEYS_PATH)

        if pedalboards:
            stuffToDelete.append(LV2_PEDALBOARDS_DIR)

        if plugins:
            stuffToDelete.append(LV2_PLUGIN_DIR)

        if not stuffToDelete and not hmiSettings:
            self.write({
                'ok'   : False,
                'error': "Nothing to delete",
            })
            return

        if hmiSettings:
            # NOTE this will desync HMI, but we always restart ourselves at the end
            SESSION.hmi.reset_eeprom(None)
            yield gen.Task(SESSION.hmi.ping)
            yield gen.Task(run_command, ["hmi-reset"], None)

        if plugins:
            yield gen.Task(run_command, ["systemctl", "stop", "jack2"], None)

        yield gen.Task(run_command, ["rm", "-rf"] + stuffToDelete, None)
        os_sync()

        self.write({
            'ok'   : True,
            'error': "",
        })

        restartJACK2 = pedalboards or plugins
        IOLoop.instance().add_callback(restart_services, restartJACK2, True)


(r"/system/prefs", SystemPreferences),
class SystemPreferences(JsonRequestHandler):
    OPTION_NULL            = 0
    OPTION_FILE_EXISTS     = 1
    OPTION_FILE_NOT_EXISTS = 2
    OPTION_FILE_CONTENTS   = 3

    def __init__(self, application, request, **kwargs):
        JsonRequestHandler.__init__(self, application, request, **kwargs)

        self.prefs = []

        self.make_pref("bluetooth_name", self.OPTION_FILE_CONTENTS, "/data/bluetooth/name", str)
        self.make_pref("jack_mono_copy", self.OPTION_FILE_EXISTS, "/data/jack-mono-copy")
        self.make_pref("jack_sync_mode", self.OPTION_FILE_EXISTS, "/data/jack-sync-mode")
        self.make_pref("jack_256_frames", self.OPTION_FILE_EXISTS, "/data/using-256-frames")
        self.make_pref("separate_spdif_outs", self.OPTION_FILE_EXISTS, "/data/separate-spdif-outs")

        # Optional services
        self.make_pref("service_mod_peakmeter", self.OPTION_FILE_NOT_EXISTS, "/data/disable-mod-peakmeter")
        self.make_pref("service_mod_sdk", self.OPTION_FILE_EXISTS, "/data/enable-mod-sdk")
        self.make_pref("service_netmanager", self.OPTION_FILE_EXISTS, "/data/enable-netmanager")

        # Workarounds
        self.make_pref("autorestart_hmi", self.OPTION_FILE_EXISTS, "/data/autorestart-hmi")

    def make_pref(self, label, otype, data, valtype=None, valdef=None):
        self.prefs.append({
            "label": label,
            "type" : otype,
            "data" : data,
            "valtype": valtype,
            "valdef" : valdef,
        })

    def get(self):
        ret = {}

        for pref in self.prefs:
            if pref['type'] == self.OPTION_FILE_EXISTS:
                val = os.path.exists(pref['data'])

            elif pref['type'] == self.OPTION_FILE_NOT_EXISTS:
                val = not os.path.exists(pref['data'])

            elif pref['type'] == self.OPTION_FILE_CONTENTS:
                if os.path.exists(pref['data']):
                    with open(pref['data'], 'r') as fh:
                        val = fh.read().strip()
                    try:
                        val = pref['valtype'](val)
                    except:
                        val = pref['valdef']
                else:
                    val = pref['valdef']
            else:
                pass

            ret[pref['label']] = val

        self.write(ret)



            
(r"/system/exechange", SystemExeChange),

class SystemExeChange(JsonRequestHandler):
    @gen.coroutine
    def post(self):
        etype = self.get_argument('type')
        finished = False

        if etype == "command":
            cmd = self.get_argument('cmd').split(" ",1)
            if len(cmd) == 1:
                cmd = cmd[0]
            else:
                cmd, cdata = cmd

            if cmd == "reboot":
                yield gen.Task(run_command, ["hmi-reset"], None)
                IOLoop.instance().add_callback(self.reboot)

            elif cmd == "restore":
                IOLoop.instance().add_callback(start_restore)

            elif cmd == "backup-export":
                args  = ["mod-backup", "backup"]
                cdata = cdata.split(",")
                if cdata[0] == "1":
                    args.append("-d")
                if cdata[1] == "1":
                    args.append("-p")
                resp  = yield gen.Task(run_command, args, None)
                error = resp[2].decode("utf-8", errors="ignore").strip()
                if len(error) > 1:
                    error = error[0].title()+error[1:]+"."
                self.write({
                    'ok'   : resp[0] == 0,
                    'error': error,
                })
                return

            elif cmd == "backup-import":
                args  = ["mod-backup", "restore"]
                cdata = cdata.split(",")
                if cdata[0] == "1":
                    args.append("-d")
                if cdata[1] == "1":
                    args.append("-p")
                resp = yield gen.Task(run_command, args, None)
                error = resp[2].decode("utf-8", errors="ignore").strip()
                if len(error) > 1:
                    error = error[0].title()+error[1:]+"."
                self.write({
                    'ok'   : resp[0] == 0,
                    'error': error,
                })
                if resp[0] == 0:
                    IOLoop.instance().add_callback(restart_services, True, False)
                return

            else:
                self.write(False)
                return

        elif etype == "filecreate":
            path   = self.get_argument('path')
            create = bool(int(self.get_argument('create')))

            if path not in ("autorestart-hmi",
                            "jack-mono-copy",
                            "jack-sync-mode",
                            "separate-spdif-outs",
                            "using-256-frames"):
                self.write(False)
                return

            filename = "/data/" + path

            if create:
                foldername = os.path.dirname(filename)
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                with open(filename, 'wb') as fh:
                    fh.write(b"")
            elif os.path.exists(filename):
                os.remove(filename)

        elif etype == "filewrite":
            path    = self.get_argument('path')
            content = self.get_argument('content').strip()

            if path not in ("bluetooth/name",):
                self.write(False)
                return

            filename = "/data/" + path

            if content:
                foldername = os.path.dirname(filename)
                if not os.path.exists(foldername):
                    os.makedirs(foldername)
                with open(filename, 'w') as fh:
                    fh.write(content)
            elif os.path.exists(filename):
                os.remove(filename)

        elif etype == "service":
            name       = self.get_argument('name')
            enable     = bool(int(self.get_argument('enable')))
            inverted   = bool(int(self.get_argument('inverted')))
            persistent = bool(int(self.get_argument('persistent')))

            if name not in ("hmi-update", "mod-peakmeter", "mod-sdk", "netmanager"):
                self.write(False)
                return

            if inverted:
                checkname = "/data/disable-" + name
            else:
                checkname = "/data/enable-" + name

            if name == "netmanager":
                servicename = "jack-netmanager"
            else:
                servicename = name

            if persistent:
                if enable:
                    with open(checkname, 'wb') as fh:
                        fh.write(b"")
                else:
                    if os.path.exists(checkname):
                        os.remove(checkname)

            if inverted:
                enable = not enable

            if enable:
                if name == "hmi-update":
                    self.write(True)
                    finished = True
                yield gen.Task(run_command, ["systemctl", "start", servicename], None)

            else:
                yield gen.Task(run_command, ["systemctl", "stop", servicename], None)

        if not finished:
            os_sync()
            self.write(True)

    @gen.coroutine
    def reboot(self):
        os_sync()
        yield gen.Task(run_command, ["reboot"], None)

(r"/update/download/", UpdateDownload),             # Migration Admin Gov

class UpdateDownload(MultiPartFileReceiver):
    destination_dir = "/tmp/os-update"

    def process_file(self, basename, callback=lambda:None):
        self.sfr_callback = callback

        # TODO: verify checksum?
        src = os.path.join(self.destination_dir, basename)
        dst = UPDATE_MOD_OS_FILE
        run_command(['mv', src, dst], None, self.move_file_finished)

    def move_file_finished(self, resp):
        os_sync()
        self.result = True
        self.sfr_callback()
(r"/update/begin", UpdateBegin),                    # Migration Admin Gov

class UpdateBegin(JsonRequestHandler):
    @web.asynchronous
    @gen.engine
    def post(self):
        if not os.path.exists(UPDATE_MOD_OS_FILE):
            self.write(False)
            return

        with open(UPDATE_MOD_OS_HERLPER_FILE, 'wb') as fh:
            fh.write(b"")

        IOLoop.instance().add_callback(start_restore)
        self.write(True)

(r"/package/uninstall", PackageUninstall),
class PackageUninstall(JsonRequestHandler):
    @web.asynchronous
    @gen.engine
    def post(self):
        bundles = json.loads(self.request.body.decode("utf-8", errors="ignore"))
        error   = ""
        removed = []

        print("asked to remove these:", bundles)

        for bundlepath in bundles:
            if os.path.exists(bundlepath) and os.path.isdir(bundlepath):
                if not os.path.abspath(bundlepath).startswith(LV2_PLUGIN_DIR):
                    error = "bundlepath '{}' is not in LV2_PATH".format(bundlepath)
                    break

                resp, data = yield gen.Task(SESSION.host.remove_bundle, bundlepath, True, None)

                if resp:
                    removed += data
                    shutil.rmtree(bundlepath)
                else:
                    error = data
                    break
            else:
                print("bundlepath is non-existent:", bundlepath)

        if error:
            resp = {
                'ok'     : False,
                'error'  : error,
                'removed': removed,
            }
        elif len(removed) == 0:
            resp = {
                'ok'     : False,
                'error'  : "No plugins found",
                'removed': [],
            }
        else:
            resp = {
                'ok'     : True,
                'removed': removed,
            }

        if len(removed) > 0:
            # Re-save banks and reset cache, as pedalboards might contain the removed plugins
            broken = get_broken_pedalboards()
            if len(broken) > 0:
                list_banks(broken)
                reset_get_all_pedalboards_cache(kPedalboardInfoBoth)

        self.write(resp)



        