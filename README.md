## Backend Planner for PDDL (The Planning Domain Definition Language)

Lightweight implementation of [cloud PDDL planner](https://bitbucket.org/planning-researchers/cloud-solver/src/master/) by Christian Muise, Simon Vernhes and Florian Pommerening.

### [See it in action!](https://finitech-sdp.github.io/operations-monitor/#/)

### Features:
- Node.js was replaced with [Falcon](https://falconframework.org/#), a [blazing fast](https://falconframework.org/#sectionBenchmarks), minimalist Python web API framework
- Only essential planning utilities were retained
- Codebase was updated from Python 2 to Python 3
- Designed to work for specific origins only (see `Access-Control-Allow-Origin` in `planner.py`), therefore throttling was removed

### API endpoints:
- `/solve-and-validate` requires two parameters in string format, `domain` and `problem`: for example, [this domain](https://raw.githubusercontent.com/Finitech-SDP/operations-monitor/master/src/assets/planner/domain/domain.pddl) and [this problem](https://raw.githubusercontent.com/Finitech-SDP/operations-monitor/master/src/assets/planner/problem/problem.pddl).

### Acknowledgements:
- [Planner is SIW+-then-BFSf, a configuration put forward by Nir Lipovetzky, Miquel Ramirez, and Christian Muise from the LAPKT planning framework.](https://github.com/LAPKT-dev/LAPKT-public/tree/master/planners/siw_plus-then-bfs_f-ffparser)

### Contributors:
- Theodor Amariucai