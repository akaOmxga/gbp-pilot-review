# 05 — Design des prompts IA

Document de référence pour l'appel Claude qui génère les réponses aux avis. Inclut le prompt système complet, le template utilisateur, le schéma JSON de sortie, la nomenclature exhaustive des codes `details`, et la stratégie de versioning.

## 1. Modèle et configuration

| Paramètre | Valeur |
|---|---|
| Modèle | `claude-sonnet-4-6` |
| `temperature` | `0.7` (équilibre créativité/cohérence pour des réponses humaines) |
| `max_tokens` | `600` |
| Tool use forcé | `submit_response` (force le format JSON) |
| Prompt caching | activé sur le bloc système |
| SDK | Anthropic Python SDK |

L'appel utilise le **tool use forcé** (paramètre `tool_choice={"type": "tool", "name": "submit_response"}`) plutôt que du parsing texte. C'est plus robuste qu'un `response_format: json_object` car le schéma est strictement validé par l'API.

### Coût estimé par appel

| Composant | Tokens (estim.) |
|---|---|
| Système (cacheable) | ~1500 |
| Utilisateur (variable) | 300–800 |
| Sortie | 200–400 |

Avec prompt caching, le coût d'un appel "chaud" est dominé par les tokens utilisateur + sortie (le système est facturé ~10% de son tarif quand cache hit). Calcul à raffiner après les premiers tests réels.

## 2. Schéma JSON de sortie

```json
{
  "status": 0,
  "content": "",
  "details": "content_too_sensitive"
}
```

ou en cas de succès :

```json
{
  "status": 1,
  "content": "Bonjour Sophie, merci beaucoup pour votre retour ! Nous sommes ravis que votre expérience ait été à la hauteur. À très vite chez nous.",
  "details": ""
}
```

### Définition de l'outil Anthropic

```python
SUBMIT_RESPONSE_TOOL = {
    "name": "submit_response",
    "description": (
        "Soumets ta décision et ta réponse à l'avis. "
        "Utilise status=1 si tu rédiges une réponse appropriée, "
        "status=0 si tu refuses (avec un code dans 'details')."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "integer",
                "enum": [0, 1],
                "description": "1 = réponse rédigée, 0 = refus de répondre"
            },
            "content": {
                "type": "string",
                "maxLength": 800,
                "description": "Texte de la réponse. Vide si status=0."
            },
            "details": {
                "type": "string",
                "enum": [
                    "content_too_sensitive",
                    "unclear_request",
                    "language_not_supported",
                    "requires_factual_info",
                    "personal_attack",
                    "legal_threat",
                    "competitor_mention",
                    "incoherent_review",
                    "off_topic",
                    "spam_or_fake",
                    "extreme_negative",
                    "request_for_contact",
                    ""
                ],
                "description": "Code de la nomenclature si status=0. Chaîne vide si status=1."
            }
        },
        "required": ["status", "content", "details"]
    }
}
```

## 3. Prompt système (cacheable)

> Le bloc ci-dessous est le **prompt système v1.0.0**. Il sera stocké dans `prompt_versions.system_prompt` et marqué `is_active=TRUE`. Toute modification = nouvelle version.

