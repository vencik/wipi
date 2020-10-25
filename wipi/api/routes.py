from typing import Union, Iterator
from json import dumps as jsonify
from http import HTTPStatus

from flask import Response, request as req
from flask_voluptuous import expect, Schema, All

from . import app, backend


def resp(
    content: Union[str, Iterator[str]],
    status: int = HTTPStatus.OK,
    mime_type: str = "application/json") -> Response:
    """
    Produce response
    :param content: Response content (whole response or chunk generator)
    :param status: Response status
    :param mime_type: Response content type
    :return: Response object
    """
    return Response(content, status=status, mimetype=mime_type)


@app.route("/", methods=["GET"])
@expect(Schema({}), 'args')  # no arguments expected
def _contract(args) -> Response:
    return resp(jsonify(indent=4, sort_keys=True, obj={
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
            "response" : "You're looking at it...",
        }],
    }))


@app.route("/get_state/<cname>", methods=["GET"])
@expect(Schema({}), 'args')  # no arguments expected
def _get_state(cname, args) -> Response:
    state = backend.get_state(cname)
    if state is not None:
        return resp(jsonify(state))

    return resp(
        jsonify({"error" : "No such controller or not enabled"}),
        HTTPStatus.NOT_FOUND)


# TODO: voluptuous schema check? (It'd have to be provided by the controller...)
@app.route("/set_state/<cname>", methods=["POST"])
@expect(Schema({
    str : All(),
}))
def _set_state(cname, json) -> Response:
    state = backend.set_state(cname, json)
    if state is not None:
        return resp(jsonify(state))

    return resp(
        jsonify({"error" : "No such controller or not enabled"}),
        HTTPStatus.NOT_FOUND)
