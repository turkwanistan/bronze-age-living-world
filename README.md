# Bronze Age Living World

A persistent, evidence-constrained artificial society centered first on Ugarit c. 1350 BCE.

The project follows a strict boundary:

- **SQLite is canonical state.**
- **Optiplex/runtime code owns material state, time, scheduling, validation, persistence, and replay.**
- **ChatGPT is used only for bounded cognition when a consequential situation requires judgment.**
- **Character cognition receives a scoped packet, never unrestricted world state.**
- **Historical/model uncertainty, character uncertainty, and runtime randomness are separate.**
- **Culture constrains opportunities, obligations, concepts, sanctions, and institutions; it never assigns civilization-wide personality.**

Start with [`START_HERE.md`](START_HERE.md). Historical authority is [`bronze-age-simulation-encyclopedia.md`](bronze-age-simulation-encyclopedia.md); implementation authority is [`plan.md`](plan.md).

## Local development

```bash
python -m pytest
python -m bronze_world.cli init-fixture --db state/ugarit_fixture.sqlite --seed 1350
python -m bronze_world.cli advance --db state/ugarit_fixture.sqlite --days 45
python -m bronze_world.cli status --db state/ugarit_fixture.sqlite
python -m bronze_world.cli pending-jobs --db state/ugarit_fixture.sqlite
```

The fixture deliberately uses **abstract resource units** until historical calibration supports better quantities. Those choices are explicit model assumptions, not historical claims.
