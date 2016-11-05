/* MGEN: Static Website Generator
 * Client-side API access library
 */

var MGEN = {} || MGEN;


MGEN.DataStore = function(collectionName) {
    this.data = []
    this.collectionName = collectionName
    this.apiPath = '/api/' + collectionName
    
    // default page settings
    this.paging = {
        page: 1,
        start: 0,
        limit: 50
    }
    
    this.total = NaN
    
}

MGEN.DataStore.prototype.enablePaging = function (page, start, limit) {
    if (page !== undefined 
        && start !== undefined 
        && limit !== undefined) {
    
        this.paging.page = page
        this.paging.start = start
        this.paging.limit = limit
    }
    else {
        this.paging.page = 1
        this.paging.start = 0
        this.paging.limit = 50
    }
        
}

MGEN.DataStore.prototype.disablePaging = function () {
    this.paging = null
}

MGEN.displayErrorDialog = function(title, message, msgId) {
    if (msgId === undefined) {
        msgId = "error-dialog"
    }

    // hide all open modals
    $('.modal.fade.in').modal('hide')
    
    try {
        var err = JSON.parse(message)
        title = 'Error Occured: ' + err.exception
        message = "Reason:\n" + err.reason + "\n" +
                  "Traceback:\n" +
                  err.traceback.join("\n")
                  
    }
    catch(SyntaxError) {
        console.log("received error is not well formed exception")
    }
    
    
    $('body').prepend(
        $('<div id="' + msgId + '" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="' + msgId + '-label">' +
            '<div class="modal-dialog" role="document">' +
                '<div class="modal-content">' +
                    '<div class="modal-header">' +
                        '<button type="button" class="close" data-dismiss="modal" aria-label="Close">' +
                            '<span aria-hidden="true">&times;</span>' +
                        '</button>' +
                        '<h4 class="modal-title" id="' + msgId + '-label">' + title + '</h4>' +
                    '</div>' +
                '<div class="modal-body">' +
                    '<pre>' + message + '</pre>' +
                '</div>' +
                '<div class="modal-footer">' +
                    '<button id="error-dlg-dismiss" class="btn btn-default" data-dismiss="modal">Dismiss</button>' +
                '</div>' +
            '</div>' +
        '</div>')
    )
        
    $('#' + msgId).modal()
}

MGEN.DataStore.prototype.update = function(callback) {
    var self = this
    $.ajax(this.apiPath, {
        method: "GET",
        dataType: "json",
        data: this.paging,
        error: function(xhr, type, ex) {
            MGEN.displayErrorDialog(ex, xhr.responseText)
        },
        success: function(data) {
            if (data.page !== undefined 
             && data.start !== undefined 
             && data.limit !== undefined) {
                // paging is reported by server
                self.paging.page = data.page
                self.paging.start = data.start
                self.paging.limit = data.limit
            }
            else {
                self.paging = null
            }
            self.total = data.total
            self.data = data[self.collectionName]
            $(self).trigger('change', self)
            if (callback)
                callback.call(this, self.data)
        }
    })
}

MGEN.DataStore.prototype.get = function(objID, callback) {
    var self = this;
    $.ajax(this.apiPath + "/" + objID, {
        method: "GET",
        dataType: "json",
        error: function(xhr, type, ex) {
            MGEN.displayErrorDialog(ex, xhr.responseText)
        },
        success: function(data) {
            // assume single item returned
            if (data.total == 1 && callback !== undefined) {
                callback.call(this, data[self.collectionName][0])
            }
        }
    })
}


MGEN.DataStore.prototype.add = function(obj, callback) {
    var self = this;
    $.ajax(this.apiPath, {
        method: "POST",
        dataType: "json",
        data: JSON.stringify(obj),
        error: function(xhr, type, ex) {
            MGEN.displayErrorDialog(ex, xhr.responseText)
        },
        success: function(data) {
            // assume single item returned
            // pass it to caller's callback
            if (data.total == 1 && callback !== undefined) {
                callback.call(this, data[self.collectionName][0])
            }
                
        }
    })
}