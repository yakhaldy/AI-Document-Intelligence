export default function Legal() {
  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '2.5rem 1rem' }}>
      <h1>Informations légales</h1>
      <p style={{ color: 'var(--color-text-muted)' }}>
        AI Document Intelligence est un projet personnel de démonstration technique (portfolio),
        pas un service commercial. Ces pages reflètent honnêtement ce que fait réellement
        l'application, sans jargon juridique inutile.
      </p>

      <h2 id="mentions" style={{ marginTop: '2rem' }}>
        Mentions légales
      </h2>
      <div className="card">
        <p>
          Éditeur : Yahya Khaldy, développeur individuel — projet personnel non commercial.
          <br />
          Code source : <a href="https://github.com/yakhaldy/AI-Document-Intelligence">github.com/yakhaldy/AI-Document-Intelligence</a>
          <br />
          Hébergement : instance de démonstration sur un serveur cloud (Oracle Cloud), sans nom de
          domaine dédié à ce stade.
          <br />
          Contact : via une issue sur le dépôt GitHub ci-dessus.
        </p>
      </div>

      <h2 id="confidentialite" style={{ marginTop: '2rem' }}>
        Politique de confidentialité
      </h2>
      <div className="card">
        <p>Ce que l'application stocke réellement, sans plus :</p>
        <ul>
          <li>Un compte utilisateur (identifiant, mot de passe haché) — pas d'adresse e-mail demandée.</li>
          <li>Les documents que vous uploadez vous-même (factures, contrats, rapports) et les données qui en sont extraites.</li>
          <li>Aucun cookie n'est déposé : la session est un jeton (JWT) conservé dans le stockage local de votre navigateur, pas un cookie.</li>
          <li>Aucun traceur publicitaire, aucun partage avec un tiers commercial.</li>
          <li>Un outil d'observabilité technique (Langfuse) peut enregistrer les appels aux modèles de langage utilisés en interne (latence, coût), sans finalité commerciale.</li>
        </ul>
        <p>
          Étant un projet de démonstration, il n'y a pas encore de formulaire self-service pour
          exporter ou supprimer son compte — une demande via GitHub sera traitée manuellement.
        </p>
      </div>

      <h2 id="cgu" style={{ marginTop: '2rem' }}>
        Conditions d'utilisation
      </h2>
      <div className="card">
        <p>
          Cette instance est fournie à titre de démonstration, "en l'état", sans garantie de
          disponibilité ni d'exactitude des résultats d'extraction/classification. Ne téléversez
          pas de documents contenant des informations sensibles que vous ne voulez pas voir
          traitées par un modèle de langage tiers (le pipeline d'extraction/RAG appelle des API
          LLM externes).
        </p>
      </div>
    </div>
  )
}
