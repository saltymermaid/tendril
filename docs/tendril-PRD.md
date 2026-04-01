# Tendril — Product Requirements Document

## Overview

Tendril is a personal gardening planning and tracking app for a single user (with Google OAuth authentication) in USDA Zone 10a (St. Petersburg, Florida). The app's primary purpose is to support food production through succession planting, helping the user plan what to plant, when to plant it, and when to harvest — with the goal of reducing grocery purchases through continuous yield.

Succession planting in this context means staggering plantings over time so that harvests are spread evenly across weeks rather than arriving all at once. For example, instead of planting four squares of radishes simultaneously, the user plants one square every two weeks to maintain a steady supply.

The app is a Progressive Web App (PWA) optimized for iPhone, self-hosted on a Beelink mini PC running Ubuntu Server via Docker containers, with external access through a custom domain (tendril.garden, registered with Cloudflare) and Cloudflare Tunnel.

---

## Phased Roadmap

### Phase 1 — Core Planning & Tracking
- Authentication (Google OAuth)
- Container management (garden beds + tower)
- Square support structures (trellis, cage, pole)
- Seed catalog (categories, varieties, planting seasons)
- Grid-based planting with companion planting rules
- Planting model with planning and tracking (Not Started → In Progress → Complete)
- Seed packet photo import via Claude API
- Structured events (planting, harvesting) and free-form journal notes
- Gantt chart timeline views (full year + rolling 3-month) with computed lifecycle phases
- Time-slider garden view (view any bed at any date)
- Multi-bed overview (all beds at a glance with mini-grids)
- "What can I plant here?" recommendation engine
- Task system (auto-generated from planting data + manual tasks)
- Irrigation tracking (structured, per-bed)
- Weather display on main page (display only, no task integration)
- PWA with push notifications
- Main page: weekly tasks + weather

### Phase 2 — Intelligence & Integration
- Weather-triggered tasks (frost warnings, irrigation skip suggestions)
- AI plant diagnostics (contextual, attached to a plant/square, with diagnosis logged)
- Florida-specific RAG resources for plant doctor context
- Harvest reporting and analytics
- Yard layout view (spatial map of bed locations)

### Phase 3 — Future Considerations
- Multi-user support
- Additional container types (pots, row gardens)
- Other features as identified

---

## Authentication

The app uses Google OAuth for authentication. Even though the app currently serves a single user, auth is implemented from the start because the app is publicly accessible via Cloudflare Tunnel. The system restricts access to a whitelist of allowed Google accounts (initially one), configured via environment variable.

---

## Container Model

The app tracks plants in **containers**, which come in different types. All containers have a name, location description, and irrigation configuration.

### Container Types

**Grid Bed:** A rectangular raised bed measured in whole feet (e.g., 4×4, 2×4). Subdivided into 1×1-foot squares following square foot gardening principles. Each square can hold a planting or be part of a multi-square planting. The UI renders these as an interactive grid.

**Tower:** A vertical planter organized by **levels** (layers). Each level contains multiple pockets, but the user plants the same thing across all pockets on a given level — so the level is the unit of planting, not the individual pocket. A tower is configured with a number of levels and pockets per level. The UI renders towers differently from grid beds (stacked horizontal layers). Each level functions like a single square for planting purposes. All tower plantings are single-level — no plant spans multiple levels.

The data model should use a base container entity with a `type` field to distinguish bed types. Grid beds get square-foot subdivisions; towers get numbered levels. This should be extensible for future container types (pots, row gardens, etc.).

### Support Structures

Individual squares in a grid bed can have a **support structure** attached:

- **Trellis** — a vertical growing surface for climbing/vining plants. Typically placed along one side of a bed, but modeled per-square (an arched trellis connecting two beds is treated as two separate trellises in the app).
- **Cage** — a tomato cage or similar enclosure on a single square.
- **Pole** — a single stake or pole on a single square.

Support structures are optional metadata on a square. When a square has a trellis, the recommendation engine and planting UI will **warn** (not block) if the user attempts to plant a non-climbing/vining variety there. This is a soft constraint, similar to companion planting warnings.

Support structures do not apply to tower levels.

### Current Garden Inventory (Seed Data)
- Three 4×4 raised beds
- One 2×4 mobile raised bed
- One tower (7 levels, 6 pockets per level)

---

## Irrigation Tracking

Each container has a structured irrigation configuration:

