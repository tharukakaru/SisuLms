"""Install this working source into the dedicated Ubuntu sandbox only."""
from pathlib import Path
import shutil
import subprocess


def main():
    bench = Path.home() / 'sisu-hnb-sandbox-bench'
    if Path.cwd().resolve() != bench.resolve():
        raise SystemExit('Run from ~/sisu-hnb-sandbox-bench only.')
    source = Path(__file__).resolve().parents[1]
    target = bench / 'apps' / 'institute_lms'
    if target.exists():
        raise SystemExit('Destination already exists; stopped without overwriting it.')
    if not (source / 'institute_lms' / 'cybersource.py').is_file():
        raise SystemExit('CyberSource working source missing.')
    target.mkdir()
    for name in ('institute_lms', 'frontend', 'scripts', 'tests', 'docs'):
        shutil.copytree(source / name, target / name,
                        ignore=shutil.ignore_patterns('node_modules', '__pycache__', '*.pyc',
                                                     '.env', '.env.*', '*.p12', '*.pfx'))
    for name in ('pyproject.toml', 'package.json', 'README.md', 'LICENSE', '.gitignore'):
        shutil.copy2(source / name, target / name)
    subprocess.run([str(bench / 'env/bin/python'), '-m', 'pip', 'install', '-e', str(target)], check=True)
    subprocess.run(['npm', 'ci'], cwd=target / 'frontend', check=True)
    app_list = bench / 'sites/apps.txt'
    apps = app_list.read_text().splitlines()
    if 'institute_lms' not in apps:
        app_list.write_text('\n'.join(apps + ['institute_lms']) + '\n')
    subprocess.run(['bench', 'build', '--app', 'institute_lms'], cwd=bench, check=True)
    print('PASS: SISU CyberSource working source installed and built in sandbox only.')
    print('No site/database created, credentials copied, or payments enabled.')


if __name__ == '__main__':
    main()
