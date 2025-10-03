#! /usr/bin/bash
qs -c caelestia kill 2>/dev/null || true
rm -rf ~/.cache/quickshell ~/.cache/QtQml ~/.cache/qtshadercache ~/.cache/QtShaderCache 2>/dev/null || true
sudo cmake --install build | grep -v Up-to-date
QML_DISABLE_DISK_CACHE=1 qs -c caelestia