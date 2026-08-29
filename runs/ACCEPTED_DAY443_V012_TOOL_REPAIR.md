# ACCEPTED DAY 443 — v012 WORKSHOP TOOL INTERRUPTION + REPAIR

Accepted strict checkpoint for `state/ugarit_living_v012.sqlite`.

## Gate

- run: `RUN-3dda7920595c1748`
- seed: `1701`
- scenario: `0.10.0`
- schema: `3`
- day: **443**
- state hash: `46bea8ae1c1614e51e3e11b7372f955af4fd5bc5a9fd4ac95da59e648c668c5b`
- events: **6,300**
- cognition: **144 accepted / 0 rejected / 0 pending**
- open scenes: **0**
- tests: **73/73**
- exact replay: **144 stored decisions / 0 new cognition / exact hash**
- negative stocks / false shortfalls / overdue scheduled obligations: **0 / 0 / 0**
- delivery-before-arrival / knowledge-before-delivery violations: **0 / 0**

## Accepted behavior

### One bounded tool/mold interruption

`ASM-FIXTURE-033` adds one fixture workshop-tool condition. The failure does not occur on a calendar date alone: it fires only when P7 is about to begin the first post-v011 master cycle that is otherwise materially viable.

On day 434 H-CRAFT has about 0.16 metal and 0.70 charcoal. Before the normal master cycle can consume them, one tool/mold failure sets `workshop_tool_condition` from 1.0 to 0.0. The metal and charcoal remain untouched, proving the failure actually blocks production rather than merely adding flavor text.

P7 chooses repair. Repair immediately consumes 0.10 finished metalwork and schedules one modeled day of downtime. On day 435 the repair completes and condition returns to 1.0. On day 441 ordinary workshop production resumes from the preserved inputs, consuming 0.15 metal + 0.20 charcoal and producing 0.08 finished metalwork. The failure count remains exactly one.

Exact failure timing, condition scale, repair input and duration are engineering calibration. The research-supported claim is only that tools/molds/finishing equipment are material craft dependencies that can interrupt production and require repair.

### Ordinary life remains independent

- P3 continues to honor the 16.5 household silver reserve at the day-434 port opportunity.
- Bat-Rapiu responds conservatively to a first minor illness on day 434 with a small household observance because H-WIDOW ritual stock is limited.
- Ahatmilku has another minor illness on day 443; the response remains proportionate rather than inventing disease progression.
- P7 still makes zero post-day-308 resource requests to P3.

## Limitations

- This is one bounded tool/mold failure, not a generic durability distribution or historical failure rate.
- Repair is performed inside the workshop; no external repair specialist is modeled.
- `workshop_tool_condition` is an engineering abstraction, not a reconstructed artifact inventory.
- Broader agricultural/weather shocks, care/property renegotiation, second-seed counterfactual validation, a second independent life-course transition, and language/scribal transaction constraints remain future work.
