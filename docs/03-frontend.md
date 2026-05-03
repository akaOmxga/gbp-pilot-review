# 03 — Architecture frontend

Document de référence pour la structure du code Next.js, les routes, les composants partagés, l'authentification et la stratégie i18n.

## 1. Stack confirmée

| Couche | Choix | Notes |
|---|---|---|
| Framework | Next.js 14+ (App Router) | rendering serveur par défaut, client components ciblés |
| Langage | TypeScript strict | `strict: true` dans `tsconfig.json` |
| UI | Tailwind CSS + shadcn/ui | composants copiés dans `components/ui/`, customizables |
| Auth | NextAuth.js (Auth.js v5) | credentials provider vers backend |
| i18n | next-intl | fr actif, en stub |
| Data fetching | TanStack Query v5 | côté client, invalidation explicite après mutations |
| Validation | Zod | schémas partagés entre formulaires et API client |
| Forms | React Hook Form + Zod resolver | |
| Icônes | lucide-react | |
| Tests | Vitest + Testing Library + Playwright | |

Pas de Redux/Zustand au MVP — l'état serveur via TanStack Query suffit.

## 2. Arborescence

```
frontend/
├── package.json
├── next.config.mjs
├── tsconfig.json
├── tailwind.config.ts
├── components.json              # config shadcn
├── middleware.ts                # i18n + auth gating
├── app/
│   ├── layout.tsx               # racine, providers globaux
│   ├── globals.css
│   ├── [locale]/
│   │   ├── layout.tsx           # NextIntlClientProvider, ThemeProvider
│   │   │
│   │   ├── (marketing)/
│   │   │   ├── layout.tsx       # header public + footer
│   │   │   ├── page.tsx         # landing
│   │   │   ├── pricing/page.tsx
│   │   │   ├── about/page.tsx
│   │   │   ├── terms/page.tsx
│   │   │   ├── privacy/page.tsx
│   │   │   ├── dpa/page.tsx
│   │   │   └── contact/page.tsx
│   │   │
│   │   ├── (auth)/
│   │   │   ├── layout.tsx       # layout centré, logo
│   │   │   ├── login/page.tsx
│   │   │   ├── signup/page.tsx
│   │   │   ├── verify-email/page.tsx
│   │   │   ├── forgot-password/page.tsx
│   │   │   └── reset-password/page.tsx
│   │   │
│   │   ├── onboarding/
│   │   │   ├── layout.tsx       # progress stepper
│   │   │   ├── page.tsx         # bienvenue
│   │   │   ├── connect-google/page.tsx
│   │   │   ├── customize/page.tsx
│   │   │   └── complete/page.tsx
│   │   │
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx       # sidebar + topbar, auth guard client
│   │   │   ├── page.tsx         # accueil métriques
│   │   │   ├── reviews/
│   │   │   │   ├── page.tsx     # liste paginée + filtres
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── pending/page.tsx
│   │   │   ├── settings/
│   │   │   │   ├── page.tsx     # tabs : preferences | filters | publication | notifications
│   │   │   │   └── loading.tsx
│   │   │   └── billing/page.tsx
│   │   │
│   │   └── admin/
│   │       ├── layout.tsx       # garde role=admin
│   │       ├── page.tsx         # dashboard admin (stats globales)
│   │       ├── clients/
│   │       │   ├── page.tsx
│   │       │   └── [id]/page.tsx
│   │       ├── validation-queue/page.tsx
│   │       ├── monitoring/page.tsx
│   │       └── deletions/page.tsx
│   │
│   └── api/
│       ├── auth/[...nextauth]/route.ts
│       └── oauth/google/callback/route.ts  # forward vers backend
│
├── components/
│   ├── ui/                      # shadcn (button, card, dialog, etc.)
│   ├── marketing/
│   │   ├── hero.tsx
│   │   ├── pricing-table.tsx
│   │   └── feature-grid.tsx
│   ├── auth/
│   │   ├── login-form.tsx
│   │   └── signup-form.tsx
│   ├── reviews/
│   │   ├── review-card.tsx
│   │   ├── review-list.tsx
│   │   ├── review-detail.tsx
│   │   ├── rating-stars.tsx
│   │   └── status-badge.tsx
│   ├── responses/
│   │   ├── response-editor.tsx
│   │   ├── response-actions.tsx     # validate / regenerate / write / ignore
│   │   ├── regenerate-button.tsx    # gère quota et limite tier
│   │   └── undo-toast.tsx           # countdown 10 min
│   ├── settings/
│   │   ├── publication-settings.tsx
│   │   ├── notification-settings.tsx
│   │   ├── regex-blocklist.tsx
│   │   └── customization-form.tsx   # disabled au MVP, lien support
│   ├── shared/
│   │   ├── app-shell.tsx
│   │   ├── sidebar.tsx
│   │   ├── topbar.tsx
│   │   ├── empty-state.tsx
│   │   ├── error-state.tsx
│   │   ├── confirm-dialog.tsx
│   │   ├── metric-card.tsx
│   │   ├── data-table.tsx
│   │   ├── pagination.tsx
│   │   └── locale-switcher.tsx
│   └── admin/
│       ├── client-row.tsx
│       ├── validation-queue-item.tsx
│       └── job-status-grid.tsx
│
├── lib/
│   ├── api-client.ts            # fetch wrapper, attache JWT, gestion 401
│   ├── api-types.ts             # types DTO partagés (générés depuis OpenAPI)
│   ├── auth.ts                  # NextAuth config
│   ├── i18n.ts                  # config next-intl
│   ├── permissions.ts           # helpers role-based
│   ├── format.ts                # date, devise, plural
│   └── utils.ts                 # cn() shadcn, etc.
│
├── hooks/
│   ├── use-reviews.ts           # TanStack Query
│   ├── use-pending-reviews.ts
│   ├── use-review.ts
│   ├── use-settings.ts
│   ├── use-quota.ts
│   ├── use-subscription.ts
│   └── use-undo-publication.ts  # countdown + cancel
│
├── messages/
│   ├── fr.json                  # exhaustif au MVP
│   └── en.json                  # stub avec les mêmes clés
│
└── types/
    ├── api.ts                   # types backend DTO
    └── next-auth.d.ts           # extension session avec role/clientId
```

