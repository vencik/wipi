from typing import Union, Iterator, Dict
from json import dumps as jsonify
from http import HTTPStatus

from flask import Response, request as req
from flask_voluptuous import expect, Schema, Required, All, Union as Uni

from . import app, backend


def empty_resp(status: int = HTTPStatus.NO_CONTENT) -> Response:
    """
    Produce response without response body
    """
    return Response("", status=status)

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
    Produce JSON responce
    :param content: JSON response content
    :param status: Response status
    :param kwargs: Additional keyword arguments for json.dump
    :return: Response object
    """
    return raw_resp(jsonify(content, **kwargs), "application/json", status)

def chunked_resp(chunks: Iterator[str], status: int = HTTPStatus.OK) -> Response:
    """
    Produce chunked JSON response
    :param chunks: JSON response content chunks generator
    :param status: Response status
    :return: Response object
    """
    return raw_resp(chunks, "application/json", status)


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
            "uri" : req.url_root + "controllers",
            "method" : "GET",
            "description" : "Get enabled controller names and types",
            "response" : {
                "name1" : "type1",
                "name2" : "type2",
            },
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
        }, {
            "uri" : req.url_root + "set_state_deferred",
            "method" : "POST",
            "description" : "Schedule set/change status of some/all controllers",
            "request" : {
                "controllers" : [{
                    "name" : "controller name",
                    "state" : "{... new controller state (subset) dict ...}",
                }],
                "at" : "Optional time spec in form of 'YYYY/MM/DD HH:MM:SS' " +
                       "or list of these (if omitted, the action is performed ASAP)",
                "repeat" : [{
                    "times" : "Optional integer, says how many times the action " +
                              "shall be repeated after the last scheduled time " +
                              "in 'at' (if omitted, the action will repeat " +
                              "indefinitely)",
                    "interval" : "Required float, sets the repetition interval",
                }],
            },
            "response" : "None, will just respond with 204 on successful scheduling",
        }, {
            "uri" : req.url_root + "set_state_deferred/<controller name>",
            "method" : "POST",
            "description" : "Schedule set/change status of specified controller",
            "request" : {
                "state" : "{... new controller state (subset) dict ...}",
                "at" : "Optional time spec in form of 'YYYY/MM/DD HH:MM:SS' " +
                       "or list of these (if omitted, the action is performed ASAP)",
                "repeat" : [{
                    "times" : "Optional integer, says how many times the action " +
                              "shall be repeated after the last scheduled time " +
                              "in 'at' (if omitted, the action will repeat " +
                              "indefinitely)",
                    "interval" : "Required float, sets the repetition interval",
                }],
            },
            "response" : "None, will just respond with 204 on successful scheduling",
        }, {
            "uri" : req.url_root + "list_deferred",
            "method" : "GET",
            "description" : "List all scheduled status sets/changes",
            "response" : [{
                "controller" : "Controller name",
                "state" : "{... new controller state (subset) dict ...}",
                "at" : ["YYYY/MM/DD HH:MM:SS"],
            }],
        }, {
            "uri" : req.url_root + "list_deferred/<controller name>",
            "method" : "GET",
            "description" : "List controller's scheduled status sets/changes",
            "response" : [{
                "controller" : "<controller name> (as specified, may be ignored)",
                "state" : "{... new controller state (subset) dict ...}",
                "at" : ["YYYY/MM/DD HH:MM:SS"],
            }],
        }, {
            "uri" : req.url_root + "cancel_deferred",
            "method" : "GET",
            "description" : "Cancel all scheduled status sets/changes",
            "response" : "None, will just respond with 204 on successful scheduling",
        }, {
            "uri" : req.url_root + "downstream",
            "method" : "POST",
            "description" : "Stream data from controllers (using chunked-encoded " +
                            "HTML response)",
            "request" : {
                "controllers": [{
                    "name" : "controller name",
                    "query" : "{... controller streaming query ...}",
                }],
            },
            "response" : [
                "{... controllers' stream data chunks comming incrementally " +
                "(note that they'll come in an interleaved manner, as individual " +
                "controllers produce them) ...}",
            ],
        }, {
            "uri" : req.url_root + "downstream/<controller name>",
            "method" : "POST",
            "description" : "Stream data from controller (using chunked-encoded " +
                            "HTML response)",
            "request" : "{... controller streaming query ...}",
            "response" : [
                "{... controller stream data chunks comming incrementally ...}"
            ],
        }],
    }, indent=4, sort_keys=True)


@app.route("/controllers", methods=["GET"])
@expect(Schema({}), 'args')  # no arguments expected
def _controllers(args) -> Response:
    return resp(backend.controllers())


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


@app.route("/set_state_deferred", methods=["POST"])
@expect(Schema({
    Required("controllers") : [{
        Required("name") : str,
        Required("state") : {
            str : All(),
        },
    }],
    "at" : Uni(str, [str]),
    "repeat" : [{
        "times" : int,
        Required("interval") : Uni(float, int)
    }]
}))
def _set_states_deferred(json) -> Response:
    backend.set_state_deferred(state=json)
    return empty_resp()


@app.route("/set_state_deferred/<cname>", methods=["POST"])
@expect(Schema({
    Required("state") : {
        str : All(),
    },
    "at" : Uni(str, [str]),
    "repeat" : [{
        "times" : int,
        Required("interval") : Uni(float, int)
    }]
}))
def _set_state_deferred(cname, json) -> Response:
    backend.set_state_deferred(cname, json)
    return empty_resp()


@app.route("/list_deferred", methods=["GET"])
@expect(Schema({}), 'args')  # no arguments expected
def _list_all_deferred(args) -> Response:
    return resp(backend.list_deferred())


@app.route("/list_deferred/<cname>", methods=["GET"])
@expect(Schema({}), 'args')  # no arguments expected
def _list_deferred(cname, args) -> Response:
    return resp(backend.list_deferred(cname))


@app.route("/cancel_deferred", methods=["GET"])
@expect(Schema({}), 'args')  # no arguments expected
def _cancel_deferred(args) -> Response:
    backend.cancel_deferred()
    return empty_resp()


@app.route("/downstream", methods=["POST"])
@expect(Schema({
    Required("controllers") : [{
        Required("name") : str,
        Required("query") : {
            str : All(),
        }
    }]
}))
def _downstreams(json) -> Response:
    return chunked_resp(backend.downstream(query=json))


@app.route("/downstream/<cname>", methods=["POST"])
@expect(Schema({
    str : All(),
}))
def _downstream(cname, json) -> Response:
    return chunked_resp(backend.downstream(cname, json))
