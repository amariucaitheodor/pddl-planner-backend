import falcon
import json
import subprocess
import logging
from tempfile import NamedTemporaryFile
from processing.solution_processor import process_solution

# get a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')

# add formatter to console handler
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


class Planner(object):

    def __init__(self):
        self.solver_additional_parameter_value = None
        self.solver_additional_parameter = None
        self.solver_path = None

        logger.debug('creating an instance of Planner')

    def on_post(self, req, resp):
        logger.info('starting reply to new request')
        resp.status = falcon.HTTP_200  # This is the default status

        if req.media is None:
            logger.debug('query parameters `domain` and `problem` are missing')
            resp.status = falcon.HTTP_400  # Bad request
            resp.body = json.dumps({'error': 'Query parameters `domain` and `problem` are missing.'})
            logger.debug('delivering error reply to request')
            return

        if 'domain' not in req.media:
            logger.debug('domain was not found in the query parameters')
            resp.status = falcon.HTTP_400  # Bad request
            resp.body = json.dumps({'error': 'Domain was not found in the query parameters.'})
            logger.debug('delivering error reply to request')
            return

        if 'problem' not in req.media:
            logger.debug('problem was not found in the query parameters')
            resp.status = falcon.HTTP_400  # Bad request
            resp.body = json.dumps({'error': 'Problem was not found in the query parameters.'})
            logger.debug('delivering error reply to request')
            return

        self.solver_additional_parameter_value = ""
        self.solver_additional_parameter = ""
        if 'solver' in req.media:
            if req.media['solver'] == "AGILE2":
                logger.info('selected solver is AGILE2')
                self.solver_path = "./solvers/agile2014/siw-then-bfsf"
            elif req.media['solver'] == "AGILE":
                logger.info('selected solver is AGILE')
                self.solver_path = "solvers/agile2018/bfws"
                self.solver_additional_parameter = "--BFWS-f5"
                self.solver_additional_parameter_value = "true"
        else:
            logger.info('no solver selected, default is AGILE')
            self.solver_path = "solvers/agile2018/bfws"
            self.solver_additional_parameter = "--BFWS-f5"
            self.solver_additional_parameter_value = "true"

        with NamedTemporaryFile("w+") as plan_file, \
                NamedTemporaryFile("w+") as domain_file, \
                NamedTemporaryFile("w+") as problem_file:

            logger.debug('writing domain')
            # bytes(req.media['domain'], "utf-8").decode("unicode_escape") took forever to figure out...
            domain_file.write(bytes(req.media['domain'], "utf-8").decode("unicode_escape"))
            domain_file.flush()
            logger.debug('finished writing domain')

            logger.debug('writing problem')
            problem_file.write(bytes(req.media['problem'], "utf-8").decode("unicode_escape"))
            problem_file.flush()
            logger.debug('finished writing problem')

            # Run planner
            try:
                logger.debug('running solver {0} with additional parameter {1} and value {2}'.format(
                    self.solver_path,
                    self.solver_additional_parameter,
                    self.solver_additional_parameter_value)
                )
                planner_output = subprocess.check_output(
                    [self.solver_path,
                     "--domain", domain_file.name,
                     "--problem", problem_file.name,
                     "--output", plan_file.name,
                     self.solver_additional_parameter, self.solver_additional_parameter_value],
                    stderr=subprocess.STDOUT
                )
                logger.debug('solver finished')
            except subprocess.CalledProcessError as e:
                logger.debug(e)
                # Maybe plan was not found etc. status should still be HTTP_200 OK
                resp.body = json.dumps({'error': e.output.decode(encoding='UTF-8').replace("\\n", '  ')})
                return

            # Process plan
            logger.debug('processing plan')
            response = json.loads(
                process_solution(
                    domain_file.name,
                    problem_file.name,
                    plan_file.name,
                    str(planner_output))
            )
            if response['parse_status'] == 'err':
                logger.debug('processing finished: parsing failed')
                # Parsing failed
                resp.body = json.dumps(
                    {
                        'error': 'Parsing failed. Please check your domain and problem for syntax errors.',
                        'parse_status': response['parse_status']
                    }
                )
                logger.debug('delivering error reply to request')
                return
            else:
                logger.debug('processing finished: parsing succeeded')

            # Run validator on plan
            try:
                logger.debug('running validator on plan {}'.format(plan_file.name))
                validator_output = subprocess.check_output(
                    ["./solvers/agile2014/validate",
                     domain_file.name,
                     problem_file.name,
                     plan_file.name]
                )
                logger.debug('finished running validator')
            except subprocess.CalledProcessError as e:
                logger.debug(e)
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
            logger.info('delivering successful reply to request')
            resp.body = json.dumps(response, sort_keys=True)


class HandleCORS(object):
    def __init__(self):
        self.allowed_origins = 'https://amariucaitheodor.github.io'

        logger.debug('creating an instance of HandleCORS with allowed origins {}'.format(self.allowed_origins))

    def process_request(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', self.allowed_origins)
        resp.set_header('Access-Control-Allow-Methods', '*')
        resp.set_header('Access-Control-Allow-Headers', '*')
        resp.set_header('Access-Control-Max-Age', 1728000)  # 20 days
        if req.method == 'OPTIONS':
            raise falcon.HTTPStatus(falcon.HTTP_200)


# falcon.API instances are callable WSGI apps
app = falcon.API(middleware=[HandleCORS()])

app.add_route('/solve-and-validate', Planner())
