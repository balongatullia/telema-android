"""
TELEMA - Application Android (Kivy) pour la gestion de l'Equipe de
Coordination Diocesaine de la Communaute Telema. Fonctionne entierement
hors ligne : les donnees sont stockees dans une base SQLite locale, dans le
dossier de donnees prive de l'application sur le telephone.
"""
import os
import datetime
import sqlite3

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner

from telemadb import DB

BLEU = (0x1F / 255, 0x4E / 255, 0x79 / 255, 1)
BLEU_CLAIR = (0x2E / 255, 0x74 / 255, 0xB5 / 255, 1)
ACCENT = (0x5B / 255, 0x9B / 255, 0xD5 / 255, 1)
FOND = (0.96, 0.97, 0.98, 1)
BORD = (0.89, 0.91, 0.94, 1)

# ---------------------------------------------------------------------------
# Definition des modules geres par le moteur CRUD generique (meme principe
# que la version Windows/Web : un seul ecran reutilisable pour tous les
# modules simples).
# ---------------------------------------------------------------------------
def get_membres_options(db, paroisse_id=None):
    conn = db.conn()
    if paroisse_id:
        rows = conn.execute(
            "SELECT id, nom || ' ' || IFNULL(prenom,'') AS lbl FROM membres WHERE paroisse_id=? ORDER BY nom",
            (paroisse_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT id, nom || ' ' || IFNULL(prenom,'') AS lbl FROM membres ORDER BY nom").fetchall()
    conn.close()
    return [(r["id"], r["lbl"]) for r in rows]

def get_paroisses_options(db):
    conn = db.conn()
    rows = conn.execute("SELECT id, nom FROM paroisses ORDER BY nom").fetchall()
    conn.close()
    return [(r["id"], r["nom"]) for r in rows]

def get_annees_pastorales_options(db):
    conn = db.conn()
    rows = conn.execute("SELECT id, libelle FROM annees_pastorales ORDER BY date_debut DESC").fetchall()
    conn.close()
    return [(r["id"], r["libelle"]) for r in rows]

MODULES = {
    "paroisses": {
        "table": "paroisses", "titre": "Paroisses",
        "champs": [
            ("nom", "Nom de la paroisse", "text", None),
            ("adresse", "Adresse", "text", None),
            ("responsable", "Responsable", "text", None),
            ("telephone", "Telephone", "text", None),
        ],
    },
    "membres": {
        "table": "membres", "titre": "Membres",
        "champs": [
            ("nom", "Nom", "text", None),
            ("prenom", "Prenom", "text", None),
            ("sexe", "Sexe", "select", ["Masculin", "Feminin"]),
            ("date_naissance", "Date naissance (AAAA-MM-JJ)", "text", None),
            ("telephone", "Telephone", "text", None),
            ("email", "Email", "text", None),
            ("adresse", "Adresse", "text", None),
            ("profession", "Profession", "text", None),
            ("groupe_sanguin", "Groupe sanguin", "select", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
            ("paroisse_id", "Paroisse", "fk", get_paroisses_options),
            ("paroisses_anterieures", "Paroisse(s) anterieure(s)", "text", None),
            ("section", "Section", "text", None),
            ("fonction", "Fonction", "text", None),
            ("date_adhesion", "Date adhesion (AAAA-MM-JJ)", "text", None),
            ("statut", "Statut", "select", ["Actif", "Inactif", "Suspendu"]),
            ("date_bapteme", "Bapteme (date)", "text", None),
            ("date_communion", "Communion (date)", "text", None),
            ("date_confirmation", "Confirmation (date)", "text", None),
            ("date_mariage", "Mariage (date)", "text", None),
            ("ordre_voeux_perpetuels", "Ordre ou voeux perpetuels", "text", None),
            ("autres_engagements_apostoliques", "Autres engagements apostoliques", "text", None),
        ],
    },
    "inscriptions": {
        "table": "inscriptions", "titre": "Inscriptions",
        "champs": [
            ("membre_id", "Membre", "fk", get_membres_options),
            ("date_inscription", "Date (AAAA-MM-JJ)", "text", None),
            ("session", "Session", "text", None),
            ("montant", "Montant (FCFA)", "text", None),
            ("statut", "Statut", "select", ["En attente", "Validee", "Rejetee"]),
        ],
    },
    "activites": {
        "table": "activites", "titre": "Planning d'activites",
        "champs": [
            ("titre", "Titre", "text", None),
            ("type", "Type", "select", ["Reunion", "Retraite", "Formation", "Autre"]),
            ("date_debut", "Date debut (AAAA-MM-JJ)", "text", None),
            ("date_fin", "Date fin (AAAA-MM-JJ)", "text", None),
            ("lieu", "Lieu", "text", None),
            ("responsable", "Responsable", "text", None),
        ],
    },
    "cotisations": {
        "table": "cotisations", "titre": "Droits statutaires",
        "champs": [
            ("membre_id", "Membre", "fk", get_membres_options),
            ("annee_pastorale_id", "Annee pastorale", "fk", get_annees_pastorales_options),
            ("montant_du", "Montant du", "text", None),
            ("montant_paye", "Montant paye", "text", None),
            ("statut", "Statut", "select", ["Impaye", "Partiel", "Solde"]),
        ],
    },
    "frais_extra": {
        "table": "frais_extra", "titre": "Droits extra-statutaires",
        "champs": [
            ("libelle", "Libelle", "text", None),
            ("membre_id", "Membre", "fk", get_membres_options),
            ("montant", "Montant (FCFA)", "text", None),
            ("date_frais", "Date (AAAA-MM-JJ)", "text", None),
            ("statut", "Statut", "select", ["Impaye", "Solde"]),
        ],
    },
    "paiements": {
        "table": "paiements", "titre": "Paiements",
        "champs": [
            ("membre_id", "Membre", "fk", get_membres_options),
            ("type_frais", "Type", "select", ["Statutaire", "Extra-statutaire", "Inscription", "Autre"]),
            ("libelle", "Libelle", "text", None),
            ("montant", "Montant (FCFA)", "text", None),
            ("date_paiement", "Date (AAAA-MM-JJ)", "text", None),
            ("mode", "Mode", "select", ["Especes", "Mobile Money", "Virement", "Cheque"]),
        ],
    },
    "finances": {
        "table": "finances", "titre": "Recettes / Depenses",
        "champs": [
            ("type_operation", "Type", "select", ["Recette", "Depense"]),
            ("categorie", "Categorie", "text", None),
            ("montant", "Montant (FCFA)", "text", None),
            ("date_operation", "Date (AAAA-MM-JJ)", "text", None),
            ("description", "Description", "text", None),
        ],
    },
    "rh": {
        "table": "rh", "titre": "Ressources humaines",
        "champs": [
            ("membre_id", "Membre", "fk", get_membres_options),
            ("fonction", "Fonction / mandat", "text", None),
            ("commission", "Commission", "text", None),
            ("date_debut_mandat", "Debut mandat", "text", None),
            ("date_fin_mandat", "Fin mandat", "text", None),
        ],
    },
    "documents": {
        "table": "documents", "titre": "Documents administratifs",
        "champs": [
            ("titre", "Titre", "text", None),
            ("categorie", "Categorie", "text", None),
            ("description", "Description", "text", None),
        ],
    },
    "cas_sociaux": {
        "table": "cas_sociaux", "titre": "Cas sociaux",
        "champs": [
            ("membre_id", "Membre concerne", "fk", get_membres_options),
            ("nature", "Nature du cas", "select", ["Maladie", "Deuil", "Difficulte financiere", "Autre"]),
            ("description", "Description", "text", None),
            ("aide_apportee", "Aide apportee", "text", None),
            ("montant_aide", "Montant aide (FCFA)", "text", None),
            ("date_signalement", "Date signalement (AAAA-MM-JJ)", "text", None),
            ("statut", "Statut", "select", ["En cours", "Cloture", "En attente"]),
        ],
    },
}

MENU_SECTIONS = [
    ("Communaute", ["membres", "paroisses", "inscriptions"]),
    ("Activites", ["activites"]),
    ("Finances", ["cotisations", "frais_extra", "paiements", "finances"]),
    ("Administration", ["rh", "cas_sociaux", "documents"]),
]

# Modules entierement reserves a l'administrateur (masques pour un
# responsable de paroisse, qui n'a pas de vision diocesaine globale).
MODULES_ADMIN_UNIQUEMENT = {"finances", "rh", "documents"}

# Modules dont les enregistrements sont filtres par paroisse pour un
# responsable de paroisse : "direct" = colonne paroisse_id sur la table
# elle-meme, "via_membre" = filtrage via membre_id -> membres.paroisse_id.
PAROISSE_LIEN = {
    "membres": "direct",
    "inscriptions": "via_membre",
    "cotisations": "via_membre",
    "paiements": "via_membre",
    "frais_extra": "via_membre",
    "cas_sociaux": "via_membre",
}

# Champ date utilise pour rattacher automatiquement chaque enregistrement a
# son annee pastorale (les cotisations ont un selecteur explicite).
ANNEE_LIEN = {
    "activites": "date_debut",
    "paiements": "date_paiement",
    "finances": "date_operation",
    "frais_extra": "date_frais",
    "cas_sociaux": "date_signalement",
    "inscriptions": "date_inscription",
}


class Carte(BoxLayout):
    """Petit conteneur avec fond blanc et coins doux (style 'panel')."""
    pass


class TelemaApp(App):
    utilisateur = StringProperty("")
    role = StringProperty("administrateur")
    paroisse_id = ObjectProperty(None, allownone=True)

    def build(self):
        """Point d'entree protege : si quoi que ce soit plante au demarrage,
        on affiche le message d'erreur exact directement a l'ecran, au lieu
        de laisser l'application se fermer brutalement sans explication."""
        try:
            return self._build_normal()
        except Exception:
            import traceback
            return self._ecran_erreur_demarrage(traceback.format_exc())

    def _ecran_erreur_demarrage(self, texte_erreur):
        Window.clearcolor = (0.98, 0.96, 0.96, 1)
        racine = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        racine.add_widget(Label(
            text="Un probleme est survenu au demarrage de l'application.\n"
                 "Faites une capture d'ecran de ce message et transmettez-la.",
            bold=True, size_hint_y=None, height=dp(70), color=(0.6, 0.15, 0.1, 1),
            halign="center", valign="middle", text_size=(Window.width - dp(32), dp(70)),
        ))
        scroll = ScrollView()
        etiquette = Label(
            text=texte_erreur, size_hint_y=None, halign="left", valign="top",
            font_size="11sp", color=(0.15, 0.15, 0.15, 1),
        )
        etiquette.bind(texture_size=lambda inst, val: setattr(etiquette, "height", val[1] + dp(20)))
        etiquette.bind(width=lambda inst, val: etiquette.setter("text_size")(etiquette, (val, None)))
        scroll.add_widget(etiquette)
        racine.add_widget(scroll)
        return racine

    def _build_normal(self):
        self.title = "TELEMA - Gestion ECD"
        Window.clearcolor = FOND
        data_dir = os.path.join(self.user_data_dir, "telema_data")
        self.db = DB(data_dir)
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(DashboardScreen(name="dashboard"))
        for key in MODULES:
            self.sm.add_widget(CrudScreen(name=f"crud_{key}", module_key=key))
        self.sm.add_widget(HistoriqueScreen(name="historique"))
        self.sm.add_widget(SauvegardeScreen(name="sauvegarde"))
        self.sm.add_widget(UtilisateursScreen(name="utilisateurs"))
        return self.sm

    def go(self, name):
        self.sm.current = name

    def est_admin(self):
        return self.role == "administrateur"

    def deconnexion(self):
        self.db.log(self.utilisateur, "Deconnexion", "")
        self.utilisateur = ""
        self.go("login")


# ---------------------------------------------------------------------------
# Ecran de connexion
# ---------------------------------------------------------------------------
class LoginScreen(Screen):
    def essayer_connexion(self, username, password):
        app = App.get_running_app()
        conn = app.db.conn()
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone()
        conn.close()
        if row:
            app.utilisateur = username
            app.role = row["role"]
            app.paroisse_id = row["paroisse_id"]
            app.db.log(username, "Connexion", "")
            app.go("dashboard")
            self.ids.erreur.text = ""
        else:
            self.ids.erreur.text = "Identifiant ou mot de passe incorrect."


# ---------------------------------------------------------------------------
# Tableau de bord
# ---------------------------------------------------------------------------
class DashboardScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        conn = app.db.conn()
        if app.est_admin():
            nb_membres = conn.execute("SELECT COUNT(*) c FROM membres").fetchone()["c"]
            nb_paroisses = conn.execute("SELECT COUNT(*) c FROM paroisses").fetchone()["c"]
            nb_activites = conn.execute("SELECT COUNT(*) c FROM activites").fetchone()["c"]
            recettes = conn.execute("SELECT IFNULL(SUM(montant),0) s FROM finances WHERE type_operation='Recette'").fetchone()["s"]
            depenses = conn.execute("SELECT IFNULL(SUM(montant),0) s FROM finances WHERE type_operation='Depense'").fetchone()["s"]
            solde_texte = f"{recettes - depenses:.0f} FCFA"
        else:
            pid = app.paroisse_id
            nb_membres = conn.execute("SELECT COUNT(*) c FROM membres WHERE paroisse_id=?", (pid,)).fetchone()["c"]
            nb_paroisses = 1
            nb_activites = conn.execute("SELECT COUNT(*) c FROM activites").fetchone()["c"]
            solde_texte = "—"
        conn.close()
        self.ids.lbl_utilisateur.text = f"Connecte : {app.utilisateur}" + ("" if app.est_admin() else " (paroisse)")
        self.ids.stat_membres.text = str(nb_membres)
        self.ids.stat_paroisses.text = str(nb_paroisses)
        self.ids.stat_activites.text = str(nb_activites)
        self.ids.stat_solde.text = solde_texte

        # construire le menu dynamiquement (masque les modules reserves a
        # l'administrateur pour un responsable de paroisse)
        menu = self.ids.menu_box
        menu.clear_widgets()
        for section, cles in MENU_SECTIONS:
            cles_visibles = cles if app.est_admin() else [
                c for c in cles if c not in MODULES_ADMIN_UNIQUEMENT and c != "paroisses"
            ]
            if not cles_visibles:
                continue
            menu.add_widget(Label(
                text=section, size_hint_y=None, height=dp(28), bold=True,
                color=BLEU_CLAIR, halign="left", valign="middle",
                text_size=(Window.width - dp(40), dp(28)),
            ))
            for cle in cles_visibles:
                btn = Button(
                    text=MODULES[cle]["titre"], size_hint_y=None, height=dp(46),
                    background_color=(1, 1, 1, 1), color=(0.15, 0.2, 0.25, 1),
                    background_normal="", halign="left", valign="middle",
                )
                btn.bind(on_release=lambda inst, k=cle: self.ouvrir_module(k))
                menu.add_widget(btn)
        extras = [("historique", "Historique"), ("sauvegarde", "Sauvegarde / Restauration"),
                  ("utilisateurs", "Gestion des utilisateurs")]
        if not app.est_admin():
            extras = []
        for extra_name, extra_label in extras:
            btn = Button(
                text=extra_label, size_hint_y=None, height=dp(46),
                background_color=(1, 1, 1, 1), color=(0.15, 0.2, 0.25, 1),
                background_normal="",
            )
            btn.bind(on_release=lambda inst, n=extra_name: App.get_running_app().go(n))
            menu.add_widget(btn)

    def ouvrir_module(self, key):
        App.get_running_app().go(f"crud_{key}")


# ---------------------------------------------------------------------------
# Ecran CRUD generique : liste + formulaire d'ajout/modification
# ---------------------------------------------------------------------------
class CrudScreen(Screen):
    def __init__(self, module_key, **kwargs):
        self.module_key = module_key
        self.cfg = MODULES[module_key]
        self.edit_id = None
        super().__init__(**kwargs)

    def on_pre_enter(self):
        app = App.get_running_app()
        if not app.est_admin() and (self.module_key in MODULES_ADMIN_UNIQUEMENT or self.module_key == "paroisses"):
            # securite : un responsable de paroisse ne doit jamais atteindre
            # un module reserve a l'administrateur, meme via une navigation
            # directe imprevue.
            app.go("dashboard")
            return
        self.ids.titre_module.text = self.cfg["titre"]
        self.charger_liste()

    def charger_liste(self):
        app = App.get_running_app()
        conn = app.db.conn()
        lien = PAROISSE_LIEN.get(self.module_key)
        if not app.est_admin() and lien == "direct":
            rows = conn.execute(
                f"SELECT * FROM {self.cfg['table']} WHERE paroisse_id=? ORDER BY id DESC", (app.paroisse_id,)
            ).fetchall()
        elif not app.est_admin() and lien == "via_membre":
            rows = conn.execute(
                f"""SELECT {self.cfg['table']}.* FROM {self.cfg['table']}
                    JOIN membres ON membres.id = {self.cfg['table']}.membre_id
                    WHERE membres.paroisse_id=? ORDER BY {self.cfg['table']}.id DESC""",
                (app.paroisse_id,),
            ).fetchall()
        else:
            rows = conn.execute(f"SELECT * FROM {self.cfg['table']} ORDER BY id DESC").fetchall()
        conn.close()
        box = self.ids.liste_box
        box.clear_widgets()
        if not rows:
            box.add_widget(Label(
                text="Aucun enregistrement pour le moment.", size_hint_y=None, height=dp(40),
                color=(0.5, 0.55, 0.6, 1),
            ))
            return
        premier_champ = self.cfg["champs"][0][0]
        deuxieme_champ = self.cfg["champs"][1][0] if len(self.cfg["champs"]) > 1 else None
        for row in rows:
            ligne = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(6), padding=(dp(4), dp(2)))
            texte_principal = str(row[premier_champ]) if row[premier_champ] is not None else "-"
            texte_secondaire = str(row[deuxieme_champ]) if deuxieme_champ and row[deuxieme_champ] is not None else ""
            info = BoxLayout(orientation="vertical")
            info.add_widget(Label(text=texte_principal, halign="left", valign="middle", color=(0.15, 0.2, 0.25, 1),
                                   text_size=(Window.width - dp(160), dp(24))))
            if texte_secondaire:
                info.add_widget(Label(text=texte_secondaire, halign="left", valign="middle", color=(0.5, 0.55, 0.6, 1),
                                       font_size="12sp", text_size=(Window.width - dp(160), dp(20))))
            ligne.add_widget(info)
            btn_modif = Button(text="Modifier", size_hint=(None, None), size=(dp(80), dp(36)),
                                background_color=BLEU_CLAIR, background_normal="")
            btn_modif.bind(on_release=lambda inst, rid=row["id"]: self.ouvrir_formulaire(rid))
            ligne.add_widget(btn_modif)
            btn_suppr = Button(text="X", size_hint=(None, None), size=(dp(36), dp(36)),
                                background_color=(0.75, 0.2, 0.15, 1), background_normal="")
            btn_suppr.bind(on_release=lambda inst, rid=row["id"]: self.supprimer(rid))
            ligne.add_widget(btn_suppr)
            box.add_widget(ligne)

    def supprimer(self, rid):
        app = App.get_running_app()
        conn = app.db.conn()
        if not app.est_admin():
            lien = PAROISSE_LIEN.get(self.module_key)
            autorise = False
            if lien == "direct":
                row = conn.execute(f"SELECT paroisse_id FROM {self.cfg['table']} WHERE id=?", (rid,)).fetchone()
                autorise = bool(row) and str(row["paroisse_id"]) == str(app.paroisse_id)
            elif lien == "via_membre":
                row = conn.execute(
                    f"""SELECT membres.paroisse_id AS pid FROM {self.cfg['table']}
                        JOIN membres ON membres.id = {self.cfg['table']}.membre_id
                        WHERE {self.cfg['table']}.id=?""", (rid,)
                ).fetchone()
                autorise = bool(row) and str(row["pid"]) == str(app.paroisse_id)
            if not autorise:
                conn.close()
                return
        conn.execute(f"DELETE FROM {self.cfg['table']} WHERE id=?", (rid,))
        conn.commit()
        conn.close()
        app.db.log(app.utilisateur, f"Suppression {self.cfg['titre']}", f"id={rid}")
        self.charger_liste()

    def ouvrir_formulaire(self, rid=None):
        self.edit_id = rid
        popup_content = FormulaireCrud(self.cfg, rid, self)
        self.popup = Popup(
            title=("Modifier" if rid else "Ajouter") + " - " + self.cfg["titre"],
            content=popup_content, size_hint=(0.92, 0.85),
        )
        self.popup.open()

    def apres_enregistrement(self):
        self.popup.dismiss()
        self.charger_liste()


class FormulaireCrud(BoxLayout):
    def __init__(self, cfg, rid, screen, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8), padding=dp(10), **kwargs)
        self.cfg = cfg
        self.rid = rid
        self.screen = screen
        self.widgets = {}

        app = App.get_running_app()
        row = None
        if rid:
            conn = app.db.conn()
            row = conn.execute(f"SELECT * FROM {cfg['table']} WHERE id=?", (rid,)).fetchone()
            conn.close()

        scroll = ScrollView()
        grille = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
        grille.bind(minimum_height=grille.setter("height"))

        for champ, label, ftype, extra in cfg["champs"]:
            grille.add_widget(Label(text=label, size_hint_y=None, height=dp(22),
                                     halign="left", color=(0.35, 0.4, 0.45, 1), font_size="12sp",
                                     text_size=(Window.width * 0.8, dp(22))))
            valeur_actuelle = row[champ] if row and row[champ] is not None else ""

            # Un responsable de paroisse ne choisit pas librement la
            # paroisse d'un membre : elle est fixee automatiquement a la
            # sienne, pour garantir l'isolation entre paroisses.
            if not app.est_admin() and self.cfg["table"] == "membres" and champ == "paroisse_id":
                grille.add_widget(Label(text="Ma paroisse (fixee automatiquement)", size_hint_y=None,
                                         height=dp(42), color=(0.5, 0.55, 0.6, 1), font_size="12sp"))
                continue

            if ftype == "select":
                sp = Spinner(text=str(valeur_actuelle) if valeur_actuelle else extra[0],
                              values=extra, size_hint_y=None, height=dp(42))
                self.widgets[champ] = sp
                grille.add_widget(sp)
            elif ftype == "fk":
                if not app.est_admin() and extra is get_membres_options:
                    # limite la liste des membres selectionnables a ceux de
                    # la paroisse du responsable connecte.
                    options = get_membres_options(app.db, paroisse_id=app.paroisse_id)
                else:
                    options = extra(app.db)
                labels = [lbl for _id, lbl in options] or ["(aucun)"]
                sp = Spinner(text=labels[0], values=labels, size_hint_y=None, height=dp(42))
                sp.option_ids = options
                if row and row[champ]:
                    for _id, lbl in options:
                        if _id == row[champ]:
                            sp.text = lbl
                self.widgets[champ] = sp
                grille.add_widget(sp)
            else:
                ti = TextInput(text=str(valeur_actuelle), multiline=False, size_hint_y=None, height=dp(42))
                self.widgets[champ] = ti
                grille.add_widget(ti)

        scroll.add_widget(grille)
        self.add_widget(scroll)

        barre = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        btn_ok = Button(text="Enregistrer", background_color=BLEU, background_normal="")
        btn_ok.bind(on_release=lambda i: self.enregistrer())
        btn_annuler = Button(text="Annuler", background_color=(0.85, 0.87, 0.9, 1),
                              color=(0.2, 0.2, 0.2, 1), background_normal="")
        btn_annuler.bind(on_release=lambda i: self.screen.popup.dismiss())
        barre.add_widget(btn_ok)
        barre.add_widget(btn_annuler)
        self.add_widget(barre)

    def enregistrer(self):
        app = App.get_running_app()
        valeurs = []
        champs_noms = []
        for champ, label, ftype, extra in self.cfg["champs"]:
            champs_noms.append(champ)
            if champ not in self.widgets:
                # champ verrouille (ex. paroisse_id fixee pour un
                # responsable de paroisse) : valeur forcee automatiquement.
                if self.cfg["table"] == "membres" and champ == "paroisse_id":
                    valeurs.append(app.paroisse_id)
                else:
                    valeurs.append(None)
                continue
            widget = self.widgets[champ]
            if ftype == "fk":
                option_ids = getattr(widget, "option_ids", [])
                val = None
                for _id, lbl in option_ids:
                    if lbl == widget.text:
                        val = _id
                        break
                valeurs.append(val)
            else:
                valeurs.append(widget.text)

        # Securite supplementaire (defense en profondeur) : un responsable
        # de paroisse ne peut rattacher une donnee qu'a un membre de sa
        # propre paroisse, meme si la liste deroulante etait deja filtree.
        if not app.est_admin() and PAROISSE_LIEN.get(self.screen.module_key) == "via_membre" and "membre_id" in champs_noms:
            membre_choisi = valeurs[champs_noms.index("membre_id")]
            conn_verif = app.db.conn()
            ok = False
            if membre_choisi:
                row_m = conn_verif.execute("SELECT paroisse_id FROM membres WHERE id=?", (membre_choisi,)).fetchone()
                ok = bool(row_m) and str(row_m["paroisse_id"]) == str(app.paroisse_id)
            conn_verif.close()
            if not ok:
                self.screen.popup.dismiss()
                return

        conn = app.db.conn()
        if self.rid:
            set_clause = ",".join(f"{c}=?" for c in champs_noms)
            conn.execute(f"UPDATE {self.cfg['table']} SET {set_clause} WHERE id=?", valeurs + [self.rid])
            action = f"Modification {self.cfg['titre']}"
            nouvel_id = self.rid
        else:
            placeholders = ",".join("?" * len(champs_noms))
            cur = conn.execute(f"INSERT INTO {self.cfg['table']} ({','.join(champs_noms)}) VALUES ({placeholders})", valeurs)
            action = f"Ajout {self.cfg['titre']}"
            nouvel_id = cur.lastrowid

        # Rattachement automatique a l'annee pastorale, d'apres la date du
        # champ pertinent pour ce module (memes regles que la version
        # Windows : 1er septembre au 31 aout).
        date_champ = ANNEE_LIEN.get(self.screen.module_key)
        if date_champ and date_champ in champs_noms:
            date_val = valeurs[champs_noms.index(date_champ)]
            annee_id = app.db.obtenir_ou_creer_annee_pastorale(date_val)
            conn.execute(f"UPDATE {self.cfg['table']} SET annee_pastorale_id=? WHERE id=?", (annee_id, nouvel_id))

        conn.commit()
        conn.close()
        app.db.log(app.utilisateur, action, "")
        self.screen.apres_enregistrement()


# ---------------------------------------------------------------------------
# Historique
# ---------------------------------------------------------------------------
class HistoriqueScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        conn = app.db.conn()
        rows = conn.execute("SELECT * FROM historique ORDER BY id DESC LIMIT 200").fetchall()
        conn.close()
        box = self.ids.hist_box
        box.clear_widgets()
        if not rows:
            box.add_widget(Label(text="Aucune operation enregistree.", size_hint_y=None, height=dp(40),
                                  color=(0.5, 0.55, 0.6, 1)))
        for r in rows:
            texte = f"[{r['date_heure']}] {r['utilisateur']} — {r['action']}"
            box.add_widget(Label(text=texte, size_hint_y=None, height=dp(30), halign="left",
                                  color=(0.2, 0.25, 0.3, 1), font_size="12sp",
                                  text_size=(Window.width - dp(30), dp(30))))


# ---------------------------------------------------------------------------
# Sauvegarde / restauration
# ---------------------------------------------------------------------------
class SauvegardeScreen(Screen):
    def on_pre_enter(self):
        self.rafraichir_liste()

    def creer_sauvegarde(self):
        import shutil
        app = App.get_running_app()
        horodatage = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(app.db.data_dir, "backups", f"telema_backup_{horodatage}.db")
        shutil.copy(app.db.path, dest)
        app.db.log(app.utilisateur, "Sauvegarde manuelle creee", dest)
        self.ids.message_sauvegarde.text = "Sauvegarde creee avec succes."
        self.rafraichir_liste()

    def rafraichir_liste(self):
        app = App.get_running_app()
        backups_dir = os.path.join(app.db.data_dir, "backups")
        box = self.ids.backups_box
        box.clear_widgets()
        if not os.path.isdir(backups_dir):
            return
        fichiers = sorted(os.listdir(backups_dir), reverse=True)
        if not fichiers:
            box.add_widget(Label(text="Aucune sauvegarde pour le moment.", size_hint_y=None, height=dp(36),
                                  color=(0.5, 0.55, 0.6, 1)))
        for f in fichiers:
            box.add_widget(Label(text=f, size_hint_y=None, height=dp(30), halign="left",
                                  color=(0.2, 0.25, 0.3, 1), font_size="12sp",
                                  text_size=(Window.width - dp(30), dp(30))))


class UtilisateursScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        if not app.est_admin():
            app.go("dashboard")
            return
        self.rafraichir_liste()

    def rafraichir_liste(self):
        app = App.get_running_app()
        conn = app.db.conn()
        rows = conn.execute(
            """SELECT users.*, paroisses.nom AS paroisse_nom FROM users
               LEFT JOIN paroisses ON paroisses.id = users.paroisse_id
               ORDER BY users.role, users.username"""
        ).fetchall()
        conn.close()
        box = self.ids.utilisateurs_box
        box.clear_widgets()
        for u in rows:
            ligne = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(6), padding=(dp(4), dp(2)))
            role_lisible = "Administrateur" if u["role"] == "administrateur" else f"Resp. {u['paroisse_nom'] or '?'}"
            info = BoxLayout(orientation="vertical")
            info.add_widget(Label(text=u["username"], halign="left", valign="middle", color=(0.15, 0.2, 0.25, 1),
                                   text_size=(Window.width - dp(160), dp(24))))
            info.add_widget(Label(text=role_lisible, halign="left", valign="middle", color=(0.5, 0.55, 0.6, 1),
                                   font_size="12sp", text_size=(Window.width - dp(160), dp(20))))
            ligne.add_widget(info)
            btn_modif = Button(text="Modifier", size_hint=(None, None), size=(dp(80), dp(36)),
                                background_color=BLEU_CLAIR, background_normal="")
            btn_modif.bind(on_release=lambda inst, uid=u["id"]: self.ouvrir_formulaire(uid))
            ligne.add_widget(btn_modif)
            btn_suppr = Button(text="X", size_hint=(None, None), size=(dp(36), dp(36)),
                                background_color=(0.75, 0.2, 0.15, 1), background_normal="")
            btn_suppr.bind(on_release=lambda inst, uid=u["id"]: self.supprimer(uid))
            ligne.add_widget(btn_suppr)
            box.add_widget(ligne)

    def supprimer(self, uid):
        app = App.get_running_app()
        conn = app.db.conn()
        nb_admins = conn.execute("SELECT COUNT(*) c FROM users WHERE role='administrateur'").fetchone()["c"]
        row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        if row and row["role"] == "administrateur" and nb_admins <= 1:
            conn.close()
            self.ids.message_utilisateurs.text = "Impossible de supprimer le dernier compte administrateur."
            return
        conn.execute("DELETE FROM users WHERE id=?", (uid,))
        conn.commit()
        conn.close()
        app.db.log(app.utilisateur, "Suppression d'un utilisateur", row["username"] if row else str(uid))
        self.ids.message_utilisateurs.text = ""
        self.rafraichir_liste()

    def ouvrir_formulaire(self, uid=None):
        popup_content = FormulaireUtilisateur(uid, self)
        self.popup = Popup(
            title=("Modifier" if uid else "Creer") + " un utilisateur",
            content=popup_content, size_hint=(0.92, 0.75),
        )
        self.popup.open()

    def apres_enregistrement(self):
        self.popup.dismiss()
        self.ids.message_utilisateurs.text = ""
        self.rafraichir_liste()