## 3. Stratégie d'authentification et session

### Login standard (email/password)

NextAuth credentials provider qui appelle `POST /api/v1/auth/login` côté backend, récupère un JWT, le stocke dans la session NextAuth. La session expose `user.id`, `user.email`, `user.role`, `user.clientId`, `user.accessToken`.

```typescript
// frontend/lib/auth.ts (extrait)
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { apiClient } from "@/lib/api-client";

export const { auth, handlers, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      credentials: { email: {}, password: {} },
      authorize: async (creds) => {
        const res = await apiClient.post("/api/v1/auth/login", creds);
        if (!res.ok) return null;
        const data = await res.json();
        return {
          id: data.user.id,
          email: data.user.email,
          role: data.user.role,
          clientId: data.user.client_id,
          accessToken: data.access_token,
        };
      },
    }),
  ],
  session: { strategy: "jwt", maxAge: 60 * 60 },
  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        token.role = user.role;
        token.clientId = user.clientId;
        token.accessToken = user.accessToken;
      }
      return token;
    },
    session: async ({ session, token }) => {
      session.user.role = token.role as "client" | "admin";
      session.user.clientId = token.clientId as string | null;
      session.user.accessToken = token.accessToken as string;
      return session;
    },
  },
});
```

### Middleware — routing protégé

