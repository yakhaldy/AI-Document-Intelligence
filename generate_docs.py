#!/usr/bin/env python3
"""
Generate synthetic French "contrat" and "rapport" text documents, to unblock
Étape 3 (classification) — generate_invoices.py only produces the "facture"
class, so a 3-way classifier had nothing to distinguish.

Run:
    python generate_docs.py --n-contracts 60 --n-reports 60 --out data/synthetic --seed 42

Output:
    <out>/contracts/texts/ctr_0001.txt
    <out>/contracts/manifest.csv   (id, doc_type, template, split)
    <out>/reports/texts/rpt_0001.txt
    <out>/reports/manifest.csv     (id, doc_type, template, split)

Design notes:
  * Plain text, not PDF/scan — classification runs on already-extracted text
    (see architecture diagram: OCR -> CLASSIFICATION), and facture text used
    for classification is the clean PDF-extracted reference text too (not
    the noisy OCR output), so all 3 classes are compared on clean text —
    apples to apples, not "noisy facture vs clean contrat/rapport".
  * Split is random (not by-template like invoices): with only 6 templates
    per class, a strict by-template split would leave too few templates to
    train on. Content still varies per instance (parties, dates, figures).
  * Company names/cities reuse generate_invoices.py's pools for stylistic
    consistency with the rest of the corpus.
"""
import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from generate_invoices import CITIES, LEGAL, MONTHS, NAME_A, NAME_B

DURATIONS = ["6 mois", "12 mois", "24 mois", "36 mois", "une durée indéterminée"]
AMOUNTS_MAD = [15000, 25000, 45000, 80000, 120000, 250000, 500000]


def company(rng):
    return f"{rng.choice(NAME_A)} {rng.choice(NAME_B)} {rng.choice(LEGAL)}"


def person(rng):
    first = rng.choice(["Karim", "Salma", "Youssef", "Amina", "Rachid", "Nadia",
                         "Hassan", "Fatima", "Omar", "Leila", "Mehdi", "Sara"])
    last = rng.choice(["Bennani", "El Amrani", "Chraibi", "Tazi", "Alaoui",
                        "Fassi", "Berrada", "Idrissi", "Squalli", "Lahlou"])
    return f"{first} {last}"


def city(rng):
    return rng.choice(list(CITIES))


