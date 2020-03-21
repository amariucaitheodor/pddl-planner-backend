## Backend Planner for PDDL (The Planning Domain Definition Language)

Lightweight implementation of [cloud PDDL planner](https://bitbucket.org/planning-researchers/cloud-solver/src/master/) by Christian Muise, Simon Vernhes and Florian Pommerening.

### [See it in action!](https://finitech-sdp.github.io/operations-monitor/#/)

### Features:
- Node.js was replaced with [Falcon](https://falconframework.org/#), a [blazing fast](https://falconframework.org/#sectionBenchmarks), minimalist Python web API framework
- Only essential planning utilities were retained
- Codebase was updated from Python 2 to Python 3
- Designed to work for specific origins only (see `Access-Control-Allow-Origin` in `planner.py`), therefore throttling was removed
- Offers 2 different solvers

### API endpoints:
- `/solve-and-validate` accepts parameters `domain` (required), `problem` (required) and `solver` (optional, default is `AGILE`)

### Acknowledgements:
- `AGILE` solver is [LAPKT-BFWS-Preference](https://ipc2018-classical.bitbucket.io/planner-abstracts/teams_1_20_30_31_36_47.pdf) by Nir Lipovetzky, Miquel Ramírez, Guillem Francès, and Hector Geffner. [Project](https://github.com/nirlipo/BFWS-public) by Nir Lipovetzky and Hector Geffner.
- `AGILE2` solver is [SIW+-then-BFSf](https://github.com/LAPKT-dev/LAPKT-public/tree/master/planners/siw_plus-then-bfs_f-ffparser), as part of a configuration put forward by Nir Lipovetzky, Miquel Ramirez, and Christian Muise from the LAPKT planning framework. This configuration also includes a validator used by all solvers.

### Contributors:
- Theodor Amariucai
