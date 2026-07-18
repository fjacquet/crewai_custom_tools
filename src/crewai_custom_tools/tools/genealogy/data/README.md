# Table prénoms → sexe (INSEE, OFS optionnel)

`prenoms_sexe.csv` — colonnes `prenom` (clé normalisée : MAJUSCULES, accents
retirés, apostrophes/tirets canoniques via `normkey`), `n_f`, `n_m` (effectifs de
naissances agrégés toutes années). **Ce fichier est versionné et embarqué** : la
fonctionnalité marche prête à l'emploi, sans téléchargement au runtime.

## Génération / rafraîchissement — une seule commande

Le script **télécharge lui-même** la source INSEE et bâtit la table (aucun
fichier à manipuler à la main) :

```bash
uv run python scripts/build_prenoms_sexe.py
```

Il écrit directement `src/crewai_custom_tools/tools/genealogy/data/prenoms_sexe.csv`.

## Sources

- **INSEE — Fichier des prénoms** (fichier national, France 1900→2025),
  Licence Ouverte / Etalab. Téléchargé automatiquement (édition épinglée dans
  `INSEE_URL`). CSV `;`, colonnes `sexe;prenom;periode;valeur;rang` (`sexe` 1=M,
  2=F ; effectifs `valeur` agrégés par prénom×sexe sur toutes les années). Le
  parseur tolère aussi l'ancien en-tête `preusuel;annais;nombre`.
  <https://www.insee.fr/fr/statistiques/8595130>
- **OFS/BFS — Prénoms des nouveau-nés** (Suisse) — **optionnel**. L'INSEE couvre
  déjà l'essentiel d'un arbre à racine franco-suisse ; pour ajouter explicitement
  la couverture suisse, fournir deux CSV `;` `prenom;nombre` :
  `--ofs-f ofs_feminin.csv --ofs-m ofs_masculin.csv`. Source :
  <https://www.bfs.admin.ch/bfs/fr/home/statistiques/population/naissances-deces/prenoms-nouveaux-nes.html>
  (portail opendata.swiss ; extraction manuelle des px/CSV requise à ce jour).

Les fichiers bruts ne sont pas versionnés ; seul `prenoms_sexe.csv` l'est.
