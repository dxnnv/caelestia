pkgname=caelestia-meta
pkgver=1.0
pkgrel=1
pkgdesc="Meta-package to hold dependencies for the Caelestia application (no files installed)"
arch=('any')
url="https://dxnny.dev"
license=('GPLv3')

depends=(
  # Runtime CLI/tools
  'aubio'
  'libnotify'
  'swappy'
  'grim'
  'dart-sass'
  'app2unit'
  'wl-clipboard'
  'slurp'
  'gpu-screen-recorder'
  'cliphist'
  'fuzzel'
  'ddcutil'
  'brightnessctl'
  'libqalculate'
  'bash'
  'fish'
  'networkmanager'
  'lm_sensors'

  # Libraries / runtime
  'glib2'
  'glibc'
  'libpipewire'
  'gcc-libs'
  'libcava'

  # Qt / build chain
  'qt6-base'
  'qt6-declarative'
  'cmake'
  'ninja'

  # Fonts / assets (keep as depends if Caelestia truly needs them present)
  'ttf-material-symbols-variable-git'
  #'caskadiya-cove-nerd'

  # AUR / VCS
  'quickshell-git'
)

# No sources; this package is empty by design.
provides=('caelestia-meta')
conflicts=()
source=()
md5sums=()

package() {
  # Intentionally empty: meta-package installs no files.
  :
}
