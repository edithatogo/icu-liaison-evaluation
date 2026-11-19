# P7 bounded agent assignment

An implementation agent may edit only P7 registry, CLI/module/tests, docs and
P7 Conductor files. It may not edit the original P4 economic equations, replace
or fork Kairos/Dapane/Voiage numerical code, upload observed clinical data,
modify private/tenant bindings, set evidence statuses to verified without
external signed acceptance, merge other owners' PRs, or change repository CI.

Task slices P7.1.1 → P7.1.2 → P7.1.3 → P7.2.1 → ...; each task requires an
exact-path test and negative control before acceptance. One active writing lane
per source file, new namespace for any additional adapter. Keep all P7.4
external dependencies blocked until independently evidenced.
