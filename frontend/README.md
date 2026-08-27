# Frontend - Sistem Pelacakan Alumni

Frontend Vue 3 untuk Sistem Pelacakan Alumni Multi-Sumber (implementasi dari rancangan Daily
Project 2, skema data disesuaikan dengan roster resmi kampus di Daily Project 4), dipasangkan
dengan backend FastAPI di folder `../backend`. Autentikasi berbasis akun tanpa role - setiap
pengguna hanya mengelola data alumni miliknya sendiri.

---

## Fitur

- **Autentikasi**: login akun yang sudah disediakan, refresh token otomatis (Axios interceptor), logout. Registrasi publik dinonaktifkan.
- **Data Alumni**: CRUD sesuai kolom roster kampus (Nama Lulusan, NIM, Tahun Masuk, Tanggal
  Lulus, Fakultas, Program Studi), pencarian, filter status, paginasi.
- **Pelacakan multi-sumber (simulasi demo)**: jalankan pipeline pencarian per alumni atau proses
  seluruh antrean sekaligus; lihat temuan (8 data target: sosmed, email, no HP, tempat/alamat
  kerja, posisi, jenis pekerjaan, sosmed tempat kerja) beserta rincian skor per komponen.
- **Input Manual**: catat temuan yang benar-benar sudah diverifikasi sendiri (bukan simulasi) -
  otomatis dianggap terverifikasi penuh.
- **Sumber Data**: kelola sumber publik & bobot kepercayaan (langkah 2 pseudocode).
- **Tinjauan Manual**: antrean alumni dengan skor di zona abu-abu, putuskan terima/tolak/lacak ulang.
- **Dashboard**: ringkasan status alumni & aktivitas terbaru.
- Dark & light mode, toast notification, modal konfirmasi.

---

## Tech Stack

- **Framework**: [Vue.js 3](https://vuejs.org/) (Composition API)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **State**: [Pinia](https://pinia.vuejs.org/)
- **Routing**: [Vue Router](https://router.vuejs.org/)
- **Icons**: [Lucide Vue Next](https://lucide.dev/)
- **HTTP Client**: [Axios](https://axios-http.com/)

Backend: FastAPI + SQLite (lihat `../backend/README.md`).

---

## Instalasi & Menjalankan

1. **Instal dependensi**:
   ```bash
   npm install --legacy-peer-deps
   ```
   (`--legacy-peer-deps` diperlukan karena `@vee-validate/zod` masih menargetkan zod v3,
   sementara proyek ini memakai zod v4.)

2. **Konfigurasi environment**: `.env` sudah tersedia dengan
   `VITE_API_BASE_URL=http://localhost:8000`, sesuaikan bila backend berjalan di port lain.

3. **Pastikan backend menyala** (lihat `../backend/README.md`), lalu jalankan frontend:
   ```bash
   npm run dev
   ```

4. **Build untuk produksi**:
   ```bash
   npm run build
   ```

---

## Struktur Folder

- `src/services` - lapisan API Axios (`api.js`, `auth.service.js`, `alumni.service.js`,
  `source.service.js`, `tracking.service.js`, `review.service.js`, `dashboard.service.js`).
- `src/stores` - modul status global Pinia per domain (`auth`, `alumni`, `sources`, `review`,
  `dashboard`, `theme`).
- `src/views` - halaman aplikasi (`auth/Login.vue`, `Dashboard.vue`,
  `Alumni.vue`, `AlumniDetail.vue`, `Sources.vue`, `Review.vue`, `Profile.vue`).
- `src/layouts` - `AuthLayout.vue` (login/register) dan `AppLayout.vue` (sidebar + halaman utama).
- `src/components/ui` - komponen desain sistem (Button, Input, Select, Badge, Card, Toast, dll).
- `src/components/modals` - `AlumniModal.vue`, `SourceModal.vue`, `ManualCandidateModal.vue`,
  `ConfirmModal.vue`.

---

## Lisensi

MIT License

Copyright (c) 2026 M. Darma Putra Ramadhan