```
Tu es un assistant qui rédige des réponses aux avis Google Business Profile au nom d'une entreprise. Tu écris ces réponses comme si tu étais le gérant ou un membre de l'équipe de l'entreprise. Ton objectif : produire une réponse personnalisée, sincère et professionnelle qui renforce la relation client et l'e-réputation, OU refuser de répondre si l'avis présente un risque (sensibilité, juridique, manque d'information, etc.).

# Règles universelles (non négociables)

1. **Politesse et bienveillance systématiques.** Aucune réponse condescendante, ironique, ou agressive, même face à un avis injuste.
2. **Pas de promesses irréalistes.** N'écris jamais "nous allons rembourser", "nous allons licencier", "cela ne se reproduira plus jamais", "nous allons vous offrir X". Ce sont des engagements que seul un humain habilité peut prendre.
3. **Pas d'informations commerciales sensibles.** Ne mentionne jamais : prix exacts, promotions, codes promo, conditions de remboursement, politiques internes, noms d'employés (sauf si l'avis les mentionne déjà positivement et qu'il s'agit d'un remerciement neutre).
4. **Pas de mention de concurrents.** Si l'avis évoque un concurrent, ne le nomme pas dans ta réponse.
5. **Pas de réductions, cadeaux, gestes commerciaux.** Tu n'as pas l'autorité pour les promettre.
6. **Pas d'aveu de faute juridique.** Pour les avis évoquant un préjudice (santé, sécurité, juridique), tu DOIS refuser (status=0, details="legal_threat" ou "content_too_sensitive").
7. **Respect du contexte et du ton fournis.** Le contexte de l'entreprise et les instructions de ton du gérant priment sur tes réflexes par défaut.
8. **Langue de réponse.** Réponds dans la langue indiquée dans <response_language>. Si la langue est ni français ni anglais, refuse avec details="language_not_supported".
9. **Longueur.** Adapte-toi à l'avis : court (1-2 phrases) pour un avis court, plus développé (3-5 phrases) pour un avis détaillé. Maximum 800 caractères.
10. **Pas de signature systématique** sauf si demandée explicitement dans <tone_instructions>.

# Quand refuser de répondre (status=0)

Tu DOIS refuser dans les cas suivants. Choisis le code `details` le plus précis :

- **content_too_sensitive** : sujet juridique, médical, sécuritaire critique (intoxication alimentaire, blessure, plainte officielle, accusation grave). Une réponse humaine est indispensable.
- **legal_threat** : menace explicite de poursuites, mention d'avocat, plainte, procédure judiciaire.
- **personal_attack** : attaque nominative envers un employé identifié (insulte, accusation personnelle).
- **competitor_mention** : l'avis mentionne un concurrent et nécessite une gestion humaine de la comparaison.
- **incoherent_review** : l'avis est incompréhensible, vide de sens, ou ne peut être traité (texte aléatoire, lettres au hasard).
- **off_topic** : l'avis ne concerne manifestement pas l'établissement (ex : avis sur un autre commerce, contenu hors sujet).
- **spam_or_fake** : suspicion forte de faux avis (texte générique copié, chaîne de caractères suspecte, contenu publicitaire).
- **unclear_request** : l'avis pose une question spécifique sur l'entreprise dont la réponse n'est pas dans <business_context> et nécessite l'avis du gérant.
- **requires_factual_info** : l'avis demande une information factuelle précise non disponible (horaire exact d'un service, prix, disponibilité d'un produit, statut d'une commande).
- **language_not_supported** : la langue détectée n'est ni le français ni l'anglais.
- **extreme_negative** : avis exprimant une détresse, une colère extrême ou un préjudice grave qui dépasse une simple insatisfaction. Même filtré en amont, double-vérifie.
- **request_for_contact** : l'avis demande explicitement un contact direct (téléphone, email) et tu ne peux fournir ces coordonnées toi-même.

Si plusieurs codes s'appliquent, choisis le plus grave (ordre de priorité ci-dessus).

# Format de sortie

Tu DOIS appeler l'outil `submit_response` avec exactement trois champs :
- `status` : 1 si tu rédiges une réponse, 0 si tu refuses
- `content` : le texte de la réponse (vide si status=0, ≤ 800 caractères si status=1)
- `details` : le code de refus parmi la liste (chaîne vide si status=1)

N'écris jamais de texte hors de l'appel d'outil.
```

## 4. Prompt utilisateur (template)

> Stocké dans `prompt_versions.user_prompt_template`. Variables au format Jinja2.

```jinja
<business_context>
{{ business_context if business_context else "Aucun contexte spécifique fourni." }}
</business_context>

<tone_instructions>
{{ tone_instructions if tone_instructions else "Ton neutre et professionnel, vouvoiement, signature non requise." }}
</tone_instructions>

<response_language>{{ response_language }}</response_language>

{% if thread_history %}
<thread>
Voici l'historique du fil. Le client a répondu après notre première réponse. Génère la nouvelle réponse en cohérence avec ce fil.

{% for entry in thread_history %}
[{{ entry.author }} — {{ entry.posted_at_human }}]
{{ entry.text }}

{% endfor %}
</thread>
{% endif %}

<review_to_handle>
Auteur : {{ review_author_first_name or "Client" }}
Note : {{ review_rating }} / 5 étoiles
Langue détectée : {{ review_language }}

Texte de l'avis :
"""
{{ review_text if review_text else "(avis sans texte)" }}
"""
</review_to_handle>

Rédige maintenant la réponse en suivant les règles universelles et le ton fourni, ou refuse via l'outil submit_response.
```

### Variables injectées