- **Type:** drip, manual, sprinkler (enum, not free-form)
- **Duration:** minutes per watering session
- **Frequency:** daily, 2× daily, every X days, or specific days of the week

This is structured data stored per container, not a free-text note. In Phase 2, irrigation data will integrate with weather data to generate smart task suggestions (e.g., "skip watering today — rain expected").

---

## Seed Catalog

### Categories

Plants are organized into **categories** (e.g., Tomatoes, Peppers, Onions, Eggplant). Each category has:

- **Name** (e.g., "Tomatoes")
- **Color** for Gantt chart display, selected via color picker on the category add/edit page
- **General planting season(s)** for Zone 10a (start/end date ranges when this category can typically be planted)
- **Harvest type:** single harvest (e.g., onions — pick once) or continuous harvest (e.g., tomatoes, peppers — produce over time)

### Specific Varieties

Under each category are specific **plant varieties** (e.g., Everglades Tomato, Cherokee Purple Tomato). Each variety has:

- **Name**
- **Category** (foreign key)
- **Planting season override** (optional — some varieties like Everglades tomatoes tolerate Florida heat longer than the general category season)
- **Days to germination** (range: min/max)
- **Days to first harvest** (range: min/max from planting date)
- **Planting depth**
- **Spacing / size:** 1×1, 1×2, or 2×2 (how many grid squares this plant occupies)
- **Sunlight requirements**
- **Climbing / vining:** boolean indicating whether this variety is a climbing or vining plant (e.g., Pole Blue Lake = true, Bush Blue Lake = false). Used for support structure compatibility warnings.
- **Planting method:** direct sow, transplant, or both
- **Companion planting rules:** list of compatible and incompatible categories
- **Seed packet photo URL** (Cloudflare R2, optional)
- **Source URL** (link to where the seed/plant can be purchased, optional)
- **Any other fields extracted from seed packets**

### Companion Planting

Companion planting rules are stored at the **category** level (e.g., "Tomatoes are incompatible with Fennel" rather than per-variety). The system uses these rules in two ways:

1. **Proactive suggestions:** When recommending "what can I plant here," factor in what's already planted in adjacent squares and boost compatible companions.
2. **Reactive warnings:** When a user attempts to plant something incompatible with a neighbor, display a warning before confirming.

Companion planting data should be seeded from a reference data file that can be maintained and updated. This matrix will be researched and compiled from standard gardening references, tailored to the categories used in the app.

### Starter Seed Data — Categories & Varieties

The following categories and varieties should be included in the seed data. Varieties marked "(future)" are saved seeds or planned purchases — they should be in the catalog but not yet planted.

| Category | Varieties |
|---|---|
| Tomatoes | Golden Jubilee, Husky Cherry Red, Everglades (future) |
| Peppers | Jalapeño, Cubanelle, Orange Sweet, Poblano |
| Cucumbers | Garden Bush Slicer, Double Yield Pickling |
| Squash | Crookneck, Easy Pick Gold Zucchini, Summer Golden Zucchini (future), Pumpkin Spookie (future), Seminole Pumpkin (future) |
| Beans | Royal Burgundy Bush, Bush Cantare, Blue Lake Bush, Pole Blue Lake (future) |
| Sweet Potatoes | Beauregard |
| Bunching Onions | Evergreen, Red Beard, Warrior |
| Peas | Snap Patio Pride (future) |
| Lettuce | (none yet) |
| Kale | (none yet) |
| Spinach | (none yet) |
| Cabbage | Dwarf Pak Choi (future) |
| Melons | Honey Rock Cantaloupe (future) |
| Radishes | Watermelon Radish |
| Herbs | Rosemary, English Thyme, French Thyme (future), Slow-Bolt Cilantro, Bouquet Dill, Mammoth Dill (future), Italian Large Leaf Basil, Common Chives |
| Flowers | Naughty Marietta Marigold, French Red Cherry Marigold, Roselle (future) |

---

## Seed Packet Import

The user can photograph a seed packet through the PWA camera interface. The photo is sent to the Claude API, which extracts planting details: days to germination, planting depth, spacing, sunlight requirements, and any other information present on the packet.

- Extracted data auto-populates the new plant variety form for user review.
- The user can correct any fields before saving.
- **No data is written to the database without explicit user confirmation.**
- The seed packet photo is stored in Cloudflare R2 object storage; the URL is saved in Postgres alongside the plant record.
- Photos are compressed/resized client-side before upload (max 1200px wide, JPEG quality 80%) to stay within R2's free tier (10GB storage, no egress fees).