def fmt_date(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def random_date(rng, start_year=2024, end_year=2025):
    d0, d1 = date(start_year, 1, 1), date(end_year, 12, 31)
    return d0 + timedelta(days=rng.randint(0, (d1 - d0).days))


# ---------------------------------------------------------------- contrats
CONTRACT_TEMPLATES = [
    "Contrat de prestation de services",
    "Contrat de bail commercial",
    "Contrat de travail à durée indéterminée",
    "Contrat de vente",
    "Contrat de partenariat commercial",
    "Contrat de sous-traitance",
]

CONTRACT_ARTICLE_POOL = {
    "Contrat de prestation de services": [
        ("Objet", "Le Prestataire s'engage à fournir au Client les services décrits en annexe, "
                   "dans le respect des délais et de la qualité convenus."),
        ("Durée", "Le présent contrat est conclu pour une durée de {duration}, renouvelable par "
                   "tacite reconduction sauf dénonciation par l'une des parties."),
        ("Prix et modalités de paiement", "En contrepartie des prestations, le Client versera au "
                   "Prestataire la somme de {amount} MAD HT, payable dans un délai de 30 jours "
                   "à compter de la réception de la facture."),
        ("Obligations des parties", "Le Prestataire s'engage à exécuter les prestations avec "
                   "diligence et selon les règles de l'art. Le Client s'engage à fournir toute "
                   "information nécessaire à la bonne exécution du contrat."),
        ("Résiliation", "Chaque partie peut résilier le présent contrat en cas de manquement grave "
                   "de l'autre partie, après mise en demeure restée infructueuse pendant 15 jours."),
    ],
    "Contrat de bail commercial": [
        ("Objet", "Le Bailleur donne à bail au Preneur les locaux commerciaux sis à {city}, "
                   "destinés à l'exercice de son activité commerciale."),
        ("Durée", "Le présent bail est consenti pour une durée de {duration}, à compter de sa "
                   "date de signature."),
        ("Loyer", "Le loyer mensuel est fixé à {amount} MAD, payable d'avance le 5 de chaque mois "
                   "par virement bancaire."),
        ("Dépôt de garantie", "Le Preneur verse au Bailleur, à titre de dépôt de garantie, une "
                   "somme équivalente à trois mois de loyer."),
        ("Entretien et réparations", "Le Preneur assurera l'entretien courant des locaux ; les "
                   "grosses réparations restent à la charge du Bailleur."),
    ],
    "Contrat de travail à durée indéterminée": [
        ("Engagement", "La Société engage {employee} en qualité de {role}, à compter du "
                   "{start_date}, pour une durée indéterminée."),
        ("Rémunération", "En contrepartie de ses fonctions, le salarié percevra une rémunération "
                   "mensuelle brute de {amount} MAD, payable en fin de mois."),
        ("Lieu de travail", "Le salarié exercera ses fonctions au siège social de la Société à "
                   "{city}, sous réserve de déplacements ponctuels."),
        ("Période d'essai", "Le présent contrat est conclu avec une période d'essai de trois mois, "
                   "renouvelable une fois."),
        ("Congés payés", "Le salarié bénéficiera des congés payés conformément à la législation "
                   "marocaine du travail en vigueur."),
    ],
    "Contrat de vente": [
        ("Objet", "Le Vendeur cède au Acheteur les biens décrits en annexe, l'Acheteur acceptant "
                   "de les acquérir aux conditions ci-après."),
        ("Prix", "Le prix de vente est fixé à {amount} MAD TTC, payable comptant à la signature "
                   "du présent contrat."),
        ("Livraison", "La livraison des biens interviendra dans un délai de 30 jours à compter de "
                   "la signature, aux frais de l'Acheteur."),
        ("Garantie", "Le Vendeur garantit l'Acheteur contre tout vice caché pendant une durée de "
                   "12 mois à compter de la livraison."),
        ("Transfert de propriété", "Le transfert de propriété n'interviendra qu'après paiement "
                   "intégral du prix convenu."),
    ],
    "Contrat de partenariat commercial": [
        ("Objet", "Les parties conviennent d'un partenariat commercial visant à développer "
                   "conjointement leurs activités sur le marché marocain."),
        ("Durée", "Le présent partenariat est conclu pour une durée de {duration}."),
        ("Répartition des revenus", "Les revenus générés par le partenariat seront répartis à "
                   "parts égales entre les deux parties, sauf accord contraire écrit."),
        ("Confidentialité", "Chaque partie s'engage à préserver la confidentialité des informations "
                   "échangées dans le cadre du présent partenariat."),
        ("Non-concurrence", "Pendant la durée du contrat, les parties s'engagent à ne pas conclure "
                   "d'accord similaire avec un concurrent direct."),
    ],
    "Contrat de sous-traitance": [
        ("Objet", "Le Donneur d'ordre confie au Sous-traitant l'exécution des travaux décrits en "
                   "annexe, dans le cadre de son marché principal."),
        ("Délais d'exécution", "Le Sous-traitant s'engage à exécuter les travaux dans un délai de "
                   "{duration} à compter de la notification de commande."),
        ("Prix", "Le montant de la sous-traitance est fixé à {amount} MAD HT, révisable selon les "
                   "conditions prévues en annexe."),
        ("Responsabilité", "Le Sous-traitant demeure seul responsable de la bonne exécution des "
                   "travaux qui lui sont confiés."),
        ("Assurance", "Le Sous-traitant justifie d'une assurance responsabilité civile "
                   "professionnelle en cours de validité."),
    ],
}


def make_contract(rng, idx):
    template = rng.choice(CONTRACT_TEMPLATES)
    party_a = company(rng)
    party_b = company(rng) if "travail" not in template else person(rng)
    signing_date = random_date(rng)
    articles = CONTRACT_ARTICLE_POOL[template]

    lines = [template.upper(), ""]
    lines.append("ENTRE LES SOUSSIGNÉS :")
    lines.append(f"{party_a}, ci-après désigné « la Première Partie »,")
    lines.append("ET")
    lines.append(f"{party_b}, ci-après désigné « la Seconde Partie »,")
    lines.append("")
    lines.append("IL A ÉTÉ CONVENU CE QUI SUIT :")
    lines.append("")
    for i, (title, body) in enumerate(articles, start=1):
        text = body.format(
            duration=rng.choice(DURATIONS),
            amount=f"{rng.choice(AMOUNTS_MAD):,}".replace(",", " "),
            city=city(rng),
            employee=party_b if isinstance(party_b, str) and " " in party_b else person(rng),
            role=rng.choice(["Comptable", "Technicien", "Responsable commercial",
                              "Ingénieur", "Assistant administratif"]),
            start_date=fmt_date(signing_date),
        )
        lines.append(f"Article {i} – {title}")
        lines.append(text)
        lines.append("")
    lines.append(f"Fait à {city(rng)}, le {fmt_date(signing_date)}, en deux exemplaires originaux.")
    lines.append("")
    lines.append("Pour la Première Partie                    Pour la Seconde Partie")
    lines.append(f"{party_a}                    {party_b}")

    return {
        "id": f"ctr_{idx:04d}", "doc_type": "contrat", "template": template,
        "text": "\n".join(lines),
    }


# ----------------------------------------------------------------- rapports
REPORT_TEMPLATES = [
    "Rapport d'audit interne",
    "Rapport mensuel d'activité",
    "Rapport de mission",
    "Compte-rendu de réunion",
    "Rapport d'incident",
    "Rapport financier trimestriel",
]

REPORT_SECTION_POOL = {
    "Rapport d'audit interne": [
        ("Contexte", "Le présent audit a été mené au sein du département {dept} de {company} "
                      "dans le cadre du programme annuel de contrôle interne."),
        ("Constats", "L'audit a permis d'identifier {n} points de non-conformité concernant les "
                      "procédures du service {dept}, principalement liés à un défaut de traçabilité "
                      "documentaire."),
        ("Recommandations", "Il est recommandé de renforcer les contrôles de premier niveau et de "
                      "formaliser les procédures actuellement appliquées de manière informelle."),
        ("Conclusion", "Sous réserve de la mise en œuvre des recommandations ci-dessus, le "
                      "dispositif de contrôle interne du département {dept} peut être jugé "
                      "globalement satisfaisant."),
    ],
    "Rapport mensuel d'activité": [
        ("Contexte", "Ce rapport présente le bilan des activités du département {dept} de "
                      "{company} pour le mois écoulé."),
        ("Résultats", "Le chiffre d'affaires du mois s'élève à {amount} MAD, en évolution par "
                      "rapport au mois précédent. {n} nouveaux dossiers ont été traités."),
        ("Difficultés rencontrées", "Le service a rencontré des retards liés à une charge de "
                      "travail exceptionnelle sur la période, notamment sur les dossiers urgents."),
        ("Conclusion", "L'activité du mois est jugée conforme aux objectifs fixés en début "
                      "d'exercice pour le département {dept}."),
    ],
    "Rapport de mission": [
        ("Contexte", "Dans le cadre de sa mission auprès de {company}, {author} s'est rendu sur "
                      "site du {start} au {end}."),
        ("Objectifs", "La mission avait pour objectif d'évaluer l'organisation du département "
                      "{dept} et de proposer des axes d'amélioration."),
        ("Constats", "Les entretiens menés ont révélé {n} axes de progrès prioritaires, "
                      "notamment en matière de coordination inter-services."),
        ("Recommandations", "Il est recommandé de mettre en place un comité de pilotage mensuel "
                      "pour assurer le suivi des actions engagées."),
    ],
    "Compte-rendu de réunion": [
        ("Participants", "Réunion du service {dept} tenue le {start}, en présence de {n} participants, "
                      "sous la présidence de {author}."),
        ("Points abordés", "Les échanges ont porté sur l'avancement des projets en cours au sein "
                      "de {company} et sur la répartition des tâches pour le trimestre à venir."),
        ("Décisions", "Il a été décidé de réallouer le budget de {amount} MAD vers les priorités "
                      "identifiées et de fixer un point d'étape mensuel."),
        ("Prochaine réunion", "La prochaine réunion du service {dept} est fixée au mois suivant, sauf "
                      "urgence justifiant une convocation anticipée."),
    ],
    "Rapport d'incident": [
        ("Contexte", "Le présent rapport documente un incident survenu le {start} au sein du "
                      "département {dept} de {company}."),
        ("Description de l'incident", "L'incident a entraîné une interruption partielle de "
                      "l'activité pendant plusieurs heures, sans conséquence sur la sécurité "
                      "du personnel."),
        ("Actions correctives", "Une intervention a été menée par l'équipe technique afin de "
                      "rétablir le fonctionnement normal ; {n} mesures correctives ont été "
                      "engagées."),
        ("Conclusion", "Un suivi renforcé du département {dept} est mis en place pour prévenir "
                      "la récurrence de ce type d'incident."),
    ],
    "Rapport financier trimestriel": [
        ("Contexte", "Ce rapport présente la situation financière de {company} pour le trimestre "
                      "écoulé, à destination de la direction générale."),
        ("Résultats financiers", "Le chiffre d'affaires trimestriel s'établit à {amount} MAD, "
                      "porté principalement par l'activité du département {dept}."),
        ("Analyse", "L'évolution constatée s'explique par {n} facteurs principaux, détaillés en "
                      "annexe du présent rapport."),
        ("Conclusion", "La situation financière de {company} sur le trimestre est jugée conforme "
                      "aux prévisions budgétaires initiales."),
    ],
}

DEPARTMENTS = ["Comptabilité", "Ressources Humaines", "Logistique", "Commercial",
               "Informatique", "Production", "Qualité"]


def make_report(rng, idx):
    template = rng.choice(REPORT_TEMPLATES)
    comp = company(rng)
    author = person(rng)
    start = random_date(rng)
    end = start + timedelta(days=rng.randint(1, 5))
    sections = REPORT_SECTION_POOL[template]

    lines = [template.upper(), ""]
    lines.append(f"Rédigé par : {author}")
    lines.append(f"Date : {fmt_date(start)}")
    lines.append(f"Société : {comp}")
    lines.append("")
    for i, (title, body) in enumerate(sections, start=1):
        text = body.format(
            dept=rng.choice(DEPARTMENTS),
            company=comp,
            author=author,
            n=rng.randint(2, 9),
            amount=f"{rng.choice(AMOUNTS_MAD):,}".replace(",", " "),
            start=fmt_date(start),
            end=fmt_date(end),
        )
        lines.append(f"{i}. {title}")
        lines.append(text)
        lines.append("")

    return {
        "id": f"rpt_{idx:04d}", "doc_type": "rapport", "template": template,
        "text": "\n".join(lines),
    }


# ------------------------------------------------------------------- main
def write_corpus(rows, out_subdir: Path, dev_ratio: float, rng):
    (out_subdir / "texts").mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for row in rows:
        (out_subdir / "texts" / f"{row['id']}.txt").write_text(row["text"], encoding="utf-8")
        split = "dev" if rng.random() < dev_ratio else "test"
        manifest_rows.append({
            "id": row["id"], "doc_type": row["doc_type"],
            "template": row["template"], "split": split,
        })
    with open(out_subdir / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "doc_type", "template", "split"])
        w.writeheader()
        w.writerows(manifest_rows)
    n_dev = sum(r["split"] == "dev" for r in manifest_rows)
    return len(manifest_rows), n_dev


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-contracts", type=int, default=60)
    parser.add_argument("--n-reports", type=int, default=60)
    parser.add_argument("--out", default="data/synthetic")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dev-ratio", type=float, default=0.7)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    out = Path(args.out)

    contracts = [make_contract(rng, i) for i in range(1, args.n_contracts + 1)]
    n_c, dev_c = write_corpus(contracts, out / "contracts", args.dev_ratio, rng)
    print(f"contrats : {n_c} (dev={dev_c}, test={n_c - dev_c})")

    reports = [make_report(rng, i) for i in range(1, args.n_reports + 1)]
    n_r, dev_r = write_corpus(reports, out / "reports", args.dev_ratio, rng)
    print(f"rapports : {n_r} (dev={dev_r}, test={n_r - dev_r})")


if __name__ == "__main__":
    main()
