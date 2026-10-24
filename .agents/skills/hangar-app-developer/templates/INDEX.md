# App Templates

Read only the template relevant to the request. Each folder contains
`template.json` with its setup requirements and specific guidance, plus an
`app/` working copy with source, `hangar-app.json`, and any `data/*.json`
table definitions and example records. No credentials are bundled.

For a new local app, copy the selected `app/` folder to a new working
directory. Replace `__HANGAR_APP_NAME__`, `hangar-template-app`, and any
`https://hangar.invalid` callback URLs with the chosen app identity and URLs
returned by Hangar. Complete required setup before claiming the integration
works. The API's template-render endpoint can resolve setup-specific values.

For an existing app, use a template as a source of relevant files or patterns;
do not replace its identity, permissions, records, or entire source tree.
Sync metadata separately from source. `tables push --apply` installs definitions
only; example records are not live data and are inserted only when requested.
The CLI's `create` does not insert these table records automatically.

- [Simple frontend page](simple-frontend-page/template.json): A minimal 1-page frontend starter with no custom backend behavior.
- [Craft starter](craft-starter/template.json): A blank Hangar starter with a clean folder structure, one frontend page, and one backend health route.
- [Data dashboard](data-dashboard/template.json): A schema-agnostic dashboard that combines CSV, Google Sheets, and Datasuite API data.
- [SMART workflow runner](smart-workflow-runner/template.json): Run one deployed SMART workflow, review each task, and track execution metrics.
- [Project update email](project-update-email/template.json): Send stakeholder-ready Jira epic update emails with a snapshot of what changed since the last run.
- [SeaTalk bot](seatalk-bot/template.json): A private SeaTalk assistant you can connect, tune, and watch from one simple dashboard.
- [Integration lab](integration-lab/template.json): A private workspace for trying connected tools and seeing what each one can do.
- [Order Admin search](order-admin-search/template.json): Browse and filter Order Admin orders with target-specific Connector access.
- [Live poll](live-poll/template.json): Run a quick poll with options, vote counts, and reporting/export hooks.
- [Release verification](release-verification/template.json): Select or create a release and update canary, logs, and released Grafana screenshot proof.
- [Project Gantt](project-gantt/template.json): Plan milestones, phases, dependencies, and delivery dates with project integration hooks.
- [New employee onboarding app](new-employee-onboarding/template.json): A welcoming checklist that helps new teammates get settled, meet people, and track their progress.
- [Google Sheets aggregator](gsheet-aggregator/template.json): Pull Google Sheets rows into Hangar app data and show a chart-ready dashboard.
- [Personal dashboard](personal-dashboard/template.json): A private home base for your priorities, notes, favorite links, and daily highlights.
- [Canvas workspace](canvas/template.json): A flexible notes, links, checklist, and research board with document integration hooks.
- [Event RSVP](event-rsvp/template.json): Collect guest responses, track attendance status, and prepare calendar/sheet exports.
- [Kanban board](kanban-board/template.json): Plan work across lanes with priorities, due dates, and delivery integration hooks.
- [Ticket tracker](ticket-tracker/template.json): Manage support requests, priorities, assignees, and Jira/mail/runbook integration hooks.
