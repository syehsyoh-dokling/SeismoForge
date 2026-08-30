# SeismoForge

## Insinyur Desain Seismik Berbasis AI dengan Gerbang Bukti

**Dari brief proyek berbahasa manusia menjadi konsep desain tahan gempa yang sudah lolos simulasi — di mana setiap angka yang dilaporkan berasal dari fisika, dan tidak ada kesimpulan yang boleh membantahnya.**

---

# Apa itu SeismoForge?

Bayangkan seorang klien mengirim pesan seperti ini:

> *"Kami merencanakan rumah sakit lima lantai di lahan reklamasi pesisir dengan tanah lunak. Berat tiap lantai sekitar 550 ton, PGA desain 0,32 g. Celah yang tersedia di sekeliling bangunan 0,9 meter. Apakah bangunan ini perlu isolasi dasar?"*

SeismoForge membaca pesan itu, merancang sistem perlindungan gempanya, **mengujinya dengan simulasi gempa sungguhan**, memperbaikinya kalau gagal, dan mengembalikan satu laporan teknik — atau menolak, kalau permintaan kliennya memang tidak mungkin dipenuhi.

## Cara kerjanya, dalam empat kalimat

1. **Model bahasa membaca brief.** Ia mengeluarkan sembilan parameter teknik dari prosa biasa — dan tidak boleh mengarang satu pun: tiap nilai wajib mengutip potongan kalimat asalnya.
2. **Mesin desain mengusulkan sebuah konsep.** Rangka konvensional, atau lapisan isolasi karet-timbal di bawah bangunan.
3. **OpenSees mengguncangnya.** Lima rekaman gempa sintetis, masing-masing analisis riwayat-respons nonlinear penuh, lalu setiap batas kinerja diperiksa terhadap hasilnya.
4. **Gerbang bukti memutuskan.** Sebelum laporan ditulis, desainnya disimulasikan ulang. Kalau buktinya membantah kesimpulannya, laporan itu **menolak ditulis**.

> **Model menangani ambiguitas. Perkakas menangani fisika. Bukti menentukan apa yang boleh diklaim.**

SeismoForge adalah **prototipe tahap konsep, bukan sistem desain konstruksi.** Setiap laporannya ditujukan untuk direview dan ditandatangani insinyur struktur berlisensi sebelum memengaruhi keputusan desain, pengadaan, atau konstruksi apa pun.

### Tautan cepat

