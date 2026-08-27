# Deployment produksi sinata.tech

Panduan ini ditujukan untuk Ubuntu/Debian dengan akses `root`. Aplikasi produksi
ditempatkan di `/var/www/sinata`, backend hanya mendengarkan `127.0.0.1:8000`, dan
Nginx menjadi satu-satunya layanan yang menerima koneksi publik.

## 1. Pastikan DNS sudah benar

Buat A record `sinata.tech` menuju IPv4 server. Jika server memakai IPv6, tambahkan
AAAA record yang benar. Pastikan hasil berikut menampilkan IP server:

```bash
getent ahostsv4 sinata.tech
```

Port 80 dan 443 harus terbuka pada firewall/cloud firewall.

## 2. Instal paket sistem

```bash
apt update
apt install -y nginx certbot python3-certbot-nginx python3-venv python3-pip nodejs npm rsync
```

Jika `node --version` lebih lama dari versi 20, pasang Node.js LTS terbaru terlebih
dahulu. Vite 8 membutuhkan Node.js 20.19+ atau 22.12+.

## 3. Salin aplikasi ke direktori produksi

Jalankan dari `/root/DailyProject3`:

```bash
mkdir -p /var/www/sinata
rsync -a --delete --exclude .git --exclude backend/venv --exclude frontend/node_modules --exclude backend/.env --exclude '*.db' ./ /var/www/sinata/
```

Salin database yang sudah ada hanya pada deployment pertama bila datanya ingin
dipertahankan:

```bash
cp -n backend/alumni_tracker.db /var/www/sinata/backend/alumni_tracker.db
```

## 4. Konfigurasi backend

```bash
cd /var/www/sinata/backend
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
cp -n .env.example .env
openssl rand -hex 32
```

Edit `/var/www/sinata/backend/.env`. Tempel hasil `openssl rand -hex 32` sebagai
`SECRET_KEY`, isi `SERPAPI_KEY` baru bila fitur pencarian digunakan, dan pastikan:

```dotenv
DATABASE_URL=sqlite:///./alumni_tracker.db
SECRET_KEY=GANTI_DENGAN_HASIL_OPENSSL
CORS_ORIGINS=["https://sinata.tech"]
SERPAPI_KEY=
```

Jangan commit file `.env`. API key yang pernah tersimpan atau dibagikan harus dirotasi.

## 5. Build frontend

```bash
cd /var/www/sinata/frontend
npm ci --legacy-peer-deps
npm run build
```

Konfigurasi `.env.production` menggunakan same-origin. Permintaan `/api/...` akan
diteruskan Nginx ke backend sehingga tidak memerlukan domain API terpisah.

## 6. Hak akses dan systemd

```bash
chown -R www-data:www-data /var/www/sinata
cp /var/www/sinata/deploy/systemd/sinata-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now sinata-backend
systemctl status sinata-backend --no-pager
curl http://127.0.0.1:8000/api/v1/health
```

Jika backend gagal, periksa log:

```bash
journalctl -u sinata-backend -n 100 --no-pager
```

## 7. Aktifkan Nginx

```bash
cp /var/www/sinata/deploy/nginx/sinata.tech.conf /etc/nginx/sites-available/sinata.tech
ln -sfn /etc/nginx/sites-available/sinata.tech /etc/nginx/sites-enabled/sinata.tech
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
curl -I http://sinata.tech
curl http://sinata.tech/api/v1/health
```

Jangan menjalankan Certbot sebelum kedua perintah `curl` berhasil melalui HTTP.

## 8. Pasang HTTPS dengan Certbot

Ganti alamat email berikut dengan email aktif:

```bash
certbot --nginx -d sinata.tech --redirect --agree-tos --no-eff-email -m EMAIL_AKTIF_ANDA
```

Verifikasi HTTPS dan pembaruan otomatis:

```bash
curl -I https://sinata.tech
curl https://sinata.tech/api/v1/health
certbot renew --dry-run
systemctl status certbot.timer --no-pager
```

## 9. Update deployment berikutnya

Di `/root/DailyProject3`:

```bash
git pull origin main
rsync -a --delete --exclude .git --exclude backend/venv --exclude frontend/node_modules --exclude backend/.env --exclude '*.db' ./ /var/www/sinata/
cd /var/www/sinata/backend
venv/bin/pip install -r requirements.txt
cd /var/www/sinata/frontend
npm ci --legacy-peer-deps
npm run build
chown -R www-data:www-data /var/www/sinata
systemctl restart sinata-backend
nginx -t
systemctl reload nginx
```

Karena database dan `.env` dikecualikan dari `rsync`, data produksi dan rahasia tidak
tertindih saat aplikasi diperbarui.