---

## Planting Model

A **planting** is a record that assigns a plant variety to a specific square (or set of squares) or tower level for a defined time period. Plantings are the core data structure that drives the Gantt chart, garden grid views, task generation, and succession planning.

### Planting Record

Each planting has:

- **Variety** (foreign key to plant variety)
- **Square(s) or tower level** (where it's planted)
- **Start date** (when the plant goes in the ground)
- **End date** (when the plant will be / was removed — always required)
- **Status:** Not Started, In Progress, or Complete
- **Planting method:** direct sow or transplant
- **Quantity** (e.g., 9 seeds, 1 transplant)
- **Removal reason** (set when status changes to Complete): harvest complete, died, pulled early, pest/disease, other

### Planting Status

- **Not Started:** The planting is planned but hasn't happened yet. The start and end dates represent the plan. The planting appears on the Gantt chart and in future-dated garden grid views.
- **In Progress:** The user has confirmed the planting is in the ground. The start date is updated to the actual planting date if it differs from the plan. The planting is now active and drives task generation.
- **Complete:** The plant has been removed. The end date is updated to the actual removal date. A removal reason is recorded.

### Status Transitions

- **Not Started → In Progress:** The user confirms planting. Start date is updated to today (or a user-specified date) if different from the planned date.
- **In Progress → Complete:** The user removes the plant via a **"Remove" button** on the square/level detail view. This action sets the end date to today, changes status to Complete, and prompts for a removal reason — all in a single interaction.
- **Not Started → (deleted):** A planned planting can be deleted entirely if plans change.

### Overlap Prevention

Plantings on the same square cannot have overlapping date ranges. If a planting's end date is extended and creates an overlap with the next planting, the next planting's start date is automatically pushed out to resolve the conflict.

### Square State (Derived)

A square's current state is derived from its plantings:

- **Fallow:** No In Progress planting on this square.
- **Planted:** Has an In Progress planting.

This is a simple two-state model. The more granular lifecycle phases (germination, growing, harvesting) are **computed for display** on the Gantt chart and are not stored as square state.

### Computed Lifecycle Phases (Display Only)

For any In Progress planting, the system computes which lifecycle phase it's in based on the start date and the variety's growth data:

1. **Germination phase:** From start date through the variety's days-to-germination range.
2. **Growing phase:** From end of germination to the variety's days-to-first-harvest range.
3. **Harvest phase:** From the harvest window opening through the end date.

These phases are used for:
- **Gantt chart visualization** — each phase rendered as a different shade/treatment of the category color
- **Task generation** — germination check-ins, harvest window alerts
- **Dashboard status** — "entering harvest window," "should be germinating"

They are calculated on the fly, not stored in the database.

---

## Planting & Grid Interaction

### Placing a Plant

To plant something, the user:

1. Selects an empty square (or squares, for multi-square plants) in a grid bed, or a level in a tower.
2. Chooses a plant variety (via the recommendation engine or manual search).
3. Records:
   - **Plant variety** (foreign key)
   - **Start date** (defaults to today, can be set to a future date for planning)
   - **End date** (required — estimated removal date)
   - **Method:** transplant or direct sow
   - **Quantity** (e.g., 9 seeds)
4. Confirms placement. The planting is created with status **Not Started** if the start date is in the future, or **In Progress** if the start date is today or in the past.

### Multi-Square Plants

Plants have a size field: 1×1, 1×2, or 2×2. When placing a plant larger than 1×1:

- The user selects the origin square.
- For 1×2 plants, the user chooses orientation (horizontal or vertical).
- The system validates that all required squares exist within the bed dimensions and are unoccupied.
- The grid UI shows the plant spanning its squares as a single visual element.

### "What Can I Plant Here?" Recommendation Engine

When the user selects one or more empty squares, the app suggests what they can plant. Suggestions are **deterministic** (no AI — driven entirely by database rules). The inputs are:

- **Current date**
- **Zone 10a planting seasons** (from category defaults or variety-specific overrides)
- **Time remaining in the season** (enough days left for germination + growth + at least some harvest)
- **Selected square count and shape** (filters to varieties whose size fits)
- **Adjacent planted squares** (companion planting compatibility — boost good neighbors, filter or flag bad ones)
- **Support structure on the square** (if a trellis is present, boost climbing/vining varieties; warn for non-climbing varieties)

Results are displayed **grouped by category** (e.g., "Tomatoes", "Eggplant"), with each category expandable to show individual varieties. This prevents overwhelming the user with dozens of varieties when the decision is first "do I want tomatoes or eggplant?"

---

## Timeline / Gantt Chart Views

The app provides Gantt-style timeline visualizations showing the lifecycle of each planting. Each planting's timeline bar shows three computed phases in distinct visual treatments:

1. **Germination** (from start date, using days-to-germination range from the variety)
2. **Growing** (from end of germination to first harvest window)
3. **Harvesting** (from first harvest window onward to end date)

For Not Started plantings, phases are projected from the planned start date. For In Progress plantings, phases are calculated from the actual start date.

### Visual Design

- Each phase uses a different shade or treatment of the **category color** (set via the color picker on the category page).
- Date ranges (germination min/max, harvest min/max) can be represented as gradients to show uncertainty.
- Different categories are visually distinguishable by their base color.
- Not Started plantings should have a distinct visual treatment (e.g., dashed borders, reduced opacity) to distinguish them from In Progress plantings.

### Scope Toggle

The user can toggle between:

- **Full year view:** See the entire growing calendar for succession planning.
- **Rolling 3-month view:** Focus on what's immediately ahead and actionable.

Default view is rolling 3-month.

### View Levels

- **Overall view:** All plantings across all containers on one timeline.
- **Per-container view:** All plantings within a single bed or tower.
- **Per-square view:** Timeline for a single square showing its planting history and current/upcoming cycles.

---

## Garden Views

### Container Detail View with Time Slider

The container detail view (for both grid beds and towers) includes a **date picker** that lets the user view the garden at any point in time:

- **Set to today:** Shows current reality — In Progress plantings in their squares, fallow squares empty.
- **Set to a future date:** Shows what the garden will look like based on planned (Not Started) and active (In Progress) plantings. Planned plantings appear in their squares with a distinct visual treatment (e.g., dashed border, lighter color).
- **Set to a past date:** Shows what the garden looked like historically based on completed plantings.

The grid displays all plantings whose date range (start to end) encompasses the selected date, regardless of status. Each square is color-coded by category color.

### Multi-Bed Overview

A single screen showing all beds and towers at a glance, each rendered as a **mini-grid** with color-coded squares showing what's planted. This provides a quick visual summary of the entire garden without drilling into individual containers. Tapping a bed navigates to its full container detail view.

### Yard Layout (Phase 2)

A spatial/map view showing where beds are physically located relative to each other in the yard. Deferred to Phase 2 due to the complexity of spatial positioning and drag-and-drop layout.

---

## Notes & Events

The app has two types of recorded information, both with timestamps:

### Structured Events

These are system-aware records tied to specific actions:

- **Planting event:** date, plant variety, method (transplant/direct sow), quantity, container, square(s)
- **Harvest event:** date, plant variety, quantity, unit of measure (lbs, count, bunches), container, square(s)

Structured events are linked to both a container/square AND a plant variety, so they appear in both contexts:
- Viewing bed 7, square A4 shows all events for that square.
- Viewing Red Bunching Warrior onions shows all events for that variety across all locations.

Harvest data supports cumulative reporting — the system can aggregate harvest totals per variety, per container, per season, or across the entire garden to help the user understand which plantings and locations are most productive.

### Free-Form Journal Notes

Observational notes not tied to a specific structured action:

- **Text content** (free-form)
- **Date**
- **Optional attachment:** can be linked to a container, a specific square, a plant variety, or any combination
- **Optional photo** (stored in R2)

The UI should allow the user to create journal notes from multiple entry points: from a container view, from a specific square/level, or from a plant variety page. The note is automatically linked to whichever context the user initiated it from, with the option to add additional links.

Examples: "Noticed yellowing leaves on bed 3 square B2," "Saw aphids on the tomatoes," "Soil in bed 1 seems compacted despite amendments."

---

## Task System

The main page displays the user's tasks for the current week.

### Task Sources

**Auto-generated tasks** are created by a server-side scheduled job (runs hourly) that evaluates planting data:

- **Harvest window alerts:** "Tomatoes in bed 2 square B3 entering harvest window" (based on computed lifecycle phase from start date + variety data)
- **Planting reminders:** "You planned to plant tomatoes in bed 3 tomorrow" (based on Not Started plantings with upcoming start dates)
- **Germination check-ins:** "Seeds planted in bed 1 square A2 should be germinating — check for sprouts"

**Manual tasks** are created by the user for anything not auto-generated (e.g., "buy compost," "repair trellis on bed 3").

**Weather-triggered tasks (Phase 2):** Frost warnings, irrigation skip suggestions based on rain forecasts.

### Task Properties

- Title / description
- Due date or date range
- Source (auto-generated vs. manual)
- Associated container/square (optional)
- Associated plant (optional)
- Status (pending, completed, dismissed)

---

## Weather Display

The main page shows a **7-day weather forecast** for the user's zip code (St. Petersburg, FL). In Phase 1, this is display-only — no integration with tasks or irrigation logic. In Phase 2, weather data feeds into task generation (frost warnings, irrigation adjustments).

Weather data should be fetched from a free weather API (e.g., Open-Meteo, which requires no API key).

---

## AI Plant Diagnostics (Phase 2)

The user can upload a photo of a plant showing symptoms (yellowing, spots, wilting, pests, etc.). The photo is sent to the Claude API along with:

- The plant variety and category (from the linked planting record)
- Florida Zone 10a growing context via RAG (common regional pests, heat stress patterns, soil issues, humidity-related diseases)
- Recent weather data (optional, Phase 2+)

The diagnosis is **contextual** — initiated from a specific plant/square in the app, and the AI response is logged as a journal note attached to that plant/square for future reference.

This is not a standalone "Plant Doctor" tab. The entry point is always from a specific planting.

---

## API Layer

The backend exposes a **REST API** consumed by the PWA frontend. The API handles all data operations, authentication, file uploads to R2, and integration with external services (Claude API, weather API).

---

## UI & Design

### General Principles

- Modern, clean interface optimized for iPhone.
- PWA: manifest file removes browser chrome, sets app icon/name. Handles iOS safe area insets (notch, home indicator). Suppresses pull-to-refresh.
- **Visual motif:** Green tendrils growing around edges of the UI.
- **Color scheme:** Garden greens as the primary palette. A style guide should be created early and referenced for all subsequent feature development.
- **No offline support in Phase 1.** The app requires network connectivity. A service worker is used for push notifications and the PWA shell, but no offline data caching.

### Key Screens

- **Main page / Dashboard:** Weekly tasks, 7-day weather forecast, quick status of active plantings.
- **Multi-bed overview:** All beds and towers as mini-grids at a glance, color-coded by what's planted. Tap to drill into detail.
- **Container detail (grid bed):** Interactive grid showing what's planted where, with date picker/time slider to view the garden at any point in time. Tap a square to view details, add a planting, log a note, or remove a plant.
- **Container detail (tower):** Level list/visual showing what's planted on each level, with the same time slider.
- **Seed catalog:** Browse categories and varieties. Add/edit with color picker for categories.
- **Gantt timeline:** Full year or rolling 3-month, filterable by container or overall. Shows computed lifecycle phases. Serves as both the planning calendar and the planting timeline.
- **"What can I plant?":** Recommendation results grouped by category, expandable to varieties.

### Frontend Framework

The frontend framework choice is left to the implementer's discretion. The PRD has no framework requirement — choose whatever best fits the PWA, mobile-first, and interactive grid/chart requirements.

---

## Infrastructure & DevOps

### Hosting

- **Server:** Beelink mini PC, Ubuntu Server (to be set up when ready for production)
- **Containerization:** All services run as Docker containers
- **Database:** Single shared Postgres instance (shared across apps on the server)
- **External access:** Custom domain (tendril.garden) + Cloudflare Tunnel (HTTPS, no static IP needed) — to be set up fresh when deploying to production
- **Object storage:** Cloudflare R2 for seed packet photos and plant diagnostic photos. Backend proxies uploads to R2 and generates pre-signed URLs for reads, keeping R2 credentials server-side.

### Database Management

- All database operations must be **repeatable** (migrations, not ad-hoc changes).
- **Seed data** must exist and be maintained. Any time the schema changes, seed data is updated to match.
- **Scripts** for resetting and reseeding the database must be easy to run, enabling local testing of migrations before pushing to production.
- There will be a **local dev environment** and a **production environment**. The same Docker Compose setup should work for both with environment-specific configuration.

### Source Control & CI/CD

- **Repository:** GitHub
- **CI/CD:** GitHub Actions for building and deploying to production
- The pipeline should build Docker images, run tests, and deploy to the Beelink server

### Testing Strategy

- **Unit tests** for the recommendation engine, companion planting logic, and planting lifecycle computations
- **Integration tests** for API endpoints
- **No E2E tests in Phase 1** (not justified for a single-user app at this stage)
- Tests run in CI before deploy

### Seed Data Should Include

- The five containers (three 4×4 beds, one 2×4 bed, one 7-level tower with 6 pockets per level)
- All plant categories and varieties listed in the Starter Seed Data table above
- Companion planting compatibility matrix (researched and compiled from standard gardening references)
- Sample irrigation configurations

---

## Notifications

Push notifications are delivered via the **Web Push API** through the PWA. No App Store submission or Apple Developer account required. (Note: iOS requires the PWA to be added to the home screen for push notifications to work.)

Notification triggers (Phase 1):
- Harvest window opening for a planting
- Planting reminders from planned (Not Started) plantings

Notification triggers (Phase 2):
- Frost warnings
- Weather-based irrigation suggestions

Notification logic is driven by a **server-side scheduled job** (runs hourly) that evaluates upcoming events and triggers push messages.

---

## Roo Code Memory Bank

Before beginning implementation, Roo Code must create a `memory-bank/` folder at the project root. See `.roo/rules/rules.md` for instructions on setting this up for the first time. The memory bank serves as Roo's persistent context across sessions — it should contain project briefs, architecture decisions, progress logs, and any context Roo needs to pick up work without re-reading the entire PRD each time.

---

## Resolved Decisions

| Decision | Resolution |
|---|---|
| Users | Single user with Google OAuth; auth built from the start |
| Auth whitelist | Environment variable for allowed Google accounts |
| Container types | Grid beds + tower from the start; extensible for future types |
| Tower representation | Levels not individual pockets; each level is a planting unit; different UI from beds; single-level plantings only |
| Support structures | Trellis, cage, or pole per square; soft warning for non-vining plants on trellis squares |
| Climbing/vining | Boolean on variety level, not category; used for support structure compatibility |
| Plant size | 1x1, 1x2, or 2x2 stored on the variety; user chooses orientation for 1x2 |
| Multi-square validation | System checks for boundary overflow and occupied square conflicts |
| Planting model | Planting record with status: Not Started / In Progress / Complete; single start and end date pair |
| Planting dates | Single start/end date fields updated as planting progresses; no separate planned vs actual dates |
| Planting removal | Remove button sets end date to today, status to Complete, and prompts for removal reason in one interaction |
| Overlap prevention | Plantings on same square cannot overlap; extending end date auto-pushes next planting start date |
| Square state | Two states only: fallow and planted; derived from In Progress plantings |
| Lifecycle phases | Germination, growing, harvesting computed for display from start date + variety data; not stored |
| Companion planting | Proactive suggestions + reactive warnings; matrix researched from standard references |
| Notes | Both structured events with planting/harvest and free-form journal notes |
| Harvest events | Include quantity + unit of measure: lbs, count, bunches; support cumulative reporting |
| Task generation | Auto from planting data + manual + weather-triggered Phase 2; scheduled job runs hourly |
| AI diagnostics | Contextual from a plant/square, diagnosis logged as a note; Phase 2 |
| Seed packet import | Phase 1; photo to Claude API to review form to confirm save; client-side compression before upload |
| Florida resources | RAG context for AI plant doctor, not a standalone wiki; Phase 2 |
| Weather | Display in Phase 1; task integration in Phase 2 |
| Gantt chart scope | Full year + rolling 3-month with toggle; default is 3-month; no separate planting calendar screen |
| Garden views | Time-slider on container detail; multi-bed overview in Phase 1; yard layout in Phase 2 |
| Irrigation | Structured data per container: type, duration, frequency incl. 2x/day |
| Harvest/grocery tracking | Not in scope |
| API style | REST API |
| Frontend framework | Implementers choice |
| Offline support | Not in Phase 1; network connectivity required |
| Photo storage | R2 with backend-proxied uploads and pre-signed read URLs; client-side compression |
| Catalog naming | Seed catalog not plant catalog |
| Source control | GitHub repo with GitHub Actions CI/CD |
| Date planted default | Defaults to today, user can modify; future dates create Not Started plantings |
| Journal note entry points | Addable from container, square/level, or plant variety views |
| Format of recommendations | Grouped by category, expandable to show individual varieties |
| Testing | Unit + integration tests; no E2E in Phase 1 |
| Domain | tendril.garden registered with Cloudflare |
| Infrastructure | Local dev first; Beelink + Cloudflare Tunnel for production later |
