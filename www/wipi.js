;(function () {
var import_oboe = document.createElement("script");
import_oboe.src = "/wipi/oboe-browser.js";
document.head.appendChild(import_oboe);

/**
 * API GET call
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {string}   Data type
 * @param {Function} Response handler: function(status, data)
 */
function api_get(jQuery, url, data_type, handler) {
    jQuery.ajax({
        url         : url,
        type        : "get",
        dataType    : data_type,
        success     : function(data, status, jqXHR) {
            handler(jqXHR.status, data);
        },
        error : function(jqXHR, status, error) {
            console.warn("API GET call failed: " + status + ":", error);
            if (data_type == "json")
                handler(jqXHR.status, jqXHR.responseJSON);
            else
                handler(jqXHR.status, jqXHR.data);
        }
    });
}


/**
 * API POST call
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {string}   Data type
 * @param {Object}   Request data (JSON)
 * @param {Function} Response handler: function(status, data)
 */
function api_post(jQuery, url, data_type, data, handler) {
    jQuery.ajax({
        url         : url,
        type        : "post",
        data        : JSON.stringify(data),
        contentType : "application/json",
        dataType    : data_type,
        success     : function(data, status, jqXHR) {
            handler(jqXHR.status, data);
        },
        error : function(jqXHR, status, error) {
            console.warn("API POST call failed " + status + ":", error);
            if (data_type == "json")
                handler(jqXHR.status, jqXHR.responseJSON);
            else
                handler(jqXHR.status, jqXHR.data);
        }
    });
}


/**
 * API downstream POST call
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {Object}   Request data (JSON)
 * @param {Function} Response chunk handler: function(node)
 * @param {Function} Response complete handler: function()
 */
function api_downstream_post(jQuery, url, data, handler, done_handler) {
    oboe({
        url     : url,
        method  : "POST",
        body    : data,
    }).node("*", handler).done(done_handler);
}


/**
 * API contract
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {Function} Response handler: function(status, data)
 */
function api_contract(jQuery, url, handler) {
    api_get(jQuery, url + '/', "json", handler);
}


/**
 * Controllers and their types
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {Function} Response handler: function(status, data)
 */
function api_controllers(jQuery, url, handler) {
    api_get(jQuery, url + "/controllers", "json", handler);
}


/**
 * Get states of all controllers
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {Function} Response handler: function(status, data)
 */
function api_get_states(jQuery, url, handler) {
    api_get(jQuery, url + "/get_state", "json", handler);
}


/**
 * Get state of one controller
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {string}   Controller name
 * @param {Function} Response handler: function(status, data)
 */
function api_get_state(jQuery, url, name, handler) {
    api_get(jQuery, url + "/get_state/" + name, "json", handler);
}


/**
 * Set states of some controllers
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {object}   states
 * @param {Function} Response handler: function(status, data)
 */
function api_set_states(jQuery, url, states, handler) {
    api_post(jQuery, url + "/set_state", "json", states, handler);
}


/**
 * Set state of one controller
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {string}   Controller name
 * @param {object}   state
 * @param {Function} Response handler: function(status, data)
 */
function api_set_state(jQuery, url, name, state, handler) {
    api_post(jQuery, url + "/set_state/" + name, "json", state, handler);
}


/**
 * Schedule setting states of some controllers
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {object}   Schedule
 * @param {Function} Response handler: function(status)
 */
function api_set_states_deferred(jQuery, url, schedule, handler) {
    api_post(jQuery, url + "/set_state_deferred", "json", schedule,
        function (status, data) { handler(status); });
}


/**
 * Schedule setting state of one controller
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {string}   Controller name
 * @param {object}   Schedule
 * @param {Function} Response handler: function(status)
 */
function api_set_state_deferred(jQuery, url, name, schedule, handler) {
    api_post(jQuery, url + "/set_state_deferred/" + name, "json", schedule,
        function (status, data) { handler(status); });
}


/**
 * List all scheduled actions
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {Function} Response handler: function(status, data)
 */
function api_list_all_deferred(jQuery, url, handler) {
    api_get(jQuery, url + "/list_deferred", "json", handler);
}


/**
 * List scheduled actions of one controller
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {string}   Controller name
 * @param {Function} Response handler: function(status, data)
 */
function api_list_deferred(jQuery, url, name, handler) {
    api_get(jQuery, url + "/list_deferred/" + name, "json", handler);
}


/**
 * Cancel all scheduled actions
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {Function} Response handler: function(status)
 */
function api_cancel_deferred(jQuery, url, handler) {
    api_get(jQuery, url + "/cancel_deferred", "json",
        function (status, data) { handler(status); });
}


/**
 * Downstream from some controllers
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {object}   query
 * @param {Function} Response handler: function(data)
 * @param {Function} Response complete handler: function()
 */
function api_downstreams(jQuery, url, query, handler, done_handler) {
    api_downstream_post(jQuery, url + "/downstream", query, handler, done_handler);
}


/**
 * Downstream from one controller
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {string}   Controller name
 * @param {object}   query
 * @param {Function} Response handler: function(status, data)
 * @param {Function} Response complete handler: function()
 */
function api_downstream(jQuery, url, name, query, handler, done_handler) {
    api_downstream_post(jQuery, url + "/downstream/" + name, query, handler, done_handler);
}


/**
 * Factory function, will return the API lib
 * Usage example:
 *
 *   var wipi = window.wipi($, "http://10.20.30.40/wipi/api)
 *   wipi.call(req, function(status, resp) {
 *       // resp is the API response
 *       if (status != 200) { return }  // handle error in a smarter way
 *       document.getElementById("resp").innerHTML = resp
 *   })
 *
 * @param  {jQuery} jQuery instance
 * @param  {string} url to running the API service
 * @return {Object} API client
 */
function api(jQuery, url) {
    return {
        contract            : api_contract.bind(null, jQuery, url),
        controllers         : api_controllers.bind(null, jQuery, url),
        get_states          : api_get_states.bind(null, jQuery, url),
        get_state           : api_get_state.bind(null, jQuery, url),
        set_states          : api_set_states.bind(null, jQuery, url),
        set_state           : api_set_state.bind(null, jQuery, url),
        set_states_deferred : api_set_states_deferred.bind(null, jQuery, url),
        set_state_deferred  : api_set_state_deferred.bind(null, jQuery, url),
        list_all_deferred   : api_list_all_deferred.bind(null, jQuery, url),
        list_deferred       : api_list_deferred.bind(null, jQuery, url),
        cancel_deferred     : api_cancel_deferred.bind(null, jQuery, url),
        downstreams         : api_downstreams.bind(null, jQuery, url),
        downstream          : api_downstream.bind(null, jQuery, url),
    };
}

window.wipi = api;
}())
