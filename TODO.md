# TODO — Dette technique et points à traiter plus tard

Liste extensible des sujets identifiés mais reportés. Format : un bullet par sujet, avec date d'ouverture, contexte, et impact.

---

## Backend

- **[2026-05-19] Tests asyncpg cassés sous Python 3.13 en local**
  - **Symptôme** : 55 tests sur 110 échouent avec `asyncpg.InterfaceError: cannot perform operation: another operation is in progress`
  - **Contexte** : apparu après mise à jour Arch Python 3.12 → 3.13. Le code n'a pas changé.
  - **Cause probable** : régression d'isolation entre tests dans `pytest-asyncio` / `asyncpg` sur Python 3.13 (event loop mal nettoyée entre tests, sessions zombies)
  - **Impact** : tests fonctionnent toujours sur CI (Python 3.12 fixé par le Dockerfile) — bloque uniquement le run local sous Arch
  - **Pistes** : downgrade local en 3.12 via `uv python install 3.12`, ou fix conftest pour forcer le close des sessions

---

## Frontend

_(rien pour l'instant)_

---

## Infrastructure / Déploiement

_(rien pour l'instant)_

---

## Sécurité / Conformité

_(rien pour l'instant)_