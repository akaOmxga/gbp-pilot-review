# 06 — Sécurité & Conformité

> Phase 7 de la [Roadmap.md](../Roadmap.md). Ce document décrit le modèle de
> menace, les contrôles techniques en place, la procédure incident, et
> l'alignement RGPD (Articles 15, 17, 30).

## Actifs protégés

| Actif | Sensibilité | Stockage |
|---|---|---|
| Tokens OAuth Google (access + refresh) | Critique | `oauth_credentials` colonnes `*_encrypted` (Fernet) |
| Mots de passe utilisateur | Critique | `users.password_hash` (Argon2id) |
| Refresh JWT | Élevée | Cookie HttpOnly + Secure (hors dev) + SameSite=lax |
| Reviews / réponses (PII clients finaux) | Élevée | Tables `reviews`, `responses` |
| Clés webhook Lemon Squeezy | Élevée | `.env` (jamais commité) |
| Secrets API (Claude, Resend, GBP) | Élevée | `.env` |

## Contrôles en place

| Domaine | Contrôle | Implémentation |
|---|---|---|
| Encryption at-rest | Fernet (cryptography) | `app/security/encryption.py` + `EncryptedString` TypeDecorator |
| Hash mots de passe | Argon2id | `app/security/auth.py` (argon2-cffi) |
| Sessions | JWT HS256, refresh en cookie HttpOnly/Secure/SameSite | `app/security/auth.py`, `app/api/v1/auth.py` |
| Rate limiting | slowapi (signup 3/h, login 5/min, global 1000/min) | `app/main.py`, `app/config.py` |
| Webhook integrity | HMAC-SHA256 + `hmac.compare_digest` | `app/integrations/lemonsqueezy/webhooks.py` |
| Headers sécurité | CSP, HSTS (prod), X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy | `app/utils/security_headers.py` |
| Injection SQL | ORM SQLAlchemy uniquement (pas de raw SQL) | repos/services |
| CORS | Origine unique = `FRONTEND_URL` | `app/main.py` |
| Logs | Redaction Bearer/JWT/champs sensibles | `app/logging_config.py` |
| Soft-delete + purge J+30 | Celery `purge_expired_data` quotidien 03:15 UTC | `app/tasks/maintenance_tasks.py` |

## Procédure incident

1. Détection : alerte Sentry (P1/P2) ou rapport utilisateur.
2. Confinement : révoquer les tokens compromis (`OAuthService.revoke`), invalider les JWT (rotation `JWT_SECRET`), bloquer l'IP via slowapi/reverse-proxy.
3. Investigation : Sentry + logs structurés (corrélation via `X-Correlation-ID`, rétention 30j Sentry).
4. Notification RGPD : si fuite données personnelles → CNIL sous 72h (Art. 33 RGPD).
5. Post-mortem : rédiger doc + actions correctives dans `Roadmap.md`.

Contact : `victor.simon760@gmail.com` (DPO de facto pendant la phase bêta).

## Conformité RGPD

### Bases légales

| Traitement | Base | Durée |
|---|---|---|
| Compte utilisateur | Exécution contrat (Art. 6.1.b) | Vie du compte + 30j |
| Réponses générées | Exécution contrat | Vie du compte + 30j |
| Logs techniques | Intérêt légitime (Art. 6.1.f) | 30j (Sentry) |
| Webhook events | Obligation légale comptable | 10 ans (facturation) |
| Métriques anonymisées | Intérêt légitime | Indéfinie |

### Droits utilisateur

- **Art. 15 — Accès** : `GET /api/v1/me/export` retourne un JSON complet (user, client, settings, locations, reviews, responses, subscription, notification_preference).
- **Art. 17 — Effacement** : `DELETE /api/v1/me` → soft-delete immédiat. Purge cron J+30 (`maintenance_tasks.purge_expired_data`).
- **Art. 20 — Portabilité** : couvert par l'endpoint export (JSON machine-readable).
- **Art. 16 — Rectification** : `PATCH /api/v1/me/settings` + endpoints clients.

### Registre des traitements (Art. 30)

| Finalité | Catégories de données | Destinataires | Transferts | Durée |
|---|---|---|---|---|
| Authentification | email, hash mdp | aucun | UE | vie compte + 30j |
| Génération réponses IA | reviews, contexte business | Anthropic (Claude API) | US (DPA Anthropic) | vie compte + 30j |
| Publication GBP | tokens OAuth, contenu réponses | Google | US (DPA Google) | vie compte + 30j |
| Notifications | email, telegram_chat_id | Resend, Telegram | US/UE | vie compte + 30j |
| Facturation | nom, email, plan | Lemon Squeezy (MoR) | US (DPA LS) | 10 ans |
| Monitoring erreurs | logs anonymisés | Sentry | UE | 30j |

### Sous-traitants

| Prestataire | Service | DPA | Pays |
|---|---|---|---|
| Google LLC | OAuth + Business Profile API | [Google Workspace DPA](https://workspace.google.com/terms/dpa_terms.html) | US (SCCs) |
| Anthropic PBC | Claude API (génération réponses) | [Anthropic DPA](https://www.anthropic.com/legal/dpa) | US (SCCs) |
| Lemon Squeezy (Stripe Inc.) | Merchant of Record (paiements) | inclus contrat MoR | US (SCCs) |
| Resend | Envoi emails transactionnels | DPA standard | US (SCCs) |
| Sentry (Functional Software, Inc.) | Error monitoring | DPA + EU region | UE/US |
| Hébergeur VPS (OVH/Hetzner) | Infrastructure | DPA standard | UE |

> ⚠️ Avant lancement production : signer/archiver les DPA des sous-traitants
> listés ci-dessus, et faire valider le template DPA client par un juriste.

## Hardening complémentaire (recommandé)

- [ ] Activer 2FA admin (`User.mfa_enabled` est présent mais non implémenté côté API)
- [ ] Audit log structuré pour actions admin (`audit_logs` table existe)
- [ ] Scan de dépendances : `pip-audit` ou `safety` en CI
- [ ] Pen-test externe avant ouverture publique
- [ ] CSP stricte avec nonce si UI servie depuis backend (actuellement API-only → CSP `default-src 'self'` suffisante)
