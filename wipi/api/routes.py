from typing import Union, Iterator
from json import dumps as jsonify
from http import HTTPStatus

from flask import Response, request as req
from flask_voluptuous import expect, Schema, Required

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
def _contract(args):
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