| Variable | Source | Notes |
|---|---|---|
| `business_context` | `clients.business_context` | Champ libre client |
| `tone_instructions` | `clients.tone_instructions` | Construit à partir du formulaire guidé (tutoiement/vouvoiement, longueur, signature, éléments toujours/jamais mentionnés, champ libre) lors de l'onboarding |
| `response_language` | `client_settings.language_override` ou `reviews.language` | "fr", "en" |
| `review_text` | `reviews.comment` | Peut être NULL (avis sans texte) |
| `review_rating` | `reviews.rating` | 1-5 |
| `review_author_first_name` | `reviews.reviewer_first_name` | Extrait depuis `reviewer_display_name` |
| `review_language` | `reviews.language` | détectée via util `language.py` |
| `thread_history` | calculé pour Pro/Business si `parent_review_id` chaîné | Liste d'objets `{author, posted_at_human, text}` |

### Construction de `tone_instructions` depuis le formulaire

À l'onboarding, on rend les options du formulaire en texte qui sera stocké dans `clients.tone_instructions`. Exemple de rendu :

```
Adresse-toi aux clients en utilisant le vouvoiement.
Réponses de longueur courte à moyenne (2-4 phrases).
Signature : "L'équipe Boulangerie Marin".
Mentionne toujours : la possibilité de revenir, le mot "qualité".
Ne mentionne jamais : nos délais d'attente, la météo.
Notes additionnelles du gérant : nous tenons à un ton chaleureux et familial, n'hésite pas à utiliser des formulations conviviales ("À bientôt", "Au plaisir").
```

## 5. Nomenclature `details` exhaustive

Pour chaque code, on définit : description, condition côté IA, action métier (qui notifier, statut résultant), template de notification, action UI suggérée côté dashboard.

| Code | Description | Notifier | Template | Action UI |
|---|---|---|---|---|
| `content_too_sensitive` | Sujet juridique/santé/sécurité critique | Équipe + client | `ai_refusal_sensitive` | Rédiger manuellement, contacter le client par téléphone |
| `unclear_request` | L'avis pose une question hors contexte | Client | `ai_refusal_unclear` | Rédiger manuellement |
| `language_not_supported` | Langue ≠ fr/en | Client | `ai_refusal_language` | Rédiger manuellement ou ignorer |
| `requires_factual_info` | Demande d'info factuelle indisponible | Client | `ai_refusal_factual` | Rédiger manuellement |
| `personal_attack` | Attaque nominative envers un employé | Équipe + client | `ai_refusal_attack` | Rédiger manuellement, envisager signalement Google |
| `legal_threat` | Menace juridique explicite | Équipe + client | `ai_refusal_legal` | Ne pas répondre publiquement, contacter conseiller juridique |
| `competitor_mention` | Mention d'un concurrent | Client | `ai_refusal_competitor` | Rédiger manuellement |
| `incoherent_review` | Avis incohérent/incompréhensible | Client | `ai_refusal_incoherent` | Ignorer ou signaler à Google |
| `off_topic` | Avis hors sujet | Client | `ai_refusal_offtopic` | Signaler à Google |
| `spam_or_fake` | Suspicion de faux avis | Équipe + client | `ai_refusal_spam` | Signaler à Google |
| `extreme_negative` | Avis très négatif au-delà du filtre 1-3 | Équipe + client | `ai_refusal_extreme` | Rédiger manuellement avec attention particulière |
| `request_for_contact` | Demande de contact direct | Client | `ai_refusal_contact` | Rédiger manuellement avec coordonnées |
| `generation_error` | Erreur technique pipeline (réservé système) | Équipe + client | `generation_error` | Réessayer ou rédiger manuellement |

`generation_error` n'est jamais produit par l'IA elle-même : c'est le code que le `GenerationService` injecte si l'appel Claude échoue (timeout, JSON malformé non récupéré au retry, exception SDK).

## 6. Stratégie de versioning des prompts

### Modèle de données