```typescript
// frontend/middleware.ts
import createMiddleware from "next-intl/middleware";
import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";

const intl = createMiddleware({
  locales: ["fr", "en"],
  defaultLocale: "fr",
  localePrefix: "always",
});

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isAuthed = !!req.auth;
  const role = req.auth?.user.role;

  const isDashboard = /^\/(fr|en)\/(dashboard|reviews|pending|settings|billing|onboarding)/.test(pathname);
  const isAdmin = /^\/(fr|en)\/admin/.test(pathname);

  if ((isDashboard || isAdmin) && !isAuthed) {
    return NextResponse.redirect(new URL("/fr/login", req.url));
  }
  if (isAdmin && role !== "admin") {
    return NextResponse.redirect(new URL("/fr/dashboard", req.url));
  }
  return intl(req);
});

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
```

### OAuth Google Business — séparé

Important : le flow OAuth Google Business **n'utilise pas NextAuth**. C'est un OAuth de service (autorisation d'accéder aux locations du client), pas un login. Le flow :

1. Client connecté clique "Connecter mon compte Google" sur `/onboarding/connect-google`
2. Le bouton appelle `GET ${BACKEND_URL}/api/v1/oauth/google/start` (avec JWT)
3. Le backend redirige vers `accounts.google.com` avec `state` signé
4. Google redirige vers `/api/oauth/google/callback` (route handler Next.js) qui forward vers backend
5. Backend persiste les tokens, redirige vers `/onboarding/customize`

Détails dans `04-flows.md`.

## 4. Composants réutilisables clés

| Composant | Rôle | Particularités |
|---|---|---|
| `<ReviewCard />` | Carte récapitulative d'un avis | Note, extrait, langue, statut, avatar reviewer |
| `<ReviewDetail />` | Vue détaillée + thread + réponses | Affiche les versions de réponses |
| `<ResponseEditor />` | Éditeur de réponse (textarea + compteur) | Limite 800 chars, validation Zod |
| `<ResponseActions />` | Boutons valider/refuser/regénérer/rédiger | États dérivés du statut |
| `<RegenerateButton />` | Bouton regen avec quota | Désactivé si quota atteint, tooltip explicatif |
| `<StatusBadge />` | Badge couleur par statut | Mapping centralisé statuts → couleurs |
| `<RatingStars />` | Affichage 5 étoiles | Read-only |
| `<MetricCard />` | Carte de KPI (label, valeur, delta) | Skeleton intégré |
| `<EmptyState />` | Vide gracieux | Icône + titre + CTA optionnel |
| `<UndoToast />` | Toast avec countdown 10 min | Hook `useUndoPublication` |
| `<ConfirmDialog />` | Dialog de confirmation | Variant `destructive` rouge |
| `<DataTable />` | Tableau générique | Pagination, tri, filtres |

### Mapping statut → couleur (centralisé)

```typescript
// frontend/lib/status.ts
export const reviewStatusLabel = {
  detected: { label: "Reçu", color: "neutral" },
  filtering: { label: "Analyse", color: "neutral" },
  blocked_regex: { label: "Bloqué (filtre)", color: "amber" },
  requires_human_validation: { label: "Validation requise", color: "amber" },
  processing: { label: "En traitement", color: "blue" },
  awaiting_response: { label: "Réponse prête", color: "blue" },
  completed: { label: "Publié", color: "green" },
} as const;

export const responseStatusLabel = {
  draft: { label: "Brouillon", color: "neutral" },
  pending_validation_client: { label: "À valider", color: "amber" },
  pending_validation_team: { label: "Validation équipe", color: "purple" },
  awaiting_publication: { label: "Programmée", color: "blue" },
  scheduled: { label: "Programmée", color: "blue" },
  publishing: { label: "Publication...", color: "blue" },
  published: { label: "Publiée", color: "green" },
  failed: { label: "Échec", color: "red" },
  cancelled: { label: "Annulée", color: "neutral" },
  superseded: { label: "Remplacée", color: "neutral" },
} as const;
```

## 5. Design system shadcn

### Composants à installer dès le départ

```bash
npx shadcn@latest add button card dialog dropdown-menu form input \
  label select table tabs toast badge tooltip separator skeleton \
  switch textarea avatar checkbox popover radio-group sheet \
  alert alert-dialog progress
```

### Tokens de couleur (`globals.css`)

Palette neutre Tailwind (zinc) + accent `emerald` (cohérent avec un produit "réponse positive aux avis"). Configuration shadcn en mode `slate` ajustée. Mode sombre prêt techniquement mais non exposé en V1 dans l'UI (pas de toggle).

### Conventions

- Tous les composants UI custom utilisent `cn()` de `@/lib/utils` pour merger les classes Tailwind.
- Pas de styled-components ni CSS modules — Tailwind only.
- Tailles d'écran : `sm` (640px), `md` (768px), `lg` (1024px), `xl` (1280px). Mobile-first, dashboard fonctionnel dès `sm`.

## 6. Stratégie i18n

### Configuration

```typescript
// frontend/lib/i18n.ts
import { getRequestConfig } from "next-intl/server";

export default getRequestConfig(async ({ locale }) => ({
  messages: (await import(`../messages/${locale}.json`)).default,
}));
```

### Conventions

- Tous les strings UI **doivent** passer par `useTranslations()` (client) ou `getTranslations()` (server). Aucun string en dur dans les composants exposés à l'utilisateur.
- Clés organisées par domaine : `common.*`, `auth.*`, `reviews.*`, `settings.*`, `errors.*`, `status.*`.
- `messages/fr.json` est la source de vérité au MVP. `messages/en.json` est un stub avec les **mêmes clés** mais les valeurs en français (sera traduit en V2).
- Lint custom : un script CI vérifie que les deux fichiers ont exactement les mêmes clés.

### Routing

`[locale]` segment dans toutes les routes. Middleware redirige `/` → `/fr/`. Le commutateur de locale est en pied de page (caché à l'utilisateur en V1 puisqu'une seule locale est réellement disponible).

## 7. Data fetching et état

### TanStack Query

```typescript
// frontend/hooks/use-reviews.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useReviews(params: { status?: string; page?: number }) {
  return useQuery({
    queryKey: ["reviews", params],
    queryFn: () => apiClient.get("/api/v1/reviews", { params }).json(),
    staleTime: 30_000,
  });
}
```

### Conventions

- Une `queryKey` par ressource, structurée en tableau : `["reviews", { status, page }]`, `["review", id]`.
- Mutations explicites avec `useMutation` + `queryClient.invalidateQueries(["reviews"])` après succès.
- Toasts d'erreur via `sonner` (intégré shadcn) systématiques.
- Optimistic updates uniquement pour les actions à faible enjeu (toggle settings). Validation/publication = pas d'optimistic.

### Polling temps réel

Les statuts changeants (queue de validation, publications en cours) sont rafraîchis via `refetchInterval: 15_000` dans les query options des pages concernées (`/pending`, `/admin/validation-queue`, `/admin/monitoring`). Pas de WebSockets au MVP.

## 8. Responsive et accessibilité

- **Mobile-first** : tous les composants testés à 375px.
- **Sidebar** : fixe en `lg`, drawer en `< lg` (utilise `<Sheet />` shadcn).
- **Tableaux** : conversion en cartes empilées en `< md` via composant `<ResponsiveDataTable />`.
- **Focus visible** : `focus-visible:ring-2 ring-emerald-500` partout.
- **Contraste** : niveau AA minimum (vérifié via plugin Tailwind `tailwindcss-accessibility` ou audit manuel Lighthouse).
- **Aria** : labels explicites sur les boutons icône, `aria-live="polite"` sur les toasts, `role="status"` sur les chargements.
- **Lecteur d'écran** : tous les statuts ont un texte explicite (pas que de la couleur).

## 9. Bootstrap local et commandes

```bash
pnpm install
pnpm dev                             # Next.js dev server
pnpm build && pnpm start             # build + run prod
pnpm test                            # Vitest
pnpm test:e2e                        # Playwright
pnpm lint                            # ESLint
pnpm typecheck                       # tsc --noEmit
pnpm i18n:check                      # vérifie parité fr/en
```

`.env.local` exemple :

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<openssl rand -base64 32>
```