class FormulaireUtilisateur(BoxLayout):
    def __init__(self, utilisateur_id, screen, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8), padding=dp(10), **kwargs)
        self.utilisateur_id = utilisateur_id
        self.screen = screen
        app = App.get_running_app()
        row = None
        if utilisateur_id:
            conn = app.db.conn()
            row = conn.execute("SELECT * FROM users WHERE id=?", (utilisateur_id,)).fetchone()
            conn.close()

        self.champ_username = TextInput(text=row["username"] if row else "", multiline=False,
                                         size_hint_y=None, height=dp(42), hint_text="Identifiant")
        self.champ_password = TextInput(text="", multiline=False, size_hint_y=None, height=dp(42),
                                         hint_text="Mot de passe (laisser vide pour ne pas changer)" if row else "Mot de passe")
        paroisses = get_paroisses_options(app.db)
        labels_paroisses = [lbl for _id, lbl in paroisses] or ["(aucune paroisse)"]
        self.champ_role = Spinner(text="Administrateur" if row and row["role"] == "administrateur" else "Responsable de paroisse",
                                   values=["Responsable de paroisse", "Administrateur"], size_hint_y=None, height=dp(42))
        self.champ_paroisse = Spinner(text=labels_paroisses[0], values=labels_paroisses, size_hint_y=None, height=dp(42))
        self.champ_paroisse.option_ids = paroisses
        if row and row["paroisse_id"]:
            for _id, lbl in paroisses:
                if _id == row["paroisse_id"]:
                    self.champ_paroisse.text = lbl

        for w, label in [(self.champ_username, "Identifiant"), (self.champ_password, "Mot de passe"),
                          (self.champ_role, "Role"), (self.champ_paroisse, "Paroisse (si responsable)")]:
            self.add_widget(Label(text=label, size_hint_y=None, height=dp(20), halign="left",
                                   color=(0.35, 0.4, 0.45, 1), font_size="12sp",
                                   text_size=(Window.width * 0.8, dp(20))))
            self.add_widget(w)

        self.erreur = Label(text="", size_hint_y=None, height=dp(20), color=(0.75, 0.2, 0.15, 1), font_size="12sp")
        self.add_widget(self.erreur)

        barre = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        btn_ok = Button(text="Enregistrer", background_color=BLEU, background_normal="")
        btn_ok.bind(on_release=lambda i: self.enregistrer())
        btn_annuler = Button(text="Annuler", background_color=(0.85, 0.87, 0.9, 1),
                              color=(0.2, 0.2, 0.2, 1), background_normal="")
        btn_annuler.bind(on_release=lambda i: self.screen.popup.dismiss())
        barre.add_widget(btn_ok)
        barre.add_widget(btn_annuler)
        self.add_widget(barre)

    def enregistrer(self):
        app = App.get_running_app()
        username = self.champ_username.text.strip()
        password = self.champ_password.text.strip()
        role = "administrateur" if self.champ_role.text == "Administrateur" else "responsable_paroisse"
        paroisse_id = None
        for _id, lbl in getattr(self.champ_paroisse, "option_ids", []):
            if lbl == self.champ_paroisse.text:
                paroisse_id = _id
        if not username or (not self.utilisateur_id and not password):
            self.erreur.text = "Identifiant et mot de passe obligatoires."
            return
        if role == "responsable_paroisse" and not paroisse_id:
            self.erreur.text = "Veuillez choisir une paroisse pour ce responsable."
            return
        conn = app.db.conn()
        try:
            if self.utilisateur_id:
                row = conn.execute("SELECT password FROM users WHERE id=?", (self.utilisateur_id,)).fetchone()
                mdp = password if password else row["password"]
                conn.execute(
                    "UPDATE users SET username=?, password=?, role=?, paroisse_id=? WHERE id=?",
                    (username, mdp, role, paroisse_id if role == "responsable_paroisse" else None, self.utilisateur_id),
                )
                if app.utilisateur == username or (self.utilisateur_id and conn.execute("SELECT username FROM users WHERE id=?", (self.utilisateur_id,)).fetchone()["username"] == app.utilisateur):
                    app.utilisateur = username
                    app.role = role
                    app.paroisse_id = paroisse_id if role == "responsable_paroisse" else None
            else:
                conn.execute(
                    "INSERT INTO users (username, password, role, paroisse_id) VALUES (?,?,?,?)",
                    (username, password, role, paroisse_id if role == "responsable_paroisse" else None),
                )
            conn.commit()
            app.db.log(app.utilisateur, "Creation/modification utilisateur", username)
            conn.close()
            self.screen.apres_enregistrement()
        except sqlite3.IntegrityError:
            conn.close()
            self.erreur.text = f"L'identifiant « {username} » est deja utilise."


