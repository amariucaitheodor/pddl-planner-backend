import falcon
import json
import subprocess
from tempfile import NamedTemporaryFile

from processing.solution_processor import process_solution


class Planner(object):

    def on_post(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status

        if 'domain' not in req.media:
            resp.status = falcon.HTTP_400  # Bad request
            resp.body = {"Domain was not found in the request parameters."}
            return

        if 'problem' not in req.media:
            resp.status = falcon.HTTP_400  # Bad request
            resp.body = {"Problem was not found in the request parameters."}
            return

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
                    ["./binaries/siw-then-bfsf",
                     "--domain", domain_file.name,
                     "--problem", problem_file.name,
                     "--output", plan_file.name],
                    stderr=subprocess.STDOUT
                )
            # TODO: fix JSON creation
            except subprocess.CalledProcessError as e:
                response_dict = {'error': e.output.decode(encoding='UTF-8').replace("\\n", '  ')}
                resp.body = response_dict
                print(type(e.output.decode(encoding='UTF-8').replace("\\n", '  ')))
                return

            # Process solution
            response = json.loads(
                process_solution(
                    domain_file.name,
                    problem_file.name,
                    plan_file.name,
                    str(planner_output))
            )

            # Run validator on plan
            try:
                validator_output = subprocess.check_output(
                    ["./binaries/validate",
                     domain_file.name,
                     problem_file.name,
                     plan_file.name]
                )
            # TODO: fix JSON creation
            except subprocess.CalledProcessError as e:
                response_dict = {'error': e.output.decode(encoding='UTF-8').replace("\\n", '  ')}
                resp.body = response_dict
                return

            # Add validator result to response
            response['validator'] = str(validator_output)

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
