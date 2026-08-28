# TELEMA — Application Android (Kivy)
### Gestion de l'Équipe de Coordination Diocésaine — 100 % hors ligne

## 1. Ce que j'ai construit et testé

Une vraie application Android en Python/Kivy (pas une page web déguisée) :

- Écran de connexion (admin / telema2026)
- Tableau de bord avec statistiques en direct, adapté selon le rôle
- Modules : Membres (fiche complète : sacrements, groupe sanguin,
  profession, adresse, section, engagements, paroisse antérieure...),
  Paroisses, Inscriptions, Planning d'activités, Droits statutaires
  (rattachés à une année pastorale), Droits extra-statutaires, Paiements,
  Recettes/Dépenses, Ressources humaines, Cas sociaux, Documents
  administratifs
- **Accès par rôle** : administrateur (accès total au diocèse) ou
  responsable de paroisse (accès strictement limité à sa propre paroisse —
  mêmes règles d'isolation que la version Windows : membres, inscriptions,
  cotisations, paiements et cas sociaux filtrés automatiquement à sa
  paroisse ; aucun accès aux finances, RH, documents ou aux autres
  paroisses)
- **Années pastorales** (1er septembre → 31 août) : chaque cotisation,
  paiement, dépense/recette, activité, cas social et inscription est
  automatiquement rattaché à son année pastorale d'après sa date ; aucune
  donnée n'est jamais supprimée en changeant d'année
- Historique horodaté de toutes les opérations
- Sauvegarde manuelle de la base de données
- Base de données **SQLite locale**, stockée dans le dossier privé de
  l'application sur le téléphone — **aucune connexion Internet requise**

J'ai testé chaque écran (connexion selon le rôle, tableau de bord, liste,
formulaire d'ajout avec tous les nouveaux champs, isolation entre
paroisses — y compris une tentative de contournement délibérée —,
rattachement automatique à l'année pastorale) dans un environnement
graphique virtuel avant de vous le livrer. Tout fonctionne.

## 2. Pourquoi je ne peux pas vous donner directement le fichier .apk

Contrairement au .exe Windows (que j'ai pu compiler ici grâce à Wine),
la fabrication d'un .apk Android nécessite de télécharger le **SDK et le
NDK Android** depuis les serveurs de Google (plusieurs centaines de Mo).
Mon environnement de travail n'a pas accès à ces serveurs (accès réseau
restreint), donc je ne peux pas lancer cette compilation moi-même ici.

## 3. Comment obtenir le .apk — gratuitement, sans installer Android Studio

J'ai préparé un robot de compilation automatique (**GitHub Actions**) qui
fait tout le travail à votre place, sur les serveurs de GitHub (gratuits).
Vous n'avez besoin d'aucune compétence technique particulière :

1. Créez un compte gratuit sur https://github.com si vous n'en avez pas.
2. Créez un nouveau dépôt (bouton vert « New »), par exemple nommé
   `telema-android`.
3. Téléversez-y tout le contenu de ce dossier `telema_android` (glisser-
   déposer les fichiers sur la page du dépôt, ou utiliser « Add file » >
   « Upload files »). Le dossier `.github/workflows` doit être conservé
   tel quel : c'est lui qui déclenche la compilation automatique.
4. Une fois les fichiers envoyés, cliquez sur l'onglet **Actions** en haut
   du dépôt : une compilation démarre automatiquement (elle dure environ
   20 à 30 minutes la première fois).
5. Quand elle est terminée (coche verte ✓), cliquez dessus, puis en bas de
   la page, dans la section **Artifacts**, téléchargez **TelemaGestion-APK**.
   C'est un fichier .zip contenant votre .apk installable.
6. Transférez ce .apk sur votre téléphone Android (câble USB, ou tout
   simplement en l'envoyant vous-même par WhatsApp/e-mail), puis appuyez
   dessus pour l'installer (autorisez « Sources inconnues » si demandé).

Je peux vous accompagner pas à pas pour cette étape si besoin — dites-le
moi simplement au moment venu.

## 4. Alternative encore plus simple, sans GitHub

Si vous préférez que je m'en occupe de bout en bout : donnez-moi accès à
un compte GitHub (ou créez-en un et partagez-moi un jeton d'accès
temporaire), et je peux pousser le code et déclencher la compilation
moi-même via l'API GitHub, puis vous transmettre le lien de
téléchargement direct de l'APK.

## 5. Structure du projet

```
telema_android/
├── main.py                    → application Kivy (interface + logique)
├── telemadb.py                → base de données SQLite locale
├── buildozer.spec             → configuration de compilation Android
├── icon.png                   → icône de l'application
└── .github/workflows/
    └── build-apk.yml          → robot de compilation automatique de l'APK
```

## 6. Tester l'application dès maintenant sur votre PC (avant l'APK)

Si vous avez Python sur votre ordinateur, vous pouvez déjà tester
l'application (elle s'affichera dans une fenêtre, comme sur un téléphone) :

```
pip install kivy
python main.py
```

## 7. Gestion des utilisateurs

Un écran « Gestion des utilisateurs » (menu Administration, administrateur
uniquement) permet désormais de créer, modifier et supprimer les accès
directement depuis l'application — identifiant, mot de passe, rôle
(administrateur ou responsable de paroisse) et paroisse concernée. Le
dernier compte administrateur ne peut pas être supprimé, pour éviter de se
retrouver bloqué hors de l'application.
