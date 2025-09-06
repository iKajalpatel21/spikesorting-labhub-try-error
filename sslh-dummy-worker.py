import json, time, os, sys, requests, logging
import importlib
import urllib3
import time

# importing sslh-cli
import importlib

sslh_cli = importlib.import_module("sslh-cli")

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Changing schema for a worker
# 1. it mast have job_id
if ">job_id" in sslh_cli.JOB_CONFIG:
    del sslh_cli.JOB_CONFIG[">job_id"]
sslh_cli.JOB_CONFIG["*job_id"] = str
# 2. it mast have SI version to ensure server and worker have the same version of SI
if ">si" in sslh_cli.JOB_CONFIG:
    del sslh_cli.JOB_CONFIG[">si"]
sslh_cli.JOB_CONFIG["*si"] = str
# 3. it mast set log level
if ">log_level" in sslh_cli.JOB_CONFIG["*job_evn"]:
    del sslh_cli.JOB_CONFIG["*job_evn"][">log_level"]
sslh_cli.JOB_CONFIG["*job_evn"]["*log_level"] = str
# 4. it mast redirect logs to the NAS
if ">REDIRECT" in sslh_cli.JOB_CONFIG["*job_evn"]:
    del sslh_cli.JOB_CONFIG["*job_evn"][">REDIRECT"]
sslh_cli.JOB_CONFIG["*job_evn"]["*REDIRECT"] = {"*log": str, "*out": str, "*err": str}


# Load configuration from JSON file
def validate_config(conf: dict) -> (dict, str):
    x = sslh_cli.check_schema_an_enry(
        conf,
        {
            "*SERVER": str,
            "*SSH_KEY": str,
            "*NAS": str,
            "*LOCAL": str,
            "*TIMEOUT": int,
            "*API_TOKEN": str,
            "*VERIFY_SSL": (str, bool),
            "*JOB_SAVE": bool,
        },
    )
    if x == 0:
        return conf
    return x


# REST status update call to mark job status 'completed' or 'failed'
def mark_status(
    job_id: str,
    step_id: (str, None),
    status: str,
    api_url: str = "",
    headers: dict = {},
    verify: (str, bool) = "",
    timeout: int = 10,
):
    requests.post(
        f"{api_url}/status/",  # Endpoint from urls.py
        headers=headers,
        json={"job_id": job_id, "step_id": step_id, "status": status},
        verify=verify,
        timeout=timeout,
    )


def run_the_job(config: dict, job_conf, api: (dict, None)):
    x = sslh_cli.base_check(job_conf)
    if x != 0:
        return f"Base Configuration Checkout fails :{x}"

    # x = sslh_cli.job_sanity_check(job_conf)
    # logging.debug(f"--->JOB Sanity: {x}")
    # if x != 0:
    # logging.error(f'Config did not pass sanity check: {x}')
    # return f'Config did not pass sanity check:\n   {x}'

    # Main job loop
    job_id = job_conf["job_id"]
    logging.info(f"Job {job_id} runs")
    if not api is None:
        mark_status(job_id, None, "running", **api)
    for step in job_conf["job_steps"]:
        function = step["function"]
        identifier = step["identifier"]
        depends = step["depends"]
        if not api is None:
            mark_status(job_id, identifier, "running", **api)
        logging.info(f" > Step: {function}:{identifier} runs")
        time.sleep(20)  # kind of doing the job
        logging.info(f" > Step: {function}:{identifier} finished")
        if not api is None:
            mark_status(job_id, identifier, "completed", **api)
    logging.info(f"Job {job_id} Finished")
    if not api is None:
        mark_status(job_id, None, "completed", **api)
    return 0


