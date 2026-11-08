#!/usr/bin/env bash
set -euo pipefail

usage() {
    printf 'Usage: %s <installer-url-or-file> [makepkg options]\n' "${0##*/}"
    printf 'Accepts an HTTP(S) URL or a local installer path.\n'
    printf 'Runs makepkg --cleanbuild --syncdeps with the remaining arguments.\n'
}

if [[ ${1:-} == --help || ${1:-} == -h ]]; then
    usage
    exit 0
fi
if (( $# == 0 )) || [[ -z $1 ]]; then
    usage >&2
    exit 1
fi

installer_source=$1
shift
case "$installer_source" in
    http://*|https://*) source_type=url ;;
    *://*) printf 'Unsupported installer URL: use HTTP or HTTPS.\n' >&2; exit 1 ;;
    *)
        source_type=file
        # Resolve relative input paths before changing to the project directory.
        [[ $installer_source == /* ]] || installer_source="$PWD/$installer_source"
        if [[ ! -f $installer_source || ! -r $installer_source || ! -s $installer_source ]]; then
            printf 'Installer must be a readable, nonempty file: %s\n' "$installer_source" >&2
            exit 1
        fi
        ;;
esac

build_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd -- "$build_directory"

required_commands=(makepkg)
[[ $source_type != url ]] || required_commands+=(curl)
for required_command in "${required_commands[@]}"; do
    if ! command -v "$required_command" >/dev/null 2>&1; then
        printf 'Required command is missing: %s\n' "$required_command" >&2
        exit 1
    fi
done

if (( EUID == 0 )); then
    printf 'Run this script as your normal user; makepkg cannot run as root.\n' >&2
    exit 1
fi

staged_installer=$(mktemp "$build_directory/.ScreenConnect.ClientSetup.sh.XXXXXXXX")
trap 'rm -f -- "$staged_installer"' EXIT

if [[ $source_type == url ]]; then
    printf 'Downloading ScreenConnect technician client...\n'
    curl --fail --location --show-error --retry 3 \
        --connect-timeout 30 --max-time 300 \
        --proto '=http,https' --proto-redir '=http,https' \
        --output "$staged_installer" "$installer_source"
else
    printf 'Using local installer: %s\n' "$installer_source"
    cp -- "$installer_source" "$staged_installer"
fi

if [[ ! -s $staged_installer ]]; then
    printf 'The installer is empty.\n' >&2
    exit 1
fi

# Atomic replacement also supports supplying the existing project installer.
mv -f -- "$staged_installer" "$build_directory/ScreenConnect.ClientSetup.sh"
printf 'Building package; makepkg will verify the pinned source checksums.\n'
makepkg --cleanbuild --syncdeps "$@"
