# Demo Checklist: Retail Operations Control Tower

Checklist untuk menjalankan demo end-to-end dari project ini. Setiap langkah
diverifikasi dengan output yang diharapkan.

---

## Prasyarat

- [ ] Python 3.11+ terinstal
- [ ] uv terinstal (atau pip sebagai alternatif)
- [ ] Repository sudah di-clone ke direktori lokal
- [ ] Koneksi internet untuk install dependencies (sekali saja)

---

## Langkah 1: Setup environment

```bash
cd retail-ops-control-tower

# Buat virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"
```

Verifikasi:

- [ ] Tidak ada error saat install
- [ ] `python -c "import streamlit"` berhasil (tidak error)
- [ ] `python -c "import pandas"` berhasil

---

## Langkah 2: Generate sample data

```bash
python scripts/generate_sample_data.py
```

Verifikasi:

- [ ] 8 file CSV muncul di `data/sample/`:
  - [ ] `stores.csv` (100 baris + header)
  - [ ] `campaigns.csv` (3 baris + header)
  - [ ] `allocation_plan.csv` (~1,410 baris + header)
  - [ ] `dispatch.csv` (~1,410 baris + header)
  - [ ] `store_confirmations.csv` (~1,366 baris + header)
  - [ ] `photo_proofs.csv` (~3,091 baris + header)
  - [ ] `sales_daily.csv` (~39,480 baris + header)
  - [ ] `issues.csv` (~123 baris + header)
- [ ] Output di terminal menampilkan jumlah baris per tabel
- [ ] Re-running dengan seed yang sama menghasilkan output identik

---

## Langkah 3: Build exception table dan action list

```bash
python scripts/build_exception_table.py --aging-date 2026-07-15
```

Verifikasi:

- [ ] `data/processed/exceptions.csv` muncul (~1,603 exceptions)
- [ ] `data/processed/daily_action_list.csv` muncul (~1,603 action items)
- [ ] Output di terminal menampilkan breakdown per exception type:
  - [ ] missing_confirmation
  - [ ] late_confirmation
  - [ ] quantity_mismatch
  - [ ] missing_photo_proof
  - [ ] late_photo_proof
  - [ ] stockout_risk
  - [ ] overstock_risk
  - [ ] low_sell_through
  - [ ] unresolved_issue_sla_breach

---

## Langkah 4: Build KPI summary dan AM scorecard

```bash
python scripts/build_kpi_summary.py --aging-date 2026-07-15
```

Verifikasi:

- [ ] `data/processed/kpi_summary.csv` muncul (12 KPIs)
- [ ] `data/processed/am_scorecard.csv` muncul (10 area managers)
- [ ] KPI summary berisi:
  - [ ] 5 process KPIs (readiness, confirmation, photo proof, allocation
        accuracy, mismatch rate)
  - [ ] 7 performance KPIs (exception rate, open count, SLA breach, sell-through,
        stockout risk, overstock risk, AM backlog)
- [ ] AM scorecard menampilkan per-AM: store count, allocation count, open
      exceptions, critical count, SLA breach count

---

## Langkah 5: Generate weekly report

```bash
python scripts/generate_weekly_report.py --aging-date 2026-07-15
```

Verifikasi:

- [ ] `reports/weekly_ops_report.md` muncul (8 section)
- [ ] `reports/executive_summary.md` muncul
- [ ] Weekly report berisi section:
  - [ ] 1. Executive Snapshot
  - [ ] 2. Campaign Readiness
  - [ ] 3. Allocation Reconciliation
  - [ ] 4. Exception Backlog
  - [ ] 5. AM / Store Follow-Up List
  - [ ] 6. Sales / Sell-Through Note
  - [ ] 7. Recommended Actions (top 10)
  - [ ] 8. Data Caveats
- [ ] Executive summary menampilkan top 5 action items dalam tabel

---

## Langkah 6: Generate validation summary

```bash
python scripts/generate_validation_summary.py
```

Verifikasi:

- [ ] `reports/validation_summary.md` muncul
- [ ] Menampilkan total findings (warning count > 0)
- [ ] Menampilkan findings per rule (VAL-01 sampai VAL-09)
- [ ] Menampilkan row counts per tabel yang divalidasi

---

## Langkah 7: Jalankan Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

Verifikasi:

- [ ] Browser terbuka ke http://localhost:8501
- [ ] Dashboard menampilkan:
  - [ ] KPI tiles (process dan performance)
  - [ ] Campaign readiness table
  - [ ] Allocation reconciliation table
  - [ ] Exception backlog dengan filter
  - [ ] AM scorecard table
  - [ ] Weekly report section (inline markdown)
- [ ] Filter sidebar berfungsi:
  - [ ] Filter campaign (multi-select)
  - [ ] Filter region (multi-select)
  - [ ] Filter area manager (multi-select)
- [ ] Tidak ada error message di dashboard

---

## Langkah 8: Jalankan test suite

```bash
pytest -q
```

Verifikasi:

- [ ] Semua test lulus (327 passed)
- [ ] Tidak ada failure
- [ ] Runtime di bawah 30 detik

---

## Langkah 9: Verifikasi architecture diagram

```bash
python scripts/render_architecture_diagram.py
```

Verifikasi:

- [ ] `docs/architecture.png` ter-generate (PNG, minimal 1600px lebar)
- [ ] `docs/architecture.html` ter-generate (interactive HTML)
- [ ] PNG menampilkan 5 stage: intake, normalize, validate, prioritize, report
- [ ] HTML dapat dibuka di browser

---

## Langkah 10: Verifikasi CLI commands

```bash
python -m retail_ops_control_tower --help
```

Verifikasi:

- [ ] Help menampilkan 3 subcommand: generate-data, build-exceptions, report
- [ ] `python -m retail_ops_control_tower generate-data --help` menampilkan
      argumen: --stores, --skus, --days, --seed, --output-dir

---

## Checklist demo cepat (jika waktu terbatas)

Jika hanya ada 5 menit untuk demo, jalankan langkah-langkah berikut:

1. `pytest -q` (tunjukkan 327 test lulus)
2. `streamlit run dashboard/app.py` (tunjukkan dashboard interaktif)
3. Buka `reports/weekly_ops_report.md` (tunjukkan 8-section report)
4. Buka `docs/architecture.png` (tunjukkan diagram 5-stage)
5. Buka `data/processed/exceptions.csv` (tunjukkan ranked action list)

---

## Troubleshooting

**Streamlit tidak bisa start:**

- Pastikan virtual environment sudah di-activate
- Pastikan streamlit terinstall: `uv pip install streamlit`
- Coba jalankan dengan flag headless: `streamlit run dashboard/app.py --server.headless true`

**Dashboard menampilkan "Generated sample or processed data is missing":**

- Jalankan langkah 2-4 terlebih dahulu untuk generate data
- Dashboard membaca dari `data/sample/` dan `data/processed/`

**Test failure:**

- Pastikan semua dependencies terinstall: `uv pip install -e ".[dev]"`
- Pastikan tidak ada file yang dimodifikasi di `data/sample/` atau
  `data/processed/`
- Coba regenerate data: `python scripts/generate_sample_data.py`
