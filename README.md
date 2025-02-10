# SEFEST25WEBDEV_VIBES
# 🚀 Proyek FRILO

FRILO adalah platform berbasis Flask yang menghubungkan pekerja lepas (freelancer) dengan pencari jasa (hirer). Aplikasi ini memungkinkan pengguna untuk membuat dan mengelola proyek, mengajukan penawaran, serta berkomunikasi melalui fitur chat real-time.

## 🎯 Fitur Utama
- **Autentikasi Pengguna**: Sistem login dan registrasi dengan hashing password.
- **Manajemen Proyek**: Pengguna dapat membuat, memperbarui, dan membatalkan proyek.
- **Pilih Peran & Profil**: Pengguna dapat memilih peran sebagai pekerja atau hirer serta mengisi profil mereka.
- **Aplikasi Proyek**: Freelancer dapat melamar ke proyek terbuka.
- **Chat Real-Time**: Komunikasi langsung dengan fitur socket.io.
- **Penyimpanan Data dengan MongoDB**: Semua data tersimpan dalam database NoSQL MongoDB.

## 📌 Teknologi yang Digunakan
- Python (Flask, Flask-SocketIO, Flask-PyMongo)
- HTML, CSS, JavaScript
- MongoDB (NoSQL Database)
- Socket.IO untuk komunikasi real-time

---

## 📖 Cara Instalasi dan Menjalankan Proyek

Ikuti langkah-langkah di bawah ini untuk menginstal dan menjalankan aplikasi ini secara lokal:

### 1️⃣ Clone Repository
```sh
git clone https://github.com/username/repo-name.git
cd repo-name
```

### 2️⃣ Buat Virtual Environment dan Install Dependencies
```sh
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 3️⃣ Konfigurasi Database
- Pastikan Anda memiliki akses ke MongoDB.
- Buat file `.env` dan tambahkan MongoDB URI:
```sh
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database_name
SECRET_KEY=your_secret_key
```

### 4️⃣ Jalankan Aplikasi
```sh
python app.py
```
Aplikasi akan berjalan di `http://127.0.0.1:5000/`.

---

## 🛠 Cara Menggunakan Aplikasi

### 1️⃣ Registrasi & Login
1. Buka halaman utama dan klik "Sign Up".
2. Isi detail akun dan pilih peran (Worker atau Hirer).
3. Setelah registrasi, login ke akun Anda.

### 2️⃣ Membuat Proyek (Hirer)
1. Pilih menu "Buat Proyek".
2. Isi detail proyek, seperti nama, deskripsi, dan kategori.
3. Klik "Submit" untuk menyimpan proyek.

### 3️⃣ Melamar Proyek (Worker)
1. Buka halaman "Proyek Tersedia".
2. Klik proyek yang diinginkan dan tekan tombol "Lamar".

### 4️⃣ Chat Real-Time
1. Pilih kontak di menu chat.
2. Ketik pesan dan tekan "Kirim".

---

## 🤝 Kontribusi
Jika Anda ingin berkontribusi:
1. Fork repositori ini.
2. Buat branch baru (`git checkout -b feature-branch`).
3. Commit perubahan (`git commit -m 'Menambahkan fitur X'`).
4. Push ke branch Anda (`git push origin feature-branch`).
5. Buat Pull Request.

---

## 📧 Kontak
Jika ada pertanyaan, silakan hubungi:
- Email: winsonlearn@gmail.com

Terima kasih telah menggunakan FRILO! 🚀

