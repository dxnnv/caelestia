#! /usr/bin/bash
sudo cmake --build build -j"$(nproc)"
sudo cmake --install build | grep -v Up-to-date
systemctl --user restart caelestia