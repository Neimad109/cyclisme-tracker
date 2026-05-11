# 🚴 Ex-Arkéa Tracker 2026

Dashboard de suivi des anciens coureurs Arkéa-B&B Hotels pour la saison 2026.  
Mis à jour automatiquement chaque soir à 19h via GitHub Actions + ProCyclingStats.

## Structure

```
cyclisme-tracker/
├── index.html          # Page du dashboard
├── scraper.py          # Script de scraping PCS
├── data/
│   └── results.json    # Données (générées automatiquement)
└── .github/workflows/
    └── scrape.yml      # Tâche automatique 19h
```

## Ajouter un résultat manuellement

Édite `data/results.json` et ajoute une entrée dans le tableau `results` :

```json
{
  "rider": "mozzato",
  "race": "Gand-Wevelgem",
  "date": "2026-03-29",
  "cat": "wt",
  "pos": 4,
  "pts": 160,
  "note": "Belle course dans le final",
  "source": "manual"
}
```

> ⚠️ Mets toujours `"source": "manual"` pour que le scraper ne l'écrase pas.

## IDs des coureurs

| ID | Nom |
|----|-----|
| vauquelin | Kévin Vauquelin |
| costiou | Ewen Costiou |
| mozzato | Luca Mozzato |
| biermans | Jenthe Biermans |
| senechal | Florian Sénéchal |
| venturini | Clément Venturini |
| capiot | Amaury Capiot |
| rodriguez | Cristián Rodríguez |
| garciaPierna | Raúl García Pierna |
| guglielmi | Simon Guglielmi |
| huys | Laurens Huys |
| svestad | E. Svestad-Bårdseng |
| leBerre | Mathis Le Berre |
| grondin | Donavan Grondin |
| tjotta | Martin Tjøtta |
| rouland | Louis Rouland |
| thierry | Pierre Thierry |
| lozouet | Léandre Lozouet |

## Catégories

| cat | Description |
|-----|-------------|
| wt | WorldTour (classique, étape WT) |
| gc | Grand Tour / course par étapes GC |
| pro | Pro Series |
| 1.1 | Course 1.1 |
