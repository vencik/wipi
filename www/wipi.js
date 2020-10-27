;(function () {
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
 * List of controllers
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
 * Downstream from some controllers
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {object}   query
 * @param {Function} Response handler: function(status, data)
 */
function api_downstreams(jQuery, url, query, handler) {
    api_post(jQuery, url + "/downstream", "json", query, handler);
}


/**
 * Downstream from one controller
 *
 * @param {jQuery}   jQuery instance
 * @param {string}   API URL
 * @param {string}   Controller name
 * @param {object}   query
 * @param {Function} Response handler: function(status, data)
 */
function api_downstream(jQuery, url, name, query, handler) {
    api_post(jQuery, url + "/downstream/" + name, "json", query, handler);
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
        contract    : api_contract.bind(null, jQuery, url),
        controllers : api_controllers.bind(null, jQuery, url),
        get_states  : api_get_states.bind(null, jQuery, url),
        get_state   : api_get_state.bind(null, jQuery, url),
        set_states  : api_set_states.bind(null, jQuery, url),
        set_state   : api_set_state.bind(null, jQuery, url),
        downstreams : api_downstreams.bind(null, jQuery, url),
        downstream  : api_downstream.bind(null, jQuery, url),
    };
}

window.wipi = api;
}())
