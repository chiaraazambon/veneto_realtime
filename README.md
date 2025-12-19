# Veneto Realtime Snow
Questo repository contiene gli **script Python** e la **documentazione**
per il preprocessing dei dati meteorologici e per le simulazioni **GEOtop**
relative alla regione **VENETO**.

Il focus è sulla gestione dei file **SMET** provenienti da:
- **APOLLO** (storico)
- **INGESTION** (nuovi dati ARPAV)

e sulla loro preparazione per le simulazioni operative.

## Requirements

- Python **≥ 3.10**
- Librerie Python (vedi `pyproject.toml`)
- Accesso ai file SMET APOLLO e INGESTION


## Usage
I seguenti script devono essere eseguiti **in sequenza** per il preprocessing dei nuovi dati INGESTION.

```sh

# Correzione PSUM (units_multiplier)
python scripts/psum_multiplicator.py
  --smet-dir ./INGESTION/arpav_YYYY-MM-DD_YYYY-MM-DD

# Filtraggio stazioni di interesse (222 → 111)
python scripts/filtraggio_ingestion_smet.py
  --dir-ref ./INGESTION/smet_ref_05-12
  --dir-all ./INGESTION/arpav_YYYY-MM-DD_YYYY-MM-DD
  --out-dir ./INGESTION/arpav_filtrati

# Rinomina header + station_id (JSON + Excel)
python scripts/fix_ingestion_smet.py
  --json-path ./config/anagrafica_stazioni.jsonl
  --xlsx-path ./config/rename_id.xlsx

# Fix header da APOLLO per subset di stazioni
python scripts/fix_header.py

# 5) Preprocess dati meteorologici
cd meteo
mf process PM0_Local.yml 
mf process PM1_integr.yml 
mf process PM2_snow.yml 

# Append APOLLO + INGESTION
for f in smet_APOLLO/*.smet; do
  mf combine-smet "$f" "2_outSNOW/$(basename "$f")"
done

```

## Workflow
Dopo aver scaricato i nuovi dati INGESTION (circa 222 file SMET)
e gli ultimi file SMET aggiornati dal server APOLLO,
si procede alla standardizzazione dei dati INGESTION.

### a. Correzione PSUM
Verificare che il campo units_multiplier associato a PSUM
nei file SMET di INGESTION sia uguale a 1.
Se non lo è, correggerlo tramite lo script `psum_multiplicator.py`.

### b. Filtraggio dei dati INGESTION
Utilizzando come riferimento la cartella `smet_ref_05-12`
presente nel repository, filtrare i nuovi dati INGESTION
(riducendo i file da 222 a 111).

### c. Rinomina e standardizzazione header
Poiché i dati originali presentano metadati non omogenei,
gli header SMET vengono riscritti facendo riferimento:
- al file JSON di anagrafica presente nella cartella `config`
- al file Excel di mapping ID, per le stazioni non presenti nel JSON

Questo step standardizza:
- station_id
- coordinate
- metadati principali
- nome del file SMET

### d. Preprocess e append
Dalla cartella meteo, eseguire i preprocess:
- PM0
- PM1
- PM2

Nota:
- alcune stazioni non vengono appendate
per mancanza di estensione temporale
- per la stazione di Passo Falzarego, dopo il primo append,
è necessario eseguire un secondo append con il rispettivo
nivometro (347.smet), previa modifica dell’header di 347.smet
sulla base dello SMET 37.smet


### e. Simulazione
Una volta completato l’append, i file sono pronti per:
- la generazione dei mgrids
- il lancio della simulazione GEOtop

### Documentazione completa
La descrizione dettagliata del workflow operativo,
inclusi i controlli da effettuare e i casi particolari,
è disponibile in:
`docs/workflow_veneto_realtime_dec2025.md`
