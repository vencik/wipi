from typing import Union, Iterator, Dict
from json import dumps as jsonify
from http import HTTPStatus

from flask import Response, request as req
from flask_voluptuous import expect, Schema, Required, All

from . import app, backend


def raw_resp(content: Union[str, Iterator[str]], mime_type: str, status: int) -> Response:
    """
    Produce response
    :param content: Response content (whole response or chunk generator)
    :param mime_type: Response content type
    :param status: Response status
    :return: Response object
    """
    return Response(content, status=status, mimetype=mime_type)

def resp(content: Dict, status: int = HTTPStatus.OK, **kwargs) -> Response:
    """
    Produce an error responce
    :param content: JSON response content
    :param status: Response status
    :param kwargs: Additional keyword arguments for json.dump
    :return: Response object
    """
    return raw_resp(jsonify(content, **kwargs), "application/json", status)


@app.route("/", methods=["GET"])
@expect(Schema({}), 'args')  # no arguments expected
def _contract(args) -> Response:
    return resp({
        "errors" : {
            "description" : "Error responses have the following form",
            "response" : {
                "error" : "Error message"
            },
        },

        "requests" : [{
            "uri" : req.url_root,
            "method" : "GET",
            "description" : "API contract description",
            "response" : "{... you're looking at it now ...}",
        }, {
            "uri" : req.url_root + "get_state",
            "method" : "GET",
            "description" : "Get status of all controllers",
            "response" : {
                "controllers" : [{
                    "name" : "controller name",
                    "state" : "{... controller state dict ...}",
                }],
            },
        }, {
            "uri" : req.url_root + "get_state/<controller name>",
            "method" : "GET",
            "description" : "Get status of specified controller",
            "response" : "{... controller state dict ...}",
        }, {
            "uri" : req.url_root + "set_state",
            "method" : "POST",
            "description" : "Set/change status of some/all controllers",
            "request" : {
                "controllers" : [{
                    "name" : "controller name",
                    "state" : "{... new controller state (subset) dict ...}",
                }],
            },
            "response" : {
                "controllers" : [{
                    "name" : "controller name",
                    "state" : "{... controller state dict ...}",
                }],
            },
        }, {
            "uri" : req.url_root + "set_state/<controller name>",
            "method" : "POST",
            "description" : "Set/change status of specified controller",
            "request" : "{... new controller state (subset) dict ...}",
            "response" : "{... controller state dict ...}",
        }],
    }, indent=4, sort_keys=True)


@app.route("/get_state", methods=["GET"])
@expect(Schema({}), 'args')  # no arguments expected
def _get_states(args) -> Response:
    return resp(backend.get_state())


@app.route("/get_state/<cname>", methods=["GET"])
@expect(Schema({}), 'args')  # no arguments expected
def _get_state(cname, args) -> Response:
    state = backend.get_state(cname)
    if state is not None:
        return resp(state)

    return resp(
        {"error" : "No such controller or not enabled"}, HTTPStatus.NOT_FOUND)


# TODO: voluptuous schema check? (It'd have to be provided by the controller...)
@app.route("/set_state", methods=["POST"])
@expect(Schema({
    Required("controllers") : [{
        Required("name") : str,
        Required("state") : {
            str : All(),
        }
    }]
}))
def _set_states(json) -> Response:
    return resp(backend.set_state(state=json))


# TODO: voluptuous schema check? (It'd have to be provided by the controller...)
@app.route("/set_state/<cname>", methods=["POST"])
@expect(Schema({
    str : All(),
}))
def _set_state(cname, json) -> Response:
    state = backend.set_state(cname, json)
    if state is not None:
        return resp(state)

    return resp(
        {"error" : "No such controller or not enabled"}, HTTPStatus.NOT_FOUND)
