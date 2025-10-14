pkgname=caelestia-meta
pkgver=1.0
pkgrel=1
pkgdesc="Meta-package to hold dependencies for the Caelestia application (no files installed)"
arch=('any')
url="https://dxnny.dev"
license=('GPLv3')

depends=(
  # Runtime CLI/tools
  'dart-sass'
  'libqalculate'
  'lm_sensors'
  'networkmanager'

  ## Applications
  'app2unit'
  'fuzzel'

  ## Capture
  'aubio'
  'hyprshot'
  'gpu-screen-recorder'
  'slurp'
  'swappy'

  ## Clipboard
  'cliphist'
  'wl-clipboard'

  ## Display
  'brightnessctl'
  'ddcutil'
  'hyprsunset'

  ## Notifications
  'libnotify'
  'swaync'

  ## Shell
  'bash'
  'fish'

  # Libraries / runtime
  'gcc-libs'
  'glib2'
  'glibc'
  'libcava'
  'libpipewire'
  'quickshell'

  # Qt / build chain
  'cmake'
  'ninja'
  'qt6-base'
  'qt6-declarative'

  # Fonts / assets
  'ttf-material-symbols-variable-git'
  #'caskadiya-cove-nerd'


  'quickshell'
)

# No sources, package is intentionally empty.
provides=('caelestia-meta')
conflicts=()
source=()
md5sums=()

package() {
  # Intentionally empty: meta-package installs no files.
  :
}
