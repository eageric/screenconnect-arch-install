# Local package for the technician client embedded in this instance's installer.
pkgname=screenconnect-client-bin
pkgver=26.6.6.9747
pkgrel=1
pkgdesc='ScreenConnect Java technician client (instance-specific binary payload)'
arch=('x86_64')
url='https://www.screenconnect.com/'
license=('custom:proprietary')
depends=('java-runtime>=8' 'glibc' 'desktop-file-utils' 'xdg-utils')
makedepends=('python')
options=('!strip' '!debug')
source=('ScreenConnect.ClientSetup.sh' 'extract-app.py')
noextract=('ScreenConnect.ClientSetup.sh')
sha256sums=('3b7aad14ec698b2c5d37dca1daca262efe88e46e38365b66036f37c647bb7882'
            '9166595da9f4bc60c627d6c661991f0b9f76952bacf6389fdbd5ef0535231ba1')

prepare() {
    python "$srcdir/extract-app.py" "$srcdir/ScreenConnect.ClientSetup.sh" "$srcdir/payload"
}

check() {
    sh -n "$srcdir/payload/ClientLauncher.sh"
    desktop-file-validate "$srcdir/payload/screenconnect-client.desktop"
}

package() {
    local file
    for file in ScreenConnect.Client.jar ScreenConnect.Core.jar ClientLaunchParameters.txt \
                libscnative_x64.so libscnative_libwebp_x64.so libscnative_libzstd_x64.so; do
        install -Dm644 "$srcdir/payload/$file" "$pkgdir/opt/screenconnect-client/$file"
    done
    install -Dm755 "$srcdir/payload/ClientLauncher.sh" \
        "$pkgdir/opt/screenconnect-client/ClientLauncher.sh"
    install -d "$pkgdir/usr/bin"
    ln -s /opt/screenconnect-client/ClientLauncher.sh "$pkgdir/usr/bin/screenconnect-client"
    install -Dm644 "$srcdir/payload/screenconnect-client.desktop" \
        "$pkgdir/usr/share/applications/screenconnect-client.desktop"
    install -Dm644 "$srcdir/payload/ApplicationIcon32.png" \
        "$pkgdir/usr/share/icons/hicolor/32x32/apps/screenconnect-client.png"
}
