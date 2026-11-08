# ScreenConnect technician client for Arch Linux

This local PKGBUILD repackages the generic `app` → `tar.gz` payload in
`ScreenConnect.ClientSetup.sh`. It never executes the vendor installer and does
not install the RPM/DEB unattended agent or a system service.

## Build and install

The first argument to `build-client.sh` is required: supply an installer URL or
a path to an already downloaded installer. All remaining arguments are passed
unchanged to `makepkg`.

Download and build from Northern Computer:

```sh
./build-client.sh 'https://cwa-northerncomputer.screenconnect.com/Bin/ScreenConnect.ClientSetup.sh'
```

Build from a local file (quote paths containing spaces):

```sh
./build-client.sh ~/Downloads/ScreenConnect.ClientSetup.sh
```

To also install the resulting package, add `-i` after the installer argument:

```sh
./build-client.sh ~/Downloads/ScreenConnect.ClientSetup.sh -i
```

Relative installer paths are resolved from your current directory. The script
runs the build in its own project directory and stages the installer as
`ScreenConnect.ClientSetup.sh`. Supplying that existing file is also supported.
It requires `makepkg`, plus `curl` when downloading an HTTP(S) URL; HTTPS is
preferred. Failed downloads or copies leave the previous installer in place.

The script runs `makepkg --cleanbuild --syncdeps`, which installs missing build
and runtime dependencies from the configured pacman repositories with the usual
sudo and pacman prompts. Run it as your normal user. Use `--help` for usage.

Source checksums remain pinned in `PKGBUILD`: if the supplied installer differs,
the build stops at checksum verification. Accepting another URL or file does not
automatically update the package version or checksum. Review the new payload and
update them as described below before rebuilding.

The `.gitignore` excludes the staged installer, temporary downloads, `src/`,
`pkg/`, package archives, signatures, and makepkg logs.

From this directory, with Arch's `base-devel` installed:

```sh
makepkg -si
```

Or install the already built package (pacman resolves its runtime dependencies):

```sh
sudo pacman -U ./screenconnect-client-bin-26.6.6.9747-1-x86_64.pkg.tar.zst
```

The desktop Java runtime dependency is `java-runtime>=8`. The supplied JARs use
Java 8 bytecode; compatibility with a particular newer runtime still needs a
live test. A headless-only Java runtime is insufficient for the GUI.

The package declares runtime dependencies on `java-runtime>=8`, `glibc`,
`desktop-file-utils`, and `xdg-utils`, plus the build dependency `python`.
Pacman can prompt you to choose a repository provider for the virtual Java
dependency. Runtime dependencies are recorded in the built package, so installing
it with `pacman -U` also resolves any missing runtime dependencies.

Launch **ScreenConnect Client** from the application menu, run
`screenconnect-client`, or open a session from your ScreenConnect portal. The
package advertises `x-scheme-handler/sc-ac53db9c1733326c`. If another application
already owns that association, select ScreenConnect in the browser's application
chooser or set it explicitly as your normal desktop user:

```sh
xdg-mime default screenconnect-client.desktop x-scheme-handler/sc-ac53db9c1733326c
```

Files live under `/opt/screenconnect-client`; logs are written to
`${XDG_STATE_HOME:-$HOME/.local/state}/screenconnect-client/client.log`.
Remove the package with `sudo pacman -R screenconnect-client-bin`.
User logs remain after removal.

## Relay configuration

The relay is supplied by the server that generated the installer. It is embedded
in the generic payload's `ClientLaunchParameters.txt` as a query string:

- `h=instance-ij98c7-relay.screenconnect.com`
- `p=443`

Other fields include connection/session information and a public key. Preserve
the complete parameter string rather than changing only its hostname.

Without an argument, the launcher passes
`-Dscreenconnect.client.launch.parameters.file=/opt/screenconnect-client/ClientLaunchParameters.txt`
to Java. With a nonempty first argument (normally a browser's session URL), it
instead passes that argument as `CLIENT_LAUNCH_PARAMETERS=...`. The Java client
interprets those parameters and makes the connection; the shell does not discover
the relay from the Linux distribution or package manager.

This build is specific to the supplied ScreenConnect instance. Do not publish the
installer or resulting package without reviewing its embedded connection data
and the vendor's redistribution terms.

## Updating and verification

To use a replacement installer, review its payload and version, update `pkgver`,
and regenerate the source checksums with `makepkg -g`. The extraction helper fails
if expected payload markers, archive structure, or launcher assignments change.
It packages only the x86-64 native libraries.

The launcher retains the vendor's embedded resource properties and connection
configuration, uses a system installation path and per-user logs, and quotes URL
arguments. Neither packaging nor installation launches a session automatically.

Validation performed: source checksum verification, complete package build,
shell syntax, desktop entry validation, and launcher argument checks using a fake
Java executable. The build used `makepkg --nodeps --force` because Java was absent;
no package was installed. GUI operation, Java-version compatibility, and Wayland
behavior have not been tested.