KV = """
#:import dp kivy.metrics.dp

<Carte@BoxLayout>:
    orientation: "vertical"
    padding: dp(14)
    spacing: dp(6)
    size_hint_y: None
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]

<LoginScreen>:
    canvas.before:
        Color:
            rgba: 0.12, 0.31, 0.47, 1
        Rectangle:
            pos: self.pos
            size: self.size
    FloatLayout:
        BoxLayout:
            orientation: "vertical"
            size_hint: 0.85, None
            height: dp(360)
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            padding: dp(22)
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10]
            Label:
                text: "T"
                size_hint_y: None
                height: dp(44)
                font_size: "26sp"
                bold: True
                color: 0.35, 0.6, 0.83, 1
            Label:
                text: "Communaute Telema"
                size_hint_y: None
                height: dp(28)
                font_size: "17sp"
                bold: True
                color: 0.12, 0.31, 0.47, 1
            Label:
                text: "Equipe de Coordination Diocesaine"
                size_hint_y: None
                height: dp(22)
                font_size: "11sp"
                color: 0.5, 0.55, 0.6, 1
            TextInput:
                id: champ_user
                hint_text: "Identifiant"
                multiline: False
                size_hint_y: None
                height: dp(42)
            TextInput:
                id: champ_pass
                hint_text: "Mot de passe"
                password: True
                multiline: False
                size_hint_y: None
                height: dp(42)
            Label:
                id: erreur
                text: ""
                color: 0.75, 0.2, 0.15, 1
                size_hint_y: None
                height: dp(18)
                font_size: "11sp"
            Button:
                text: "Se connecter"
                size_hint_y: None
                height: dp(44)
                background_color: 0.12, 0.31, 0.47, 1
                background_normal: ""
                on_release: root.essayer_connexion(champ_user.text, champ_pass.text)
            Label:
                text: "Compte par defaut : admin / telema2026"
                size_hint_y: None
                height: dp(18)
                font_size: "10sp"
                color: 0.6, 0.65, 0.7, 1

<DashboardScreen>:
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.96, 0.97, 0.98, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(12), 0
            canvas.before:
                Color:
                    rgba: 0.12, 0.31, 0.47, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "TELEMA — Tableau de bord"
                bold: True
                color: 1, 1, 1, 1
            Label:
                id: lbl_utilisateur
                text: ""
                font_size: "11sp"
                color: 0.85, 0.9, 0.95, 1
                size_hint_x: None
                width: dp(140)
            Button:
                text: "Quitter"
                size_hint_x: None
                width: dp(70)
                background_color: 0.2, 0.4, 0.55, 1
                background_normal: ""
                on_release: app.deconnexion()
        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(14)
                spacing: dp(12)
                BoxLayout:
                    size_hint_y: None
                    height: dp(80)
                    spacing: dp(8)
                    Carte:
                        height: dp(80)
                        Label:
                            id: stat_membres
                            text: "0"
                            bold: True
                            font_size: "20sp"
                            color: 0.12, 0.31, 0.47, 1
                        Label:
                            text: "Membres"
                            font_size: "11sp"
                            color: 0.5, 0.55, 0.6, 1
                    Carte:
                        height: dp(80)
                        Label:
                            id: stat_paroisses
                            text: "0"
                            bold: True
                            font_size: "20sp"
                            color: 0.12, 0.31, 0.47, 1
                        Label:
                            text: "Paroisses"
                            font_size: "11sp"
                            color: 0.5, 0.55, 0.6, 1
                    Carte:
                        height: dp(80)
                        Label:
                            id: stat_activites
                            text: "0"
                            bold: True
                            font_size: "20sp"
                            color: 0.12, 0.31, 0.47, 1
                        Label:
                            text: "Activites"
                            font_size: "11sp"
                            color: 0.5, 0.55, 0.6, 1
                Carte:
                    size_hint_y: None
                    height: dp(70)
                    Label:
                        id: stat_solde
                        text: "0 FCFA"
                        bold: True
                        font_size: "18sp"
                        color: 0.18, 0.45, 0.32, 1
                    Label:
                        text: "Solde de caisse"
                        font_size: "11sp"
                        color: 0.5, 0.55, 0.6, 1
                BoxLayout:
                    id: menu_box
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(4)

<CrudScreen>:
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.96, 0.97, 0.98, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(12), 0
            canvas.before:
                Color:
                    rgba: 0.12, 0.31, 0.47, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "< Retour"
                size_hint_x: None
                width: dp(80)
                background_color: 0.2, 0.4, 0.55, 1
                background_normal: ""
                on_release: app.go("dashboard")
            Label:
                id: titre_module
                text: ""
                bold: True
                color: 1, 1, 1, 1
            Button:
                text: "+ Ajouter"
                size_hint_x: None
                width: dp(90)
                background_color: 0.35, 0.6, 0.83, 1
                background_normal: ""
                on_release: root.ouvrir_formulaire()
        ScrollView:
            BoxLayout:
                id: liste_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(10)
                spacing: dp(4)

<HistoriqueScreen>:
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.96, 0.97, 0.98, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(12), 0
            canvas.before:
                Color:
                    rgba: 0.12, 0.31, 0.47, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "< Retour"
                size_hint_x: None
                width: dp(80)
                background_color: 0.2, 0.4, 0.55, 1
                background_normal: ""
                on_release: app.go("dashboard")
            Label:
                text: "Historique des operations"
                bold: True
                color: 1, 1, 1, 1
        ScrollView:
            BoxLayout:
                id: hist_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(10)
                spacing: dp(2)

<SauvegardeScreen>:
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.96, 0.97, 0.98, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(12), 0
            canvas.before:
                Color:
                    rgba: 0.12, 0.31, 0.47, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "< Retour"
                size_hint_x: None
                width: dp(80)
                background_color: 0.2, 0.4, 0.55, 1
                background_normal: ""
                on_release: app.go("dashboard")
            Label:
                text: "Sauvegarde / Restauration"
                bold: True
                color: 1, 1, 1, 1
        ScrollView:
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(14)
                spacing: dp(10)
                Carte:
                    size_hint_y: None
                    height: dp(110)
                    Label:
                        text: "Creer une sauvegarde de la base de donnees"
                        font_size: "13sp"
                        color: 0.2, 0.25, 0.3, 1
                    Button:
                        text: "Creer une sauvegarde maintenant"
                        size_hint_y: None
                        height: dp(42)
                        background_color: 0.12, 0.31, 0.47, 1
                        background_normal: ""
                        on_release: root.creer_sauvegarde()
                    Label:
                        id: message_sauvegarde
                        text: ""
                        font_size: "12sp"
                        color: 0.18, 0.45, 0.32, 1
                Label:
                    text: "Sauvegardes disponibles :"
                    size_hint_y: None
                    height: dp(26)
                    bold: True
                    color: 0.12, 0.31, 0.47, 1
                BoxLayout:
                    id: backups_box
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(2)

<UtilisateursScreen>:
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.96, 0.97, 0.98, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(12), 0
            canvas.before:
                Color:
                    rgba: 0.12, 0.31, 0.47, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "< Retour"
                size_hint_x: None
                width: dp(80)
                background_color: 0.2, 0.4, 0.55, 1
                background_normal: ""
                on_release: app.go("dashboard")
            Label:
                text: "Utilisateurs"
                bold: True
                color: 1, 1, 1, 1
            Button:
                text: "+ Creer"
                size_hint_x: None
                width: dp(80)
                background_color: 0.35, 0.6, 0.83, 1
                background_normal: ""
                on_release: root.ouvrir_formulaire()
        Label:
            id: message_utilisateurs
            text: ""
            size_hint_y: None
            height: dp(24) if self.text else 0
            color: 0.75, 0.2, 0.15, 1
            font_size: "12sp"
        ScrollView:
            BoxLayout:
                id: utilisateurs_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(10)
                spacing: dp(4)
"""

Builder.load_string(KV)

if __name__ == "__main__":
    try:
        TelemaApp().run()
    except Exception:
        # Filet de securite ultime : si meme le lancement de l'app plante
        # avant que build() ne puisse intervenir, on affiche quand meme
        # l'erreur a l'ecran avec une mini-application Kivy independante.
        import traceback
        from kivy.uix.label import Label as _Label
        from kivy.app import App as _App

        texte_erreur = traceback.format_exc()

        class _AppSecours(_App):
            def build(self):
                return _Label(
                    text="Erreur au lancement :\n\n" + texte_erreur,
                    halign="left", valign="top", font_size="11sp",
                    text_size=(360, None),
                )

        _AppSecours().run()