# Worker loop
def main(config: dict):
    api_url = config["SERVER"]
    headers = {"Authorization": f"Token {config['API_TOKEN']}"}
    poll_interval = config.get("TIMEOUT", 10)
    timeout = config.get("TIMEOUT", 10)
    VERIFY_SSL = config.get("VERIFY_SSL", True)

    sys.stderr.write("[Worker] Starting REST-based polling loop")

    job_config = None  # Track currently running job

    try:
        while True:
            try:
                # Fetch the next job from the server
                res = requests.get(
                    f"{api_url}/next-job/",
                    headers=headers,
                    verify=VERIFY_SSL,
                    timeout=timeout,
                )
                if res.status_code == 200:
                    job_config = res.json()
                    sys.stderr.write(f"\n[Worker] Fetched Job {job_config} from API\n")
                    x = run_the_job(
                        config,
                        job_config,
                        {"api_url": api_url, "headers": headers, "verify": VERIFY_SSL},
                    )
                    if x != 0:
                        sys.stderr.write("[Worker] Job failed\n")
                    else:
                        sys.stderr.write("[Worker] Finished job...\n")
                        job_config = None
                        time.sleep(poll_interval)
                elif res.status_code == 204:
                    sys.stderr.write("[Worker] No job found. Sleeping...\n")
                    time.sleep(poll_interval)
                else:
                    sys.stderr.write(f"[Worker] API error: {res.status_code}\n")
                    time.sleep(5)

            except Exception as e:
                sys.stderr.write(f"[Worker] General error: {e}\n")
                time.sleep(5)

    except KeyboardInterrupt:
        sys.stderr.write("[Worker] Worker interrupted.\n")
        if job_config is not None:
            sys.stderr.write(
                f"[Worker] Current job {job_config} may be incomplete. Backend will handle recovery.\n"
            )
        sys.stderr.write("[Worker] Exiting gracefully.\n")


if __name__ == "__main__":
    default_config = {
        "SERVER": "localhost:8443/job_queue",
        "SSH_KEY": "",
        "NAS": "/local/sslh-worker/fake-nas",
        "LOCAL": "/local/sslh-worker/testworkspace",
        "TIMEOUT": 10,
        "API_TOKEN": "",
        "VERIFY_SSL": False,
        "JOB_SAVE": False,
    }

    from optparse import OptionParser

    oprs = OptionParser("USAGE: %prog [options]")
    oprs.add_option(
        "-c",
        "--configuration-file",
        dest="config_path",
        default=None,
        type="str",
        help="sets a path to the worker configuration (default None)",
    )
    oprs.add_option(
        "-u",
        "--server-url",
        dest="SERVER",
        default=None,
        type="str",
        help="server URL (default `{}`)".format(default_config["SERVER"]),
    )
    oprs.add_option(
        "--ssh-key",
        dest="SSH_KEY",
        default=None,
        type="str",
        help="path to ssh key (default `{}`)".format(default_config["SSH_KEY"]),
    )
    oprs.add_option(
        "--NAS",
        dest="NAS",
        default=None,
        type="str",
        help="path to NAS (default `{}`)".format(default_config["NAS"]),
    )
    oprs.add_option(
        "--local",
        dest="LOCAL",
        default=None,
        type="str",
        help="path to local working directory (default `{}`)".format(
            default_config["LOCAL"]
        ),
    )
    oprs.add_option(
        "-T",
        "--timeout",
        dest="TIMEOUT",
        default=None,
        type="int",
        help="timeout between server requests (default `{}`)".format(
            default_config["TIMEOUT"]
        ),
    )
    oprs.add_option(
        "-A",
        "--API-token",
        dest="API_TOKEN",
        default=None,
        type="int",
        help="timeout between server requests (default `{}`)".format(
            default_config["API_TOKEN"]
        ),
    )
    oprs.add_option(
        "-V",
        "--verify-certificate",
        dest="VERIFY_SSL",
        default=None,
        type="int",
        help="key to verify certificate (default `{}`)".format(
            default_config["VERIFY_SSL"]
        ),
    )
    oprs.add_option(
        "--save-job",
        dest="JOB_SAVE",
        default=None,
        action="store_true",
        help="leave job on local directory (default `{}`)".format(
            default_config["JOB_SAVE"]
        ),
    )

    opts, args = oprs.parse_args()
    if opts.config_path is None:
        config = default_config
    else:
        try:
            with open(opts.config_path) as fd:
                config = json.load(fd)
        except BaseException as e:
            sys.stderr.write(f"[Worker] Cannot load `{opts.config_path}` : {e}\n")
            exit(1)
        for v in default_config:
            if not v in config:
                config[v] = default_config[v]
    opts = vars(opts)
    for v in default_config:
        if not opts[v] is None:
            config[v] = opts[v]

    config = validate_config(config)
    if type(config) is str:
        sys.stderr.write(
            f"[Worker] configuration did not pass validation: `{config}` \n"
        )
        exit(1)

    main(config)
