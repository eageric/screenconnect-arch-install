#!/usr/bin/env python3
"""Extract the technician payload without executing any vendor installer."""
import io
import re
import sys
import tarfile
from pathlib import Path, PurePosixPath


def embedded(data, kind):
    start = b'\n' + kind + b'__commencement\n'
    end = b'\n' + kind + b'__completion'
    if data.count(start) != 1 or data.count(end) != 1:
        raise ValueError(f'Expected one {kind.decode()} payload')
    begin = data.index(start) + len(start)
    return data[begin:data.index(end, begin)]


def main():
    installer, destination = map(Path, sys.argv[1:])
    archive = embedded(embedded(installer.read_bytes(), b'app'), b'tar.gz')
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as payload:
        members = payload.getmembers()
        roots = {PurePosixPath(m.name).parts[0] for m in members}
        if len(roots) != 1:
            raise ValueError('Expected one application directory')
        root = roots.pop()
        if not re.fullmatch(r'connectwisecontrol-[0-9a-f]+', root):
            raise ValueError('Unexpected application directory')
        files = {}
        for member in members:
            parts = PurePosixPath(member.name).parts
            if member.isdir() and parts == (root,):
                continue
            if not member.isfile() or len(parts) != 2 or parts[0] != root:
                raise ValueError(f'Unexpected archive member: {member.name}')
            if parts[1] in files:
                raise ValueError('Duplicate archive member')
            files[parts[1]] = payload.extractfile(member).read()

    required = {'ScreenConnect.Client.jar', 'ScreenConnect.Core.jar',
                'ClientLaunchParameters.txt', 'ClientLauncher.sh', 'ApplicationIcon32.png',
                'libscnative_x64.so', 'libscnative_libwebp_x64.so', 'libscnative_libzstd_x64.so'}
    if not required <= files.keys():
        raise ValueError('Application payload is incomplete')
    launcher = files['ClientLauncher.sh'].decode()
    old = 'clientInstallationDirectory="$userLevelApplicationsDirectory/$packageName"'
    if launcher.count(old) != 1:
        raise ValueError('Unrecognized launcher directory assignment')
    launcher = launcher.replace(old, 'clientInstallationDirectory="/opt/screenconnect-client"')
    old = 'logFilePath="$userLevelApplicationsDirectory/$packageName-logs"'
    if launcher.count(old) != 1:
        raise ValueError('Unrecognized launcher logging assignment')
    launcher = launcher.replace(old, '''logDirectory="${XDG_STATE_HOME:-$HOME/.local/state}/screenconnect-client"
umask 077
mkdir -p "$logDirectory" || exit 1
logFilePath="$logDirectory/client.log"''')
    # Keep vendor resources, but quote dynamic arguments (including browser URLs).
    start = launcher.index('launchCommandLine=')
    launcher = launcher[:start] + '''if ! command -v java >/dev/null 2>&1; then
    echo 'ScreenConnect requires a desktop Java runtime (Java 8 or newer).' >&2
    exit 1
fi

# Vendor resource properties contain space-separated, encoded -D arguments.
exec java -classpath "$javaClasspathCommandLineOptionValue" \\
    "$javaLibraryPathProperty" \\
    ${clientLaunchParametersFileProperty:+"$clientLaunchParametersFileProperty"} \\
    $clientResourcesAndConfigurationAsProperty \\
    com.screenconnect.client.Program MAIN_ACTION=start_client \\
    ${clientLaunchParametersArguments:+"$clientLaunchParametersArguments"} \\
    >> "$logFilePath" 2>&1 </dev/null
'''
    files['ClientLauncher.sh'] = launcher.encode()
    destination.mkdir(parents=True, exist_ok=True)
    for name in sorted(required):
        (destination / name).write_bytes(files[name])
    scheme = 'sc-' + root.removeprefix('connectwisecontrol-')
    (destination / 'screenconnect-client.desktop').write_text(f'''[Desktop Entry]
Type=Application
Name=ScreenConnect Client
Comment=Connect to remote ScreenConnect sessions
Exec=/usr/bin/screenconnect-client %u
Icon=screenconnect-client
Terminal=false
Categories=Network;RemoteAccess;
MimeType=x-scheme-handler/{scheme};
StartupNotify=false
''')
    print(f'Extracted technician client; URL scheme: {scheme}')


if __name__ == '__main__':
    main()
