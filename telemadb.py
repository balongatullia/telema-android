import sqlite3, os, datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'utilisateur',
    paroisse_id INTEGER
);
CREATE TABLE IF NOT EXISTS paroisses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL, adresse TEXT, responsable TEXT, telephone TEXT
);
CREATE TABLE IF NOT EXISTS membres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL, prenom TEXT, sexe TEXT, date_naissance TEXT,
    telephone TEXT, email TEXT, paroisse_id INTEGER, fonction TEXT,
    date_adhesion TEXT, statut TEXT DEFAULT 'Actif',
    groupe_sanguin TEXT, profession TEXT, adresse TEXT, section TEXT,
    date_bapteme TEXT, date_communion TEXT, date_confirmation TEXT,
    date_mariage TEXT, ordre_voeux_perpetuels TEXT,
    autres_engagements_apostoliques TEXT, paroisses_anterieures TEXT
);
CREATE TABLE IF NOT EXISTS inscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    membre_id INTEGER, date_inscription TEXT, session TEXT,
    montant REAL DEFAULT 0, statut TEXT DEFAULT 'En attente', valide_par TEXT,
    annee_pastorale_id INTEGER
);
CREATE TABLE IF NOT EXISTS activites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL, type TEXT, date_debut TEXT, date_fin TEXT,
    lieu TEXT, responsable TEXT, description TEXT, annee_pastorale_id INTEGER
);
CREATE TABLE IF NOT EXISTS presences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activite_id INTEGER, membre_id INTEGER, statut TEXT DEFAULT 'Present', remarque TEXT
);
CREATE TABLE IF NOT EXISTS comptes_rendus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activite_id INTEGER, contenu TEXT, redacteur TEXT, date_redaction TEXT
);
CREATE TABLE IF NOT EXISTS cotisations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    membre_id INTEGER, annee_pastorale_id INTEGER, montant_du REAL DEFAULT 0,
    montant_paye REAL DEFAULT 0, statut TEXT DEFAULT 'Impaye'
);
CREATE TABLE IF NOT EXISTS paiements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    membre_id INTEGER, type_frais TEXT, libelle TEXT, montant REAL DEFAULT 0,
    date_paiement TEXT, mode TEXT, reference TEXT, annee_pastorale_id INTEGER
);
CREATE TABLE IF NOT EXISTS finances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_operation TEXT, categorie TEXT, montant REAL DEFAULT 0,
    date_operation TEXT, description TEXT, annee_pastorale_id INTEGER
);
CREATE TABLE IF NOT EXISTS frais_extra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    libelle TEXT, membre_id INTEGER, montant REAL DEFAULT 0,
    date_frais TEXT, statut TEXT DEFAULT 'Impaye', annee_pastorale_id INTEGER
);
CREATE TABLE IF NOT EXISTS rh (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    membre_id INTEGER, fonction TEXT, commission TEXT,
    date_debut_mandat TEXT, date_fin_mandat TEXT
);
CREATE TABLE IF NOT EXISTS cas_sociaux (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    membre_id INTEGER, nature TEXT, description TEXT, aide_apportee TEXT,
    montant_aide REAL DEFAULT 0, statut TEXT DEFAULT 'En cours', date_signalement TEXT,
    annee_pastorale_id INTEGER
);
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL, categorie TEXT, date_ajout TEXT, fichier TEXT, description TEXT
);
CREATE TABLE IF NOT EXISTS annees_pastorales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    libelle TEXT NOT NULL, date_debut TEXT NOT NULL, date_fin TEXT NOT NULL, active INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS historique (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_heure TEXT, utilisateur TEXT, action TEXT, details TEXT
);
"""

def annee_pastorale_pour_date(d):
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d[:10])
    debut_annee = d.year if d.month >= 9 else d.year - 1
    return f"{debut_annee}-09-01", f"{debut_annee + 1}-08-31", f"{debut_annee}-{debut_annee + 1}"


class DB:
    def __init__(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "backups"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "uploads"), exist_ok=True)
        self.data_dir = data_dir
        self.path = os.path.join(data_dir, "telema.db")
        conn = self.conn()
        conn.executescript(SCHEMA)

        # Migration douce : ajoute les colonnes manquantes si la base
        # existait deja avant cette version, sans jamais toucher aux
        # donnees deja saisies.
        colonnes_users = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "paroisse_id" not in colonnes_users:
            conn.execute("ALTER TABLE users ADD COLUMN paroisse_id INTEGER")
        colonnes_membres_attendues = [
            "groupe_sanguin", "profession", "adresse", "section",
            "date_bapteme", "date_communion", "date_confirmation", "date_mariage",
            "ordre_voeux_perpetuels", "autres_engagements_apostoliques", "paroisses_anterieures",
        ]
        colonnes_membres = [r["name"] for r in conn.execute("PRAGMA table_info(membres)").fetchall()]
        for c in colonnes_membres_attendues:
            if c not in colonnes_membres:
                conn.execute(f"ALTER TABLE membres ADD COLUMN {c} TEXT")
        for table in ["cotisations", "paiements", "finances", "frais_extra", "cas_sociaux", "inscriptions", "activites"]:
            cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if "annee_pastorale_id" not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN annee_pastorale_id INTEGER")

        cur = conn.execute("SELECT COUNT(*) c FROM users")
        if cur.fetchone()["c"] == 0:
            conn.execute(
                "INSERT INTO users (username, password, role, paroisse_id) VALUES (?,?,?,?)",
                ("admin", "telema2026", "administrateur", None),
            )
        if conn.execute("SELECT COUNT(*) c FROM annees_pastorales").fetchone()["c"] == 0:
            debut, fin, libelle = annee_pastorale_pour_date(datetime.date.today())
            conn.execute(
                "INSERT INTO annees_pastorales (libelle, date_debut, date_fin, active) VALUES (?,?,?,1)",
                (libelle, debut, fin),
            )
        conn.commit()
        conn.close()

    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def obtenir_ou_creer_annee_pastorale(self, date_str):
        conn = self.conn()
        if not date_str:
            row = conn.execute("SELECT id FROM annees_pastorales WHERE active=1 LIMIT 1").fetchone()
            conn.close()
            return row["id"] if row else None
        debut, fin, libelle = annee_pastorale_pour_date(date_str)
        row = conn.execute("SELECT id FROM annees_pastorales WHERE date_debut=?", (debut,)).fetchone()
        if row:
            conn.close()
            return row["id"]
        cur = conn.execute(
            "INSERT INTO annees_pastorales (libelle, date_debut, date_fin, active) VALUES (?,?,?,0)",
            (libelle, debut, fin),
        )
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return rid

    def annee_active_id(self):
        conn = self.conn()
        row = conn.execute("SELECT id FROM annees_pastorales WHERE active=1 ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        return row["id"] if row else None

    def log(self, utilisateur, action, details=""):
        c = self.conn()
        c.execute(
            "INSERT INTO historique (date_heure, utilisateur, action, details) VALUES (?,?,?,?)",
            (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), utilisateur, action, details),
        )
        c.commit()
        c.close()

