import falcon
import json
import subprocess
from tempfile import NamedTemporaryFile

from processing.solution_processor import process_solution


class Planner(object):

    def __init__(self):
        self.solver_additional_parameter_value = None
        self.solver_additional_parameter = None
        self.solver_path = None

    def on_post(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status

        if req.media is None:
            resp.status = falcon.HTTP_400  # Bad request
            resp.body = json.dumps({'error': 'Query parameters `domain` and `problem` are missing.'})
            return

        if 'domain' not in req.media:
            resp.status = falcon.HTTP_400  # Bad request
            resp.body = json.dumps({'error': 'Domain was not found in the query parameters.'})
            return

        if 'problem' not in req.media:
            resp.status = falcon.HTTP_400  # Bad request
            resp.body = json.dumps({'error': 'Problem was not found in the query parameters.'})
            return

        if 'mode' in req.media:
            if req.media['mode'] == "OPTIMAL":
                # ./fast-downward.py --plan-file "OUTPUT.txt" domain.pddl problem.pddl --search "astar(blind())"
                return
            elif req.media['mode'] == "AGILE2":
                self.solver_path = "./solvers/agile2014/siw-then-bfsf"
            elif req.media['mode'] == "AGILE":
                self.solver_path = "solvers/agile-balanced2018/bfws"
                self.solver_additional_parameter = "--BFWS-f5"
                self.solver_additional_parameter_value = "true"
            elif req.media['mode'] == "BALANCED":
                self.solver_path = "solvers/agile-balanced2018/bfws"
                self.solver_additional_parameter = "--DUAL-BFWS"
                self.solver_additional_parameter_value = "true"
        else:
            self.solver_path = "solvers/agile-balanced2018/bfws"
            self.solver_additional_parameter = "--DUAL-BFWS"
            self.solver_additional_parameter_value = "true"

        with NamedTemporaryFile("w+") as plan_file, \
                NamedTemporaryFile("w+") as domain_file, \
                NamedTemporaryFile("w+") as problem_file:

            # bytes(req.media['domain'], "utf-8").decode("unicode_escape") took forever to figure out...
            domain_file.write(bytes(req.media['domain'], "utf-8").decode("unicode_escape"))
            domain_file.flush()

            problem_file.write(bytes(req.media['problem'], "utf-8").decode("unicode_escape"))
            problem_file.flush()

            # Run planner
            try:
                planner_output = subprocess.check_output(
                    [self.solver_path,
                     "--domain", domain_file.name,
                     "--problem", problem_file.name,
                     "--output", plan_file.name,
                     self.solver_additional_parameter, self.solver_additional_parameter_value],
                    stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError as e:
                # Maybe plan was not found etc. status should still be HTTP_200 OK
                resp.body = json.dumps({'error': e.output.decode(encoding='UTF-8').replace("\\n", '  ')})
                return

            # Process solution
            response = json.loads(
                process_solution(
                    domain_file.name,
                    problem_file.name,
                    plan_file.name,
                    str(planner_output))
            )
            if response['parse_status'] == 'err':
                # Parsing failed
                resp.body = json.dumps(
                    {
                        'error': 'Parsing failed. Please check your domain and problem for syntax errors.',
                        'parse_status': response['parse_status']
                    }
                )
                return

            # Run validator on plan
            try:
                validator_output = subprocess.check_output(
                    ["./solvers/agile2014/validate",
                     domain_file.name,
                     problem_file.name,
                     plan_file.name]
                )
            except subprocess.CalledProcessError as e:
                # Maybe plan was not found etc. status should still be HTTP_200 OK
                resp.body = json.dumps({'error': e.output.decode(encoding='UTF-8').replace("\\n", '  ')})
                return

            # Add validator result to response
            response['validator'] = str(validator_output)

            # Confirm everything is ok
            response['error'] = False

            # Format response top-level strings
            for key in response.keys():
                if isinstance(response[key], str):
                    response[key] = response[key].replace('\\t', '  ').replace('\\n', '  ')

            # Deliver response
            resp.body = json.dumps(response, sort_keys=True)


class HandleCORS(object):
    def process_request(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', 'https://finitech-sdp.github.io')
        resp.set_header('Access-Control-Allow-Methods', '*')
        resp.set_header('Access-Control-Allow-Headers', '*')
        resp.set_header('Access-Control-Max-Age', 1728000)  # 20 days
        if req.method == 'OPTIONS':
            raise falcon.HTTPStatus(falcon.HTTP_200)


# falcon.API instances are callable WSGI apps
app = falcon.API(middleware=[HandleCORS()])

app.add_route('/solve-and-validate', Planner())
