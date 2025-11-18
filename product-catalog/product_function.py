import azure.functions as func
import logging
import json

app = func.FunctionApp()

@app.function_name(name="SimpleHello")
@app.route(route="simplehello", methods=["GET", "POST"],
           auth_level=func.AuthLevel.ANONYMOUS)
def simple_hello(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Get query parameters (for GET requests)
    name = req.params.get('name', 'World')

    # Get JSON body (for POST requests)
    try:
        req_body = req.get_json()
        name = req_body.get('name', name)
    except ValueError:
        pass

    response_message = f"Hello, {name}! This Python function executed successfully."

    return func.HttpResponse(
        response_message,
        status_code=200
    )
