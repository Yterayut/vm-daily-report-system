#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
cd "$ROOT_DIR"

if [[ ! -f ".env" ]]; then
  echo "ERROR: .env not found in $(pwd)"
  exit 1
fi

read -r -p "ZABBIX_URL: " z_url
read -r -p "ZABBIX_USER: " z_user
read -r -s -p "ZABBIX_PASS: " z_pass
echo

if [[ -z "$z_url" || -z "$z_user" || -z "$z_pass" ]]; then
  echo "ERROR: all values are required"
  exit 1
fi

escape_sed() {
  printf '%s' "$1" | sed -e 's/[\\/&]/\\&/g'
}

z_url_esc="$(escape_sed "$z_url")"
z_user_esc="$(escape_sed "$z_user")"
z_pass_esc="$(escape_sed "$z_pass")"

sed -i "s|^ZABBIX_URL=.*|ZABBIX_URL=${z_url_esc}|" .env
sed -i "s|^ZABBIX_USER=.*|ZABBIX_USER=${z_user_esc}|" .env
sed -i "s|^ZABBIX_PASS=.*|ZABBIX_PASS=${z_pass_esc}|" .env

echo "Updated ZABBIX_URL/ZABBIX_USER/ZABBIX_PASS in .env"
echo "Run: ./scripts/zabbix_auth_preflight.sh ."