Table `prompt_versions` (cf. `01-database.md`) avec :
- `version` (string sémantique : `v1.0.0`, `v1.1.0`, `v2.0.0`)
- `system_prompt` (le bloc complet de la section 3)
- `user_prompt_template` (le template Jinja2 de la section 4)
- `model`, `temperature`, `max_tokens`
- `is_active` boolean (un seul actif à la fois, contrainte d'unicité partielle)
- `notes` (changelog de la version)

### Workflow de mise à jour

1. Une nouvelle version est créée via une migration Alembic data (script `python -m app.scripts.create_prompt_version --from-file prompts/v1.1.0.md`).
2. La nouvelle ligne est insérée avec `is_active=FALSE`.
3. Validation manuelle : exécuter le script de tests prompt (cf. section 7) avec la nouvelle version.
4. Si OK, switch atomique en transaction : `UPDATE prompt_versions SET is_active=FALSE WHERE is_active=TRUE; UPDATE prompt_versions SET is_active=TRUE WHERE id=<new>;`.
5. À partir de cet instant, `prompt_repo.get_active()` retourne la nouvelle version pour tous les nouveaux appels.
6. Les `responses` déjà générées conservent leur `prompt_version_id` historique pour traçabilité.

### Conventions de version

- **Patch** (`v1.0.x`) : correction typo, reformulation mineure du prompt système.
- **Minor** (`v1.x.0`) : ajout d'un nouveau code `details`, ajustement de règles non-comportementales.
- **Major** (`vx.0.0`) : refonte structurelle, changement de `temperature`/`model`, modification du schéma JSON de sortie.

A/B testing différé en V2 : on pourrait permettre `is_active` sur deux versions avec une distribution `weight`. Pas implémenté au MVP — la version active est unique.

## 7. Tests des prompts

### Banc de test

Fichier `backend/tests/prompts/fixtures.json` avec ~10 avis de référence couvrant les cas critiques :

| # | Type | Note | Contenu | Sortie attendue |
|---|---|---|---|---|
| 1 | Positif simple | 5 | "Excellent service, je recommande !" | `status=1`, ton chaleureux |
| 2 | Positif détaillé | 5 | Avis long mentionnant un employé positivement | `status=1`, mention de l'expérience |
| 3 | Neutre | 4 | "Bien dans l'ensemble, sans plus." | `status=1`, ton mesuré |
| 4 | Sans texte 5★ | 5 | (vide) | bypass IA — template court |
| 5 | Avis négatif filtre amont | 2 | (déjà filtré côté pipeline) | n'arrive jamais à l'IA |
| 6 | Anglais | 5 | "Loved it!" | `status=1` en anglais |
| 7 | Question factuelle | 4 | "Vous êtes ouverts le dimanche ?" | `status=0`, `details=requires_factual_info` |
| 8 | Menace juridique | 5 | "Je vais porter plainte..." | `status=0`, `details=legal_threat` |
| 9 | Hors sujet | 3 | "Mon chien est mignon" | `status=0`, `details=off_topic` ou `incoherent_review` |
| 10 | Langue non supportée | 5 | "我喜欢你们的服务" | `status=0`, `details=language_not_supported` |

### Exécution

```bash
uv run pytest backend/tests/prompts/test_golden.py
```

Le test charge la version active de `prompt_versions`, fait l'appel Claude réel pour chaque avis, valide :
- la structure JSON
- le `status` attendu
- le `details` (pour status=0)
- la longueur de `content` (pour status=1)
- la langue de `content` (pour status=1, via détection)

À exécuter manuellement avant chaque switch de version active. Pas en CI car coût Claude.

### Métriques tracées en production

Après lancement bêta, requête analytique périodique :

- Taux de `ai_status=0` par code `details` — détecter les codes en explosion
- Taux de regénération demandée par les clients après IA — proxy de qualité
- Taux d'édition manuelle après validation — proxy de qualité (à instrumenter dans le frontend)
- Distribution de longueur des réponses

Ces métriques alimentent la décision de créer une nouvelle version de prompt (cf. Phase 11 du Roadmap : amélioration continue).

## 8. Bypass IA — réponses templates pour avis sans texte

Pour les avis sans texte avec policy `reply_4_5_only` ou `reply_all`, on n'appelle pas l'IA mais un **template fixe localisé** :

```python
NO_TEXT_TEMPLATES = {
    "fr": {
        5: "Merci pour votre note 5 étoiles ! Au plaisir de vous accueillir à nouveau.",
        4: "Merci pour votre note ! Nous espérons vous revoir bientôt.",
        3: "Merci pour votre retour. N'hésitez pas à nous partager vos impressions.",
    },
    "en": {
        5: "Thanks for the 5-star rating! We look forward to seeing you again.",
        4: "Thanks for your rating! Hope to see you soon.",
        3: "Thanks for your feedback. Feel free to share more about your experience.",
    },
}
```

Le `responses.source` est alors `manual_validator` ou un nouveau `template` (à trancher en Phase 3 ; je propose `source='ai'` avec `prompt_version_id=NULL` et `ai_model='template_no_text_v1'` pour rester sur deux sources). Pas de quota consommé.
