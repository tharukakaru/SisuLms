"""Report fixed diagnostic labels only; never print raw provisioning logs."""
import json,re,os
from pathlib import Path
p=Path('/root/sisu-public-provision/creation.log')
if os.name!='posix' or os.geteuid()!=0:raise SystemExit('Run on server as root')
text=p.read_text(errors='replace') if p.is_file() else ''
patterns={
 'database_access_denied':r'Access denied for user|\b1045\b|\b1698\b',
 'database_connection_refused':r'Connection refused|Can.t connect to.*server|\b2003\b',
 'database_host_not_allowed':r'not allowed to connect|\b1130\b',
 'database_create_permission_denied':r'CREATE command denied|\b1044\b',
 'database_already_exists':r'database.*already exists|\b1007\b',
 'site_already_exists':r'[Ss]ite.*already exists',
 'unsupported_cli_option':r'No such option|unrecognized arguments',
 'missing_python_dependency':r'ModuleNotFoundError|ImportError',
 'redis_connection_problem':r'redis.exceptions|Redis.*[Ee]rror',
 'filesystem_permission_denied':r'PermissionError|Permission denied',
 'unsupported_database_version':r'Unsupported.*MariaDB|MariaDB.*not supported',
 'password_prompt_seen':r'(?i)password[^\r\n]*:',
 'user_cancelled':r'Aborted!|KeyboardInterrupt',
 'missing_cli_argument':r'Missing argument|Missing option',
 'site_install_failed':r'An error occurred while installing|Site creation failed',
}
result={label:bool(re.search(pattern,text,re.I)) for label,pattern in patterns.items()}
result['log_present']=p.is_file()
site=Path('/home/sisu/frappe-bench/sites/sisuacademylk.com')
result['site_directory_exists']=site.is_dir()
result['site_config_exists']=(site/'site_config.json').is_file()
result['traceback_present']='Traceback' in text
# Exception class names are identifiers only, not exception text or arguments.
result['exception_types']=sorted(set(re.findall(r'(?m)^((?:[A-Za-z_][A-Za-z0-9_]*\.)*[A-Za-z_][A-Za-z0-9_]*(?:Error|Exception)):',text)))
print(json.dumps(result))
print('Read-only diagnostic. Raw log, passwords and database identifiers withheld.')
