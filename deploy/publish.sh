#!/usr/bin/env bash
# Install a complete static release and atomically switch the current symlink.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
  echo 'Run with sudo: sudo bash deploy/publish.sh dist' >&2
  exit 1
fi
source_dir=$(realpath "${1:-dist}")
for file in index.html app.js styles.css assets/aib-logo.png assets/documents/offer.pdf assets/documents/confidentiality.pdf robots.txt sitemap.xml 404.html; do
  [[ -s "$source_dir/$file" && ! -L "$source_dir/$file" ]] || { echo "Missing or linked file: $file" >&2; exit 1; }
done
base=/srv/aib-etrn
if [[ -e "$base/current" && ! -L "$base/current" ]]; then
  echo "$base/current must be absent or a symbolic link" >&2
  exit 1
fi
install -d -m 755 "$base/releases" "$base/legal"
release=$(mktemp -d "$base/releases/$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
chmod 755 "$release"
install -d -m 755 "$release/assets/documents"
for file in index.html app.js styles.css robots.txt sitemap.xml 404.html; do
  install -m 644 "$source_dir/$file" "$release/$file"
done
install -m 644 "$source_dir/assets/aib-logo.png" "$release/assets/aib-logo.png"
install -m 644 "$source_dir/assets/documents/offer.pdf" "$release/assets/documents/offer.pdf"
install -m 644 "$source_dir/assets/documents/confidentiality.pdf" "$release/assets/documents/confidentiality.pdf"
if [[ -L "$base/current" ]]; then
  echo "Previous release: $(readlink -f "$base/current")"
fi
link="$base/current-next-$(basename "$release")"
ln -s "$release" "$link"
mv -Tf "$link" "$base/current"
echo "Published: $release"