- **GUI lokal:** jalankan `python3 gui/server.py`, buka `http://127.0.0.1:8765`
- **Panduan reproduksi:** `REPRODUCTION.md`
- **Hasil terukur:** `evaluation/results.md`
- **Trajectory agent:** `trajectories/`
- **Contoh deliverable:** `outputs/agent/brief_01_coastal_hospital/design_report.md`
- **Kasus uji:** `briefs/` (format ketat) dan `briefs_prose/` (sepuluh proyek yang sama sebagai prosa bebas)
- **Cakupan dan keselamatan:** lihat [Cakupan, Review, dan Keselamatan](#cakupan-review-dan-keselamatan)
- **Keterbatasan pemodelan:** lihat [Keterbatasan Pemodelan yang Diketahui](#keterbatasan-pemodelan-yang-diketahui)

---

# Hasilnya dalam satu layar

## **3/10 → 10/10 kesimpulan teknik yang benar**

Diukur pada benchmark sepuluh bangunan yang sama, dinilai lewat re-simulasi independen atas setiap desain yang diserahkan.

| Metrik | Baseline tanpa verifikasi | Deterministic Forge (`offline`) | Hybrid Evidence Agent (`assisted`) | Full-Agent Experimental Mode (`agent`) |
|---|---:|---:|---:|---:|
| Siapa membaca brief | — | parser ketat | **model** | **model** |
| Siapa memilih desain berikutnya | — | kebijakan tertulis | kebijakan tertulis | **model** |
| Format input yang didukung | datasheet berlabel | datasheet berlabel | **prosa bebas** | **prosa bebas** |
| Brief terselesaikan benar — metrik utama | **3/10** | **10/10** | **10/10** | **10/10** |
| Mengenali brief yang mustahil | tidak — bilang "lanjutkan" | ya | ya | ya |
| Waktu, portofolio penuh | 0,4 s | 38,6 s | 71,3 s | 337,8 s |
| Token model, portofolio penuh | — | — | **8.421 in / 2.081 out** | **518.386 in / 17.272 out** |
| Peran manusia | studi penuhnya tetap diperlukan | review | review | review |

Diukur pada `gpt-5.5` untuk mode yang digerakkan model.

Angka utamanya 3/10 → 10/10. Tetapi temuan yang lebih penting justru terjadi **di antara dua sistem yang sama-sama 10/10**:

> **Menyerahkan pencarian desain sepenuhnya kepada model menghasilkan skor teknik yang sama, dengan 62× token input dan 4,7× waktu dibanding alur hybrid.**

Eksperimen itulah yang mengubah arsitekturnya.

---

# Mengapa masalah ini layak diselesaikan

## Siapa penggunanya?

Insinyur — terutama **insinyur teknik sipil dan insinyur struktur** yang menangani perlindungan gempa di tahap konsep:

- **kantor konsultan struktur** yang menyaring beberapa opsi proteksi sebelum menetapkan satu konsep;
- **insinyur profesional individual** yang bekerja tanpa tim analisis di belakangnya;
- **arsitek** yang perlu tahu lebih awal apakah suatu konsep proteksi muat di dalam batasan tapaknya — terutama celah moat di sekeliling bangunan, karena itu memengaruhi denah dan garis sempadan.

Yang mereka semua hadapi sama: sebuah keputusan yang harus diambil **sebelum** ada anggaran untuk studi penuh.

## Masalah apa yang mereka hadapi?

Mencapai konsep seismik yang bisa dipertanggungjawabkan bukan perhitungan satu-tembakan. Bergantung pada bangunannya dan kelengkapan datanya, pekerjaan strukturnya bisa menghabiskan **beberapa hari hingga beberapa minggu** waktu insinyur sebelum masuk review.

Yang menyita bukan menuliskan rumusnya, melainkan **lingkaran komputasinya**: menyusun model, memilih rekaman gempa, menjalankan analisis riwayat-respons nonlinear, membaca hasilnya, merevisi desain, lalu mengulang.

SeismoForge tidak mengklaim menggantikan pekerjaan itu. Ia memampatkan **bagian komputasi dan iteratifnya** menjadi hitungan detik, dan menyerahkan sisanya - penilaian teknik, investigasi lokasi, dan tanda tangan - kepada insinyur.

> Tentang angkanya: proses desain konsep sudah pernah di-benchmark dalam literatur - studi Gane dan Haymaker atas proses desain konsep gedung tinggi menganalisis ukuran tim, komposisinya, dan investasi waktunya ([CIFE TR174, Stanford, 2008](https://purl.stanford.edu/xm514gk6039); versi peer-review-nya terbit sebagai *Benchmarking Current Conceptual High-Rise Design Processes*, ASCE Journal of Architectural Engineering 16(3)). Tidak ada angka jam kerja yang diterbitkan untuk keputusan spesifik ini, jadi dokumen ini mengutip rentang dari praktik alih-alih mengarang satu. Evaluasi seismik penuh menurut ASCE/SEI 41 - investigasi lokasi, uji material, verifikasi gambar, peer review - adalah aktivitas yang lebih besar lagi, dan bukan itu yang dikerjakan SeismoForge.

## Kenapa menyelesaikannya bernilai?

AI membuat jawaban pertama lebih cepat. Tapi kecepatan tidak pernah menjadi bagian yang sulit.

> **Bagian yang sulit adalah mengetahui kapan jawaban itu tidak boleh dipercaya.**

Sizing satu-tembakan bisa terlihat meyakinkan dan tetap salah, karena isolasi seismik hidup di dalam ruang desain yang saling terkopel:

- disipasi energi lebih besar memperkecil geseran isolator, tetapi **menaikkan** gaya yang diteruskan ke bangunan di atasnya;
- periode isolasi lebih panjang menurunkan gaya, tetapi **memakan** celah moat;
- tanah lunak menghukum justru perilaku periode-panjang yang di tempat lain membantu.

Baseline rumus praktis kami membuat masalah itu terukur. Ia hanya menyelesaikan **3 dari 10** brief dengan benar, dan pada satu proyek yang sengaja dibuat mustahil, ia dengan percaya diri merekomendasikan "lanjutkan".

Dan ia tidak ngawur. **Lima dari tujuh kegagalannya meleset 13% atau kurang.** Kamu tidak bisa melihat itu dari membaca laporannya.

SeismoForge ada untuk menutup jarak antara **terdengar masuk akal** dan **bisa dipertanggungjawabkan**.

---

# Produknya

## Satu brief masuk. Satu kesimpulan teknik keluar.

Pengguna menyerahkan **satu proyek** dan menerima **satu kesimpulan teknik tahap konsep**. Itulah produknya, dan itulah yang dijalankan `gui/server.py`.

Sepuluh berkas di `briefs/` bukan satu sesi raksasa. Itu **kasus evaluasi**: sepuluh bangunan berbeda, masing-masing dijalankan sendiri-sendiri, supaya klaim "ini bekerja" bisa **diuji**, bukan sekadar dinyatakan.

`briefs_prose/` memuat sepuluh proyek yang sama ditulis sebagai prosa biasa. Set kedua itu menguji pertanyaan berbeda: bisakah sistem memahami brief manusia tanpa memaksa penggunanya mengisi templat kaku?

---

# Prinsip inti: Agensi yang Digerbangi Bukti

SeismoForge tidak meminta sebuah LLM menjadi kalkulator, simulator, dan hakim bagi dirinya sendiri. Pekerjaannya dibagi menurut apa yang benar-benar dikuasai tiap komponen.

```text
                 INSINYUR (MANUSIA)
                        │
                        ▼
              Brief bahasa manusia
                        │
                        ▼
              ┌──────────────────┐
              │   AGENT INTAKE   │
              │ Pahami maksud    │
              │ Ekstrak + kutip  │
              └────────┬─────────┘
                        │
                   SOURCE LOCK
                        │
                        ▼
              ┌──────────────────┐
              │  MESIN DESAIN    │
              │ Usulkan & cari   │
              │ kandidat         │
              └────────┬─────────┘
                        │
                        ▼
              ┌──────────────────┐
              │     OPENSEES     │
              │ RHA nonlinear    │
              └────────┬─────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  GERBANG BUKTI   │
              │ Lolos / Tolak /  │
              │ Iterasi          │
              └────────┬─────────┘
                        │
                        ▼
              LAPORAN TERVERIFIKASI
                        │
                        ▼
             PERSETUJUAN MANUSIA
```

## Terkunci sumber di jalan masuk. Terkunci bukti di jalan keluar.

**Source lock (jalan masuk):** setiap nilai yang diekstrak dari prosa bebas wajib mengutip potongan teks yang mendukungnya. Kutipan itu dicek terhadap brief asli, dan datasheet hasil rekonstruksinya harus lolos parser ketat yang sama dengan jalur deterministik. Nilai yang tidak dinyatakan brief dilaporkan **hilang**, bukan dikarang.

**Evidence lock (jalan keluar):** setiap besaran respons berasal dari rantai perkakas teknik. `write_report` menyimulasikan ulang desain yang diserahkan dan **menolak** kesimpulan yang dibantah bukti. `verify_output` lalu memeriksa deliverable yang sudah ditulis sekali lagi, dengan logika yang sama seperti evaluator.

Hasilnya sistem yang sengaja dibuat asimetris:

> **AI boleh menafsirkan. AI boleh mengusulkan. AI boleh menjelaskan. Tapi AI tidak boleh membatalkan bukti fisika.**

---

# Bagaimana SeismoForge bekerja

## 1. Membaca brief

Model mengubah prosa proyek bebas menjadi sembilan field teknik yang diperlukan.

Di sinilah kemampuan model benar-benar bernilai. Parser ketat mendapat **0/10** pada `briefs_prose/`: pada kesepuluh proyek ia gagal di kesembilan field, karena informasinya tidak ditulis dalam format berlabel yang dituntutnya.

Hybrid Evidence Agent menutup celah itu sepenuhnya, memakai **8.421 token input untuk seluruh portofolio sepuluh kasus**.

Bukti terkuat bahwa pembacaan ini setia bukanlah skornya — keduanya sama-sama 10/10 — melainkan desain di bawahnya. **Pada kesepuluh brief, Hybrid Evidence Agent dan Deterministic Forge menyerahkan desain yang identik.** Bacaan model atas prosa biasa mendarat persis pada sembilan nilai yang diekstrak parser ketat dari datasheet berlabel, proyek demi proyek. Yang berubah adalah apa yang bisa **diterima** sistem sebagai masukan, bukan apa yang **disimpulkannya**.

## 2. Menghasilkan konsep teknik pertama

Alur kerjanya dimulai dari konsep rumus praktis, bukan dari pencarian buta yang mahal.

## 3. Menantangnya dengan fisika

Setiap kandidat melewati rantai simulasi OpenSees. Ground motion disintesis deterministik dari brief memakai proses spektral terfilter tanah dengan tahap high-pass Clough-Penzien.

Tiap evaluasi desain menjalankan suite lima rekaman, jadi satu kandidat berbiaya lima analisis riwayat-respons nonlinear. Portofolio deterministik penuh menjalankan 110 evaluasi desain — **550 analisis nonlinear** — dalam 38,6 detik.

Tidak ada driver desain — deterministik maupun berbasis model — yang boleh memproduksi angka respons secara langsung.

## 4. Mencari hanya bila perlu

Kalau konsep pertama gagal, alur deterministiknya bergerak melalui:

**rumus praktis → penyaringan kasar ruang yang bisa dibangun → penghalusan berbasis kegagalan**

Aturan penghalusannya mengkodekan perilaku teknik yang terkopel. Contoh: bila gaya yang diteruskan terlalu tinggi, perpanjang periode atau perlunak transisi leleh — bukan mengubah satu skalar secara membabi buta.

## 5. Membiarkan laporan berkata "tidak"

Lapisan pelaporan punya hak veto.

Desain yang gagal pemeriksaan penerimaan **tidak bisa** dilaporkan sebagai "lanjutkan". Desain yang lolos tidak bisa dilaporkan sebagai mustahil. Deliverable akhir disimulasikan ulang sebelum verdict-nya ditulis.

## 6. Menjaga manusia berkualifikasi tetap memegang kendali

Keluaran akhirnya adalah titik awal teknik yang bisa direview, dengan basis bukti yang bisa ditelusuri. Ia bukan pengganti penilaian profesional atau stempel insinyur berlisensi.

---

# Eksperimen terpenting: di mana seharusnya agent berpikir?

Jalur deterministik dibangun lebih dulu, dan ia **sudah** mencapai 10/10 pada brief berlabel. Jadi pertanyaannya bukan apakah sebuah model bisa mencapai skor itu — melainkan **apa yang ditambahkan model yang tidak bisa dilakukan kebijakan tertulis.**

Kami membelah alur kerja di dua sambungannya, lalu mengukurnya satu per satu.

**Sambungan pertama — membaca brief.** Model menafsirkan prosa bebas; kebijakan tertulis tetap menjalankan pencarian. Itulah Hybrid Evidence Agent, dan ia mendapat **10/10** pada set prosa yang sama sekali tidak bisa dibaca parser ketat.

**Sambungan kedua — menyetir pencarian.** Model juga mendapat pencarian desainnya. Itulah Full-Agent Experimental Mode, dan ia juga mendapat **10/10**.

Skor sama. Profil sumber daya berbeda jauh:

| Alur kerja | Kasus benar | Waktu | Token input model |
|---|---:|---:|---:|
| Hybrid Evidence Agent | **10/10** | 71,3 s | **8.421** |
| Full-Agent Experimental Mode | **10/10** | 337,8 s | **518.386** |

Agensi penuh **tidak membeli perbaikan terukur apa pun** pada ruang desain ini.

Itu bukan kegagalan model. Itu bukti tentang bentuk masalahnya. Ruang desainnya cukup kecil dan kopling constraint-nya cukup teratur sehingga strategi pencariannya bisa ditulis sekali. Sebaliknya, intake bahasa alami benar-benar ambigu dan tidak bisa digantikan parser ketat.

## Pelajaran arsitekturnya

> **Pakai AI di tempat ambiguitas menuntut penilaian. Pakai perkakas deterministik di tempat masalahnya sudah punya fisika.**

Arsitektur yang paling agentik ternyata bukan arsitektur yang terbaik.

Yang terbaik adalah yang memberi model tanggung jawab **hanya di tempat kemampuan model mengubah hasil.**

---

# Kasus menantang: kadang desain yang benar adalah tidak ada desain

`brief_10_cliffside_clinic` sengaja dibuat mustahil dalam asumsi benchmark: lokasi near-fault bertanah lunak yang parah, digabung batas moat 0,40 m.

Sapuan eksaustif 75 titik menemukan **nol desain yang layak** di bawah aturan benchmark.

Kasus ini penting karena metrik "success rate" konvensional bisa dikorupsi. Kalau sebuah sistem hanya dihadiahi karena menghasilkan desain yang lolos, ia terdorong untuk **memaksakan** satu.

SeismoForge menghitung ketidakmungkinan yang jujur sebagai **benar**, dan "lanjutkan" yang dipaksakan sebagai **salah**.

> **Kadang jawaban teknik yang paling aman dan paling berguna adalah: brief-nya yang harus diubah.**

Itulah sebabnya 10/10 di sini bermakna — satu dari sepuluh jawaban benar itu adalah **penolakan** untuk berpura-pura bahwa desain yang layak itu ada.

---

# Tiga mode operasi, satu jalur eksekusi

Setiap pintu masuk — CLI, GUI, dan harness evaluasi — mengirim brief melalui `agent/session.py`. Tidak ada implementasi demo terpisah. Jalur yang ditampilkan GUI adalah jalur yang diukur evaluasi, dan tiap run meninggalkan trajectory.

Dua tanggung jawab bisa berubah secara independen: siapa membaca brief, dan siapa memilih desain berikutnya.

| Mode | Pembaca brief | Penggerak pencarian | Perlu kunci API |
|---|---|---|---|
| **Deterministic Forge** (`offline`) | parser ketat | kebijakan tertulis | tidak |
| **Hybrid Evidence Agent** (`assisted`) | model | kebijakan tertulis | ya |
| **Full-Agent Experimental Mode** (`agent`) | model | model | ya |

Nama-nama di atas adalah label dokumentasi; flag dalam kurung adalah yang benar-benar dipakai kode, CLI, dan `evaluation/results.md`.

Perbedaan format wire antar provider tinggal di satu tempat: `agent/llm.py`. Hasil tool Anthropic direpresentasikan sebagai blok konten di dalam giliran user; hasil tool OpenAI adalah pesan `tool` terpisah berkunci call id. Sembilan tool-nya dideklarasikan satu kali, dan logika sesi tidak perlu bercabang per vendor.

Run terukur yang dilaporkan di sini memakai `gpt-5.5`. Jalur kode yang sama juga menerima `claude-opus-5`.

---

# Pilihan rekayasa yang penting

## Perkakas menghitung; driver memutuskan

Baik driver-nya model maupun kebijakan tertulis, respons struktural kuantitatif datang dari rantai perkakas. Lapisan keputusan boleh memilih kandidat, tapi tidak boleh mengarang nilai demand.

## Pencarian yang berbentuk seperti praktik teknik

Alurnya tidak dimulai dari eksplorasi agentik tanpa batas. Ia berangkat dari aturan sizing yang wajar, menyaring wilayah desain yang layak bila perlu, lalu menghaluskan berdasarkan constraint yang gagal.

## Laporan boleh menolak

`write_report` menyimulasikan ulang submission akhir dan tidak akan menuliskan verdict yang berselisih dengan bukti. `verify_output` memeriksa deliverable yang sudah jadi secara independen.

## Satu implementasi sesi

CLI, GUI, dan evaluasi berbagi `agent/session.py`, mencegah kegagalan klasik di mana demo yang mengkilap menempuh jalur berbeda dari sistem yang diukur.

## Rantai bukti deterministik

Pembangkitan ground motion bersifat deterministik dari input di dalam repositori. Rantai evaluasinya karena itu bisa dijalankan ulang tanpa mengunduh basis data rekaman eksternal atau bergantung pada dataset jarak jauh yang bisa berubah.

## Pipeline yang sama untuk semua bangunan

Model strukturnya terparameterisasi untuk rangka geser 1–20 lantai, kelas okupansi apa pun, dan lokasi dalam pita bahaya benchmark. Kesepuluh kasus — dari rumah sakit hingga gudang, 2 sampai 12 lantai — melewati alur yang sama tanpa modifikasi kode per kasus.

---

# Desain evaluasi

## Metrik utama

**Jumlah brief yang terselesaikan dengan benar.**

Evaluator yang sama dan sepuluh brief yang sama dipakai sepanjang pengembangan.

Submission akhir disimulasikan ulang secara independen sebelum diskor. Sebuah brief dihitung benar bila verdict "lanjutkan" bertahan pada re-simulasi itu untuk brief yang layak, atau bila brief yang mustahil ditandai — bukan dipaksakan.

## Kenapa sepuluh kasus?

Benchmark-nya mencakup tipe dan ketinggian bangunan yang berbeda, dan memuat satu kasus tantangan yang sengaja dibuat mustahil. Kasus-kasusnya sintetis supaya bisa dibagikan dan direproduksi tanpa data klien atau data pribadi.

## Prinsip perbandingan yang adil

Baseline dan sistem akhir menghadapi model struktur, ground motion, batas kinerja, dan aturan evaluasi yang sama. Perbandingannya karena itu mengukur perbedaan **alur kerja** di dalam benchmark ini, bukan perbedaan asumsi fisika yang mendasarinya.

---

# Improvement Changelog

Evaluator dan sepuluh brief benchmark tetap sama sepanjang perjalanan ini. Metrik utamanya: **brief yang terselesaikan dengan benar**.

| Tahap | Apa yang dicoba dan mengapa | Bukti | Keputusan / pelajaran |
|---|---|---|---|
| **Baseline** | Sizing rumus praktis satu-tembakan — mewakili lintasan pertama insinyur kompeten atau jawaban gaya LLM mentah sebelum verifikasi nonlinear | **3/10**; keliru bilang "lanjutkan" pada kasus yang mustahil | Menetapkan bottleneck sebenarnya: sizing yang percaya diri sering salah di lokasi menuntut |
| **Iterasi 1 — kalibrasi si pemeriksa** | Loop fisika pertama memakai sintesis motion Kanai-Tajimi polos | Sapuan 50 titik pada brief rumah sakit: **0 desain lolos**; tiap kandidat gagal di mana-mana | Yang salah pemeriksanya, bukan ruang desainnya. Energi periode-panjang tanpa filter membuat isolasi praktis mustahil. Ditambahkan tahap high-pass Clough-Penzien |
| **Iterasi 2 — rancang ulang pencarian** | Penghalusan lokal murni berbasis kegagalan: perbaiki pemeriksaan terburuk, jalankan ulang | Kasus rumah sakit sulit berosilasi 15 iterasi tanpa konvergen | **Dibuang** sebagai strategi tunggal. Constraint yang terkopel membuat langkah kegagalan-tunggal saling mengejar. Diganti penyaringan kasar → penghalusan; kasus yang sama lalu konvergen setelah screening + 1 langkah |
| **Iterasi 3 — jujurkan variabilitas rekaman** | Suite lima rekaman dengan seed deterministik per brief | Envelope perpindahan residual melewati batasnya untuk tiap kandidat, padahal demand puncak semuanya wajar | Offset residual didominasi realisasi. Kriterianya di-rebase menjadi envelope atas suite, bukan toleransi per rekaman |
| **Iterasi 4 — pelaporan bergerbang bukti** | `write_report` menyimulasikan ulang dan memveto verdict yang bertentangan; `verify_output` memeriksa deliverable secara independen | Sapuan eksaustif 75 titik memastikan brief mustahil itu punya 0 kandidat layak; baik jalur agent maupun manusia tidak bisa menuliskan "lanjutkan" untuknya | **Dipertahankan. Inilah perubahan yang mengubah keluaran yang terdengar masuk akal menjadi keluaran yang bisa dipertanggungjawabkan** |
| **Jalur deterministik final** | Kebijakan pencarian tertulis di atas permukaan tool simulasi yang terkunci, dipertahankan agar juri bisa mereproduksi hasil utama tanpa kunci API | **10/10**, termasuk verdict jujur "tidak layak sesuai brief" | Kontribusi utama: fisika-dalam-lingkaran plus penulis laporan yang bergerbang bukti. Dinyatakan terus terang: angka ini pencarian deterministik, bukan klaim model |
| **Unifikasi** | Mengganti jalur GUI dan CLI yang terpisah setelah ditemukan GUI melewati lapisan tool dan tidak mencatat trajectory; loop pencarian dan loop LLM yang terduplikasi sudah menyimpang | **10/10 tak berubah**; run GUI kini mereproduksi 19 evaluasi desain yang dibuat CLI untuk brief 01 | **Dipertahankan. Demo yang tidak melewati jalur terukur bukan bukti apa pun** |
| **Eksperimen intake** | Menanyakan apa yang bisa dilakukan model tapi tidak bisa dilakukan kebijakan tertulis. Menguji sepuluh proyek yang sama sebagai prosa biasa | Parser ketat menolak kesepuluh brief prosa di kesembilan field; pemeriksaan source-lock dan round-trip ditegakkan di `tests/selftest.py` | **Dipertahankan. Pemahaman bahasa adalah sumbu tempat model memberi nilai unik** |
| **Lapisan provider** | Menghapus logika spesifik-vendor yang terpatri di tiga tempat, dan memusatkan perbedaan format wire di `agent/llm.py` | Mode hybrid dan full-agent berjalan di `gpt-5.5`; antarmuka yang sama menerima `claude-opus-5` | **Dipertahankan. Permukaan tool yang hanya bekerja untuk satu vendor adalah demo vendor, bukan klaim arsitektur** |
| **Intake terukur** | Hybrid Evidence Agent: model membaca prosa, kebijakan tertulis mencari | **10/10**, 71,3 s, **8.421 in / 2.081 out**; parser ketat mendapat 0/10 pada prosa yang sama; desain yang diserahkan identik dengan jalur deterministik pada kesepuluh brief | Kontribusi model nyata dan spesifik: ia mengubah apa yang bisa dibaca sistem, bukan apa yang disimpulkannya |
| **Agensi penuh terukur** | Full-Agent Experimental Mode: model membaca prosa **dan** menyetir pencarian | **10/10**, 337,8 s, **518.386 in / 17.272 out** | Skor teknik sama dengan 62× token input. Tetap disimpan karena hasil negatif itulah temuan arsitekturnya |
| **Pengerasan** | Pass adversarial atas harness evaluasi: menilai desain persis sebagaimana diserahkan alih-alih menjepitnya lebih dulu; suite motion yang merosot menjadi pemeriksaan tak terpenuhi, bukan infinity yang tak bisa di-parse; penghalusan membaca kandidat yang ditanyakan, bukan state simulasi basi; GUI menjalankan simulasi satu per satu | **10/10 tak berubah** pada evaluator dan brief yang sama | **Dipertahankan. Hasilnya bertahan di bawah harness yang lebih ketat setelah dua jalur yang menyanjung dihapus** |

---

# Apa yang gagal — dan kenapa itu penting

Kegagalan terpenting bukan halusinasi LLM.

Dua kali, semua kandidat tampak salah karena **harness verifikasinya sendiri yang salah**:

1. pembangkit motion pertama membawa energi periode-panjang yang tidak fisis, sehingga tiap kandidat isolasi gagal;
2. kriteria perpindahan residual pertama memperlakukan keadaan-akhir yang bergantung realisasi seolah-olah besaran yang stabil dan terulang.

Dari situ lahir pelajaran agent-teknik terpenting proyek ini:

> **Agent yang paling berbahaya bukan yang gagal. Melainkan yang berhasil mengoptimasi terhadap verifier yang salah.**

Simulasi-dalam-lingkaran menjadikan simulator bagian dari attack surface sistem. Agent yang cakap menghadapi pemeriksa yang salah kalibrasi mungkin sama sekali tidak terlihat rusak — ia bisa konvergen dengan efisien dan percaya diri ke tempat yang salah.

Maka urutan yang benar adalah:

1. kalibrasi ujiannya;
2. sapu ruang desainnya;
3. pastikan masalah yang layak memang punya solusi, dan yang mustahil memang tidak;
4. baru izinkan agent mengoptimasi terhadap ujian itu.

Dan setelah optimasi, beri lapisan pelaporan hak untuk berkata **tidak**.

---

# Pelajaran seharga 518 ribu token

Kami menghabiskan **518.386 token input** untuk menjawab satu pertanyaan yang ternyata lebih berharga daripada satu poin tambahan di benchmark:

> **Di mana seharusnya agensi itu tinggal?**

Pada sepuluh kasus yang identik:

- membiarkan model membaca brief manusia **tak tergantikan** untuk menangani prosa bebas;
- membiarkan model **juga** menyetir pencarian desain terstruktur menghasilkan **nol kasus benar tambahan**;
- agensi ekstra itu berbiaya 62× token input dan 4,7× waktu dibanding jalur hybrid.

Pelajarannya bukan "agent itu buruk". Yang lebih berguna:

> **Tempatkan model di tempat ambiguitasnya, bukan otomatis di tempat lingkarannya.**

Kalau strateginya sudah bisa dikodekan dengan andal, pencarian deterministik justru bisa menjadi pilihan yang lebih agentik dalam pengertian sistem: lebih murah, bisa diaudit, bisa direproduksi, dan lebih mudah dibatasi.

Seandainya kami hanya melaporkan satu angka — "agentik vs baseline" — kami akan mengkredit pencarian desain atas perbaikan yang sebenarnya dimenangkan oleh pemahaman bahasa dan verifikasi.

---

# Cakupan, Review, dan Keselamatan

SeismoForge menghasilkan **studi prototipe tahap konsep, bukan dokumen konstruksi.**

Setiap deliverable CLI, GUI, dan baseline membawa notice itu.

- **Review insinyur berlisensi bersifat wajib.** Seorang insinyur struktur harus mereview dan menandatangani tiap laporan sebelum laporan itu memengaruhi desain, pengadaan, atau konstruksi. Tugas sistem ini adalah membawakan reviewer sebuah titik awal yang bisa dipertahankan beserta buktinya — bukan menggantikan penilaian profesional atau kewenangan stempel.
- **Tidak ada aksi konsekuensial yang diotomatiskan.** SeismoForge membaca brief, menjalankan simulasi, dan menulis berkas di bawah `outputs/`. Ia tidak memesan peralatan, tidak mengajukan izin, tidak menerbitkan gambar, tidak mengirim instruksi, dan tidak melakukan aksi fisik apa pun.
- **Asumsi benchmark bersifat internal.** Batas penerimaan, kelas model struktur, dan ground motion di `forge/building.py` serta `forge/motions.py` terinspirasi praktik performance-based engineering, tetapi **bukan** analisis bahaya spesifik-lokasi yang patuh kode untuk lokasi nyata mana pun.
- **Kesepuluh brief benchmark bersifat sintetis.** Repositori ini tidak memuat data klien, lokasi privat, atau data pribadi. Mode berbasis model hanya mengirim teks brief dan hasil tool ke API terpilih. Kunci API dibaca dari environment atau ditahan di memori, dan tidak pernah ditulis ke disk.
- **Laporan dirancang untuk bisa diaudit.** Tiap nilai di tabel bisa ditelusuri ke sebuah simulasi, narasi hasil model diberi label sebagai komentar tanpa verifikasi, dan riwayat pencarian mencatat tiap kandidat yang dicoba dan ditolak sebelum verdict akhir.

---

# Keterbatasan Pemodelan yang Diketahui

Hasil **3/10 → 10/10** adalah perbandingan **di dalam benchmark yang sengaja dibuat sempit ini.**

Penyederhanaan berikut memengaruhi nilai demand absolutnya. Semuanya **diungkapkan**, bukan diperbaiki diam-diam, karena mengubahnya di ujung eksperimen akan menuntut kalibrasi ulang benchmark dan penetapan ulang ground truth.

| Penyederhanaan | Dampaknya pada angka |
|---|---|
| Redaman Rayleigh di-anchor pada **eigenvalue pra-leleh** di `forge/simulate.py` | Suku proporsional-massa terlalu meredam ragam isolasi pasca-leleh — sekitar 4–6%, bukan 2% yang dinyatakan laporan — sehingga perpindahan isolator dan offset residual terlalu rendah diprediksi |
| Rangka **1 lantai bertumpu tetap** hanya mengembalikan satu ragam, sehingga redaman Rayleigh tidak diterapkan padahal blok kalibrasi masih menyatakan 5% | Hanya memengaruhi kasus 1 lantai bertumpu tetap; tiap brief benchmark di sini minimal 2 lantai |
| Model terisolasi membawa **n+1 massa lantai** — base mat plus n lantai — sementara `isolation_period`, `kd_for_period`, dan `seismic_weight` memakai n | Periode isolasi terealisasi lebih panjang dari yang dilaporkan sebesar `sqrt((n+1)/n)`, dan koefisien base shear membengkak dengan rasio itu; efeknya terbesar pada bangunan rendah |
| **Offset residual** disampel di ujung ekor getaran bebas 10 detik | Ia snapshot bergantung fase dari osilasi periode-panjang yang teredam ringan, sehingga lolos/gagal antar rekaman membawa derau. Karena itulah kriterianya memakai envelope atas suite, bukan toleransi per rekaman |
| **Sudut high-pass Clough-Penzien 0,22 Hz** dan batas bawah grid spektral meredam pita isolasi 1,8–4,5 s | Suite sedikit kurang mengeksitasi perpindahan isolator — justru demand yang ingin dibatasi oleh pemeriksaan moat |
| **Seed suite rekaman diturunkan dari nama berkas brief** di `forge/brief_parser.py` | Berkas brief identik tereproduksi bit-per-bit, tetapi teks identik dengan nama berkas berbeda mendapat suite berbeda. Run GUI dinamai `user_brief`, jadi run GUI dan CLI atas teks identik belum tentu memakai suite yang sama |
| `evaluation/ground_truth.json` adalah **peta kelayakan yang dipelihara manual** | Ditetapkan lewat sapuan eksaustif — termasuk 75 titik untuk brief 10 — tetapi tidak meregenerasi dirinya. Ubah fisika atau batas penerimaannya, dan peta kelayakan itu harus dibuktikan ulang |

Keterbatasan ini membatasi **makna** demand teknik absolutnya. Ia **tidak** menciptakan keunggulan asimetris dalam perbandingan benchmark yang dilaporkan, karena baseline dan sistem akhir menghadapi model struktur, motion, dan batas yang sama.

---

# Reproduksibilitas

Seorang juri harus bisa berangkat dari environment bersih dan mereproduksi klaim utamanya, tanpa perlu memercayai tangkapan layar atau demo yang di-host.

Repositori ini memuat:

- kode fisika dan pembangkitan motion yang deterministik;
- kesepuluh brief evaluasi;
- sepuluh brief prosa bebas yang setara;
- baseline;
- harness evaluasi dan hasil yang di-commit;
- instruksi kedua agent;
- trajectory representatif;
- contoh deliverable;
- jalur deterministik tanpa kunci API untuk hasil teknik utamanya.

Lihat **`REPRODUCTION.md`** untuk penyiapan environment, perintah persis, output yang diharapkan, versi, perkiraan runtime, dan detail eksekusi yang bergantung model.

Karena mode deterministik mereproduksi hasil 10/10 tanpa kunci API, juri bisa memverifikasi hasil utamanya terlepas dari ketersediaan model. Akses model hanya diperlukan untuk mereproduksi eksperimen intake prosa bebas dan agensi penuh.

**Catatan biaya:** tiap run melaporkan jumlah token, tetapi angka dolar hanya dicetak untuk model yang harganya tercatat di `PRICES` (`agent/llm.py`). Model yang tidak dikenali melaporkan tokennya dan menyatakan bahwa harganya belum dikonfigurasi — alih-alih mengutip angka yang belum diperiksa siapa pun.

---

# GUI Design Center

GUI lokalnya ada di `gui/` dan hanya memakai penyajian web pustaka standar Python — tanpa dependensi framework web tambahan.

Jalankan:

```bash
python3 gui/server.py
```

Lalu buka:

```text
http://127.0.0.1:8765
```

Dari satu layar, pengguna bisa:

- mengetik atau memuat brief, dan memilih mode `offline`, `assisted`, atau `agent`;
- mengikuti **pelacak tahapan** — baca brief, konsep pertama, saring ruang desain, haluskan, tulis laporan, verifikasi — yang bergerak seiring run;
- menonton **penghitung langsung**: waktu berjalan, desain yang disimulasikan, analisis nonlinear yang dijalankan;
- memeriksa **bukti intake**: tiap nilai yang diekstrak berdampingan dengan potongan kalimat brief asalnya, beserta konversi satuan yang diterapkan;
- mengikuti **tabel kandidat**: tiap desain yang dicoba, demand penentunya terhadap batasnya, dan lolos atau tidak;
- membaca **trajectory agent** saat ia terjadi — panggilan tool, tahapan, waktu, dan setiap retry source-lock;
- membaca verdict akhir, sistem terpilih, margin, catatan teknik, basis bukti, dan lokasi trajectory yang bisa dibaca mesin beserta model dan jumlah tokennya.

Tidak ada satu pun di layar itu yang merupakan pemeranan ulang. Pelacak tahapan, tabel kandidat, dan panel trajectory semuanya dirender dari **berkas trajectory milik run itu sendiri** selagi ditulis — sehingga layar tidak bisa mengklaim langkah yang tidak benar-benar diambil.

Kunci API hanya disimpan di memori. Mengosongkan kolom kunci akan memakai kunci di environment server — yang juga cara merekam demo tanpa kunci tampil di layar.

Yang terpenting, GUI **tidak** menjalankan jalur demo khusus. Ia masuk ke alur `agent/session.py` yang sama dengan CLI dan evaluasi, dan mencatat trajectory-nya di `trajectories/gui/`.

---

# Apa yang sudah ada sebelum hackathon

Komponen yang sudah ada:

- OpenSeesPy;
- NumPy;
- Anthropic SDK;
- OpenAI SDK;
- pengetahuan domain teknik struktur milik penulis.

Dibangun selama hackathon:

- inti fisika struktur;
- sintesis ground motion;
- brief benchmark;
- set intake prosa bebas;
- kedua agent beserta instruksinya;
- baseline;
- kebijakan pencarian desain;
- pembangkitan laporan bergerbang bukti;
- harness verifikasi;
- kerangka evaluasi;
- GUI;
- abstraksi provider;
- trajectory;
- dokumentasi.

Dua agent dipakai di repositori ini:

- `agent/system_prompt.md` — instruksi agent desain;
- `agent/intake_prompt.md` — instruksi agent pembaca brief.

Trajectory keduanya disertakan di `trajectories/`.

**Disclosure coding agent:** proyek ini dibangun dengan Claude Code; trajectory pengembangannya tersedia bila diminta.

---

# Peta Repositori

```text
briefs/              10 brief proyek format ketat, dipakai sebagai kasus evaluasi

briefs_prose/        10 proyek yang sama ditulis sebagai prosa biasa, untuk menguji intake

gui/                 design center web lokal

forge/               inti fisika teknik:
                     model bangunan, sintesis ground motion, RHA OpenSees,
                     pemeriksaan penerimaan, aturan sizing, kebijakan desain,
                     perender laporan

agent/               session.py      satu-satunya pintu masuk eksekusi
                     tools.py        9 tool teknik
                     llm.py          abstraksi provider
                     intake.py       pembaca brief prosa bebas
                     system_prompt.md
                     intake_prompt.md

baselines/           baseline satu-tembakan tanpa verifikasi

evaluation/          ground truth, harness juri, hasil yang di-commit

outputs/             deliverable per brief:
                     design_report.md + design.json

trajectories/        trajectory run representatif dalam JSONL + Markdown;
                     run GUI juga terekam

tests/               selftest.py:
                     parser, fisika, kebijakan, source/evidence lock,
                     kasus bukti terdegradasi, integritas juri

tools/               utilitas kalibrasi pengembangan:
                     sapuan, smoke test

video/               slot video solusi <=5 menit + outline

LICENSE              MIT + notice tahap-konsep / bukan-untuk-konstruksi
```

---

# Alur Cerita Video Solusi

Cerita <=5 menit yang disarankan sengaja dibuat sederhana:

1. **Masalahnya:** konsep seismik yang terdengar masuk akal bisa salah tanpa verifikasi nonlinear.
2. **Baseline-nya:** 3/10, dan "lanjutkan" yang keliru pada brief yang mustahil.
3. **Satu run penuh:** rumah sakit pesisir, dari brief manusia → kandidat → OpenSees → iterasi → laporan bergerbang bukti.
4. **Hasilnya:** 3/10 → 10/10.
5. **Eksperimen yang dibuang:** penghalusan lokal murni yang berosilasi 15 iterasi.
6. **Temuan yang mengejutkan:** menyerahkan pencarian desain kepada model memberi 10/10 yang sama, dengan 518.386 token input berbanding 8.421.
7. **Hot take-nya:** agent teknik yang andal butuh verifier yang terkalibrasi, dan batas yang jelas tentang di mana agensi benar-benar menambah nilai.

Outline lengkap ada di `video/README.md`.

---

# Kesimpulan Akhir

Kami mulai dengan bertanya:

> **Bisakah sebuah agent merancang konsep perlindungan gempa?**

Pertanyaan yang ternyata lebih berguna adalah:

> **Bagian mana dari pekerjaan teknik yang boleh dimiliki sebuah agent?**

Benchmark ini menghasilkan tiga jawaban.

**Pertama:** desain satu-tembakan yang terdengar masuk akal tidak cukup. Baseline mendapat **3/10**.

**Kedua:** fisika-dalam-lingkaran ditambah pelaporan bergerbang bukti bisa mengubahnya menjadi **10/10** di dalam benchmark ini — termasuk kemampuan menolak brief yang mustahil.

**Ketiga:** otonomi lebih besar tidak otomatis berarti kemampuan lebih besar. Kendali model penuh atas pencarian desain menyamai hasil hybrid, tetapi memakai **62× token input**.

Jadi SeismoForge tidak dibangun di atas gagasan bahwa AI sebaiknya mengerjakan segalanya.

Ia dibangun di atas prinsip yang lebih ketat:

> **Biarkan model menyelesaikan ambiguitas. Biarkan perkakas deterministik menghitung. Biarkan simulasi menantang usulannya. Biarkan bukti mengendalikan klaimnya. Dan biarkan insinyur tetap bertanggung jawab atas keputusannya.**

Itulah arsitektur yang sedang diuji SeismoForge.
