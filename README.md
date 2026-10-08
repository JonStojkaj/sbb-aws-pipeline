# SBB Real-Time Data Engineering Pipeline

## Übersicht

Die Pipeline ruft Fahrplandaten des Zürcher Hauptbahnhofs ab, legt die
Rohdaten in S3 ab und schreibt die aufbereiteten Abfahrten in PostgreSQL.
Ein Streamlit-Dashboard stellt die Daten für Kontrollen und Auswertungen dar.

Die Infrastruktur wird mit Terraform beschrieben, der Deploy läuft über
GitHub Actions.

## Ablauf

1. Die Lambda-Funktion lädt die aktuellen Daten von `transport.opendata.ch`.
2. Die unveränderte API-Antwort wird in S3 gespeichert.
3. Die Abfahrten werden aus der Antwort gelesen und in RDS PostgreSQL eingefügt.
4. Das Dashboard zeigt Status, Verspätungen und abgeleitete Zeitmerkmale.

## Verwendete Komponenten

- AWS Lambda
- Amazon S3
- Amazon RDS for PostgreSQL
- AWS Systems Manager Parameter Store
- Terraform
- GitHub Actions
- Python und Streamlit

## Voraussetzungen

- Python 3.12 oder neuer
- Zugriff auf eine PostgreSQL-Datenbank mit der Tabelle `departures`
- Für AWS-Bereitstellungen: AWS CLI, Terraform und ein AWS-Konto

## Konfiguration

Passwörter gehören nicht in den Quelltext. Für das Dashboard und
`setup_db.py` werden `DB_HOST`, `DB_PASSWORD` sowie optional `DB_USER` und
`DB_NAME` als Umgebungsvariablen gesetzt.

Das Dashboard lädt diese Werte aus einer lokalen `.env`-Datei. Diese Datei
bleibt durch `.gitignore` lokal und darf nicht committed werden. Für Terraform
gibt es unter `terraform/terraform.tfvars.example` nur eine Vorlage ohne
echtes Passwort.

Die Lambda-Funktion liest das Passwort aus dem Parameter
`/sbb/db_password` im AWS Systems Manager Parameter Store. Zusätzlich benötigt
sie `DB_HOST` und `S3_BUCKET_NAME` als Umgebungsvariablen.

Ein frischer Clone enthält keine AWS-Zugangsdaten, keine Datenbank und keine
Beispieldaten. Für eine lokale Nutzung müssen daher eigene Datenbankdaten
eingetragen werden. Für den Lambda-Betrieb müssen die AWS-Ressourcen und der
Parameter Store zuerst im eigenen AWS-Konto eingerichtet werden.

## Dashboard lokal starten

```bash
git clone https://github.com/JonStojkaj/sbb-aws-pipeline.git
cd sbb-aws-pipeline
pip install -r requirements.txt
streamlit run dashboard.py
```

Erstelle dafür eine lokale `.env`-Datei:

```env
DB_HOST=dein-rds-endpoint
DB_PASSWORD=dein-datenbankpasswort
DB_USER=postgres
DB_NAME=postgres
```

Das Passwort steht nur in dieser lokalen Datei. Für Lambda liegt es als
`SecureString` unter `/sbb/db_password` im AWS Systems Manager Parameter Store.
Für Terraform wird das Passwort nur lokal in `terraform/terraform.tfvars`
gesetzt. Beide Dateien werden nicht committed.

## Datenbank einrichten

Nachdem die Umgebungsvariablen gesetzt sind, erstellt dieses Kommando die
Tabelle in der angegebenen Datenbank:

```bash
python setup_db.py
```

## AWS deployen

Pushes auf `main` starten den Workflow in
`.github/workflows/deploy.yml`. Dafür müssen im GitHub-Repository die Actions
Secrets `AWS_ACCESS_KEY_ID` und `AWS_SECRET_ACCESS_KEY` hinterlegt sein.
Die Lambda-Funktion muss im selben AWS-Konto und in der Region `eu-north-1`
existieren. Ihr Name ist `sbb-extraction-pipeline`.

### Region und Funktionsname in AWS prüfen

1. Öffne die AWS-Konsole und wähle oben rechts die Region aus.
2. Öffne **Services** → **Lambda**.
3. Suche nach `sbb-extraction-pipeline`.
4. Wenn die Funktion nicht erscheint, wähle oben rechts nacheinander die
   Regionen aus, in denen du sie angelegt haben könntest.
5. Öffne die Funktion. Die aktuell ausgewählte Region steht weiterhin oben
   rechts in der AWS-Konsole. Diese Region muss im Workflow bei `aws-region`
   und in Terraform übereinstimmen.

Der aktuelle Workflow und die Terraform-Konfiguration verwenden `eu-north-1`
(Stockholm). Wenn die Funktion in einer anderen Region liegt, muss
`aws-region` in `.github/workflows/deploy.yml` und `region` in
`terraform/main.tf` auf denselben Wert geändert werden.
