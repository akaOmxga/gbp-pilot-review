"""Minimal email/telegram templates indexed by event_type.

Each template returns (subject, html_body, text_body). Variables are interpolated via
str.format(**payload).
"""

from typing import Any

_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "review_filtered": (
        "Avis filtré — {business_name}",
        "<p>Un avis a été filtré (regex blocklist).</p><p>{review_excerpt}</p>",
        "Un avis a été filtré (regex blocklist).\n{review_excerpt}",
    ),
    "ai_refusal_sensitive": (
        "Action requise : avis sensible",
        "<p>L'IA a refusé de répondre (sujet sensible). Rédaction manuelle requise.</p>",
        "L'IA a refusé de répondre (sujet sensible). Rédaction manuelle requise.",
    ),
    "ai_refusal_unclear": (
        "Action requise : avis ambigu",
        "<p>L'IA a refusé : demande hors contexte. À rédiger manuellement.</p>",
        "L'IA a refusé : demande hors contexte. À rédiger manuellement.",
    ),
    "ai_refusal_language": (
        "Avis dans une langue non supportée",
        "<p>L'avis est dans une langue ≠ fr/en. À traiter manuellement ou ignorer.</p>",
        "Avis dans une langue non supportée.",
    ),
    "ai_refusal_factual": (
        "Demande d'info factuelle dans un avis",
        "<p>L'IA a refusé : info factuelle indisponible. Réponse manuelle requise.</p>",
        "Demande d'info factuelle. Réponse manuelle requise.",
    ),
    "ai_refusal_attack": (
        "Attaque personnelle dans un avis",
        "<p>Avis contenant une attaque personnelle. Rédaction prudente recommandée.</p>",
        "Attaque personnelle dans un avis. Rédaction prudente recommandée.",
    ),
    "ai_refusal_legal": (
        "Menace juridique — ne pas répondre publiquement",
        "<p>Menace juridique détectée. Contacter un conseiller juridique.</p>",
        "Menace juridique détectée. Contacter un conseiller juridique.",
    ),
    "ai_refusal_competitor": (
        "Mention d'un concurrent",
        "<p>Avis mentionnant un concurrent. Rédaction manuelle recommandée.</p>",
        "Avis mentionnant un concurrent.",
    ),
    "ai_refusal_incoherent": (
        "Avis incohérent",
        "<p>Avis incohérent ou incompréhensible. Ignorer ou signaler à Google.</p>",
        "Avis incohérent.",
    ),
    "ai_refusal_offtopic": (
        "Avis hors sujet",
        "<p>Avis hors sujet. Possibilité de signalement à Google.</p>",
        "Avis hors sujet.",
    ),
    "ai_refusal_spam": (
        "Spam/faux avis détecté",
        "<p>Suspicion de faux avis. Signaler à Google.</p>",
        "Suspicion de faux avis.",
    ),
    "ai_refusal_extreme": (
        "Avis extrêmement négatif",
        "<p>Avis très négatif au-delà du filtre 1-3. Rédaction avec attention particulière.</p>",
        "Avis très négatif. Rédaction prudente.",
    ),
    "ai_refusal_contact": (
        "Demande de contact direct",
        "<p>Avis demandant un contact direct. Préparer une réponse avec coordonnées.</p>",
        "Demande de contact direct.",
    ),
    "generation_error": (
        "Erreur génération IA",
        "<p>Échec technique du pipeline IA. Réessayer ou rédiger manuellement.</p>",
        "Échec génération IA.",
    ),
    "oauth_revoked": (
        "Connexion Google interrompue",
        "<p>Le token Google a été révoqué. Reconnectez votre compte depuis le dashboard.</p>",
        "Token Google révoqué — reconnexion requise.",
    ),
    "publish_failed": (
        "Échec publication d'une réponse",
        "<p>La publication d'une réponse a échoué : {failure_reason}</p>",
        "Échec publication : {failure_reason}",
    ),
    "publish_succeeded": (
        "Réponse publiée",
        "<p>Votre réponse a été publiée sur Google.</p>",
        "Réponse publiée sur Google.",
    ),
    "quota_warning_80": (
        "Quota IA à 80%",
        "<p>Vous avez consommé 80% de votre quota mensuel. Pensez à upgrader.</p>",
        "Quota IA à 80%.",
    ),
    "quota_exhausted": (
        "Quota IA épuisé",
        "<p>Quota mensuel épuisé. Les nouveaux avis sont mis en attente jusqu'au reset.</p>",
        "Quota IA épuisé.",
    ),
    "human_validation_requested": (
        "Validation requise",
        "<p>Une réponse attend votre validation dans le dashboard.</p>",
        "Validation requise.",
    ),
    "subscription_changed": (
        "Abonnement mis à jour",
        "<p>Votre abonnement a évolué : {tier} ({status}).</p>",
        "Abonnement : {tier} ({status}).",
    ),
}


def render(event_type: str, payload: dict[str, Any]) -> tuple[str, str, str]:
    template = _TEMPLATES.get(event_type) or _TEMPLATES["generation_error"]
    subject, html, text = template
    safe = {k: str(v) for k, v in payload.items()}
    return (
        subject.format_map(_DefaultDict(safe)),
        html.format_map(_DefaultDict(safe)),
        text.format_map(_DefaultDict(safe)),
    )


class _DefaultDict(dict):  # type: ignore[type-arg]
    def __missing__(self, key: str) -> str:
        return ""
