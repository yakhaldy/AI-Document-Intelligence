import { Link } from 'react-router-dom'

const DIFFERENTIATORS = [
  {
    title: 'Champs marocains spécifiques',
    text: "ICE, IF, RC, TVA, MAD — des formats variés selon le fournisseur, donc une extraction non triviale, pas un simple template générique.",
  },
  {
    title: 'Une métrique à chaque étape',
    text: 'Aucune affirmation sans chiffre mesuré : OCR, extraction, classification, RAG et agent sont tous comparés objectivement, jamais juste "ça marche".',
  },
  {
    title: 'LLM et calcul strictement séparés',
    text: "Un LLM ne calcule jamais un montant lui-même. Il route vers l'outil déterministe approprié (SQL, calculatrice) et se contente de formuler la réponse.",
  },
  {
    title: 'Sécurité testée, pas supposée',
    text: "Isolation multi-tenant et résistance à l'injection de prompt dans un document, vérifiées par des tests d'attaque documentés, pas juste implémentées.",
  },
  {
    title: 'Démontrable à chaque étape',
    text: 'Le projet reste présentable même arrêté en cours de route : chaque brique (OCR, extraction, RAG, agent, API) fonctionne et se mesure indépendamment.',
  },
]

const METRICS = [
  { step: 'OCR', metric: 'CER (clean / scan / bad)', result: 'Tesseract 0.22 / 0.24 / 0.52 — PaddleOCR 0.23 / 0.30 / 0.46' },
  { step: 'Extraction', metric: 'F1 par champ', result: 'LLM 0.88–1.00 selon le champ, regex seul 0.00–0.99' },
  { step: 'Classification', metric: 'Accuracy', result: '100% (5 méthodes) — vocabulaire synthétique trivialement disjoint, voir limite méthodologique' },
  { step: 'RAG', metric: 'Recall@5 / faithfulness', result: '0.18 (vecteur) / 0.26 (hybride) / 0.44 (hybride+rerank) — faithfulness ≥ 0.92' },
  { step: 'Agent', metric: 'Bon choix d\'outil', result: '86% bon outil, 100% réponse correcte (7 questions test)' },
]

export default function About() {
  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '2.5rem 1rem' }}>
      <h1 style={{ marginBottom: '0.5rem' }}>AI Document Intelligence & RAG Agent</h1>
      <p style={{ color: 'var(--color-text-muted)', fontSize: '1.05rem' }}>
        Un système qui lit des factures marocaines (PDF ou scan), en extrait les champs
        structurés (ICE, IF, RC, montants, TVA...), permet de poser des questions en langage
        naturel sur les documents (RAG), et répond à des questions chiffrées via un agent qui
        interroge une vraie base de données — au lieu de deviner.
      </p>

      <div className="card" style={{ margin: '1.5rem 0' }}>
        <strong>Principe directeur</strong>
        <p style={{ margin: '0.4rem 0 0' }}>
          Un LLM ne doit jamais calculer un montant lui-même. Il route la question vers l'outil
          déterministe approprié (SQL, calculatrice) et se contente de formuler la réponse.
        </p>
      </div>

      <h2 style={{ marginTop: '2rem' }}>Ce qui le différencie d'un "chat with PDF" générique</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', marginTop: '1rem' }}>
        {DIFFERENTIATORS.map((d) => (
          <div key={d.title} className="card">
            <strong>{d.title}</strong>
            <p style={{ margin: '0.4rem 0 0', color: 'var(--color-text-muted)' }}>{d.text}</p>
          </div>
        ))}
      </div>

      <h2 style={{ marginTop: '2rem' }}>Résultats mesurés</h2>
      <div className="card" style={{ padding: 0, overflow: 'auto', marginTop: '1rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--color-border)' }}>
              {['Étape', 'Métrique', 'Résultat'].map((h) => (
                <th key={h} style={{ padding: '0.7rem 1rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {METRICS.map((m) => (
              <tr key={m.step} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '0.7rem 1rem', fontWeight: 600 }}>{m.step}</td>
                <td style={{ padding: '0.7rem 1rem', color: 'var(--color-text-muted)' }}>{m.metric}</td>
                <td style={{ padding: '0.7rem 1rem' }}>{m.result}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', marginTop: '0.6rem' }}>
        Chiffres mesurés sur le jeu de test dédié (jamais utilisé pour ajuster le code) — détail
        méthodologique complet dans <code>docs/eval/</code> du dépôt.
      </p>

      <div style={{ display: 'flex', gap: '0.8rem', marginTop: '2rem' }}>
        <Link to="/login" className="btn">
          Se connecter
        </Link>
        <Link to="/register" className="btn btn-secondary">
          Créer un compte
        </Link>
      </div>
    </div>
  )
}
