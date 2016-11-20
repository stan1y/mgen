/* MGEN: Client-side API access library */

(function ( $ ) {
    
    /*
     * ErrorDialog
     */
    
    var ErrorDialog = function(title, message, msgId) {
        // hide all open modals
        $('.modal.fade.in').modal('hide')
        this.msgId = msgId
        this.title = title
        this.message = message
        try {
            var err = JSON.parse(message)
            this.title = 'Error Occured: ' + err.exception
            this.message = "Reason:\n" + err.reason + "\n" +
                      "Traceback:\n" +
                      err.traceback.join("\n")
                      
        }
        catch(SyntaxError) {
            console.log("received error is not well formed exception")
        }
    }
    
    ErrorDialog.prototype.show = function() {
        $('body').prepend(
            $('<div id="' + this.msgId + '" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="' + this.msgId + '-label">' +
                '<div class="modal-dialog" role="document">' +
                    '<div class="modal-content">' +
                        '<div class="modal-header">' +
                            '<button type="button" class="close" data-dismiss="modal" aria-label="Close">' +
                                '<span aria-hidden="true">&times;</span>' +
                            '</button>' +
                            '<h4 class="modal-title" id="' + this.msgId + '-label">' + this.title + '</h4>' +
                        '</div>' +
                    '<div class="modal-body">' +
                        '<pre>' + this.message + '</pre>' +
                    '</div>' +
                    '<div class="modal-footer">' +
                        '<button id="error-dlg-dismiss" class="btn btn-default" data-dismiss="modal">Dismiss</button>' +
                    '</div>' +
                '</div>' +
            '</div>')
        )
            
        $('#' + this.msgId).modal()
        return this
    }
    
    $.fn.showErrorDialog = function(title, message, msgId) {
        return new ErrorDialog(title, message, msgId).show()
    }
    
    /*
     * DataDataQuery
     */
    
    var DataQuery = function(collectionName) {
        this.collectionName = collectionName
        this.apiPath = '/api/' + this.collectionName
        this.flt = []
        this.paging = {}
        this.data = []
    }
    
    DataQuery.prototype.filter = function(flt) {
        for (var key in flt) {
            this.flt.push({
                property: key,
                value: flt[key]
            })
        }
        return this
    }
    
    DataQuery.prototype.order_by = function() {
    
    }
    
    DataQuery.prototype.range = function() {
        
    }
    
    DataQuery.prototype.page = function (page, start, limit) {
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
    
    DataQuery.prototype.fetch = function(callback) {
        var self = this
        
        return $.ajax(this.apiPath, {
            method: "GET",
            dataType: "json",
            contentType: "application/json",
            data: {
                filter: self.flt.length > 0 ? JSON.stringify(self.flt) : undefined,
                page: self.paging.page,
                start: self.paging.start,
                limit: self.paging.limit
            },
            error: function(xhr, type, ex) {
                $().showErrorDialog(ex, xhr.responseText)
            },
            success: function(data) {
                self.total = data.total
                self.data = data[self.collectionName]
                $(self).trigger('loaded', self)
                if (callback)
                    callback.call(self, self.data)
            }
        })
    }
    
    DataQuery.prototype.one = function(callback) {
        var self = this
        return $.ajax(this.apiPath, {
            method: "GET",
            dataType: "json",
            contentType: "application/json",
            data: {
                filter: self.flt.length > 0 ? JSON.stringify(self.flt) : undefined,
                page: self.paging.page,
                start: self.paging.start,
                limit: self.paging.limit
            },
            error: function(xhr, type, ex) {
                $().showErrorDialog(ex, xhr.responseText)
            },
            success: function(data) {
                // assume single object in answer
                if (callback)
                    callback.call(self, data[self.collectionName][0])
            }
        })
    }
    
    $.fn.dataQuery = function(collectionName) {
        return new DataQuery(collectionName)
    }
    
    /*
     * ItemsContainer
     */
     
    var ItemsContainer = function(containerId, options) {
        this.options = $.extend({
            emptyMsg: 'Nothing found.',
            rowTemplate: '<div class="row"></div>',
            itemsPerRow: 3,
            defaultRenderFunc: function(item) {
                return $('<pre>' + item + '</pre>')
            }
        }, options)
        
        this.containerId = containerId
        this.cnt = $('#' + containerId)
        this.source = null
    }
    
    ItemsContainer.prototype.render = function(items, renderFunc) {
        var currentRow = $(this.options.rowTemplate),
            self = this
        
        if (!renderFunc)
            renderFunc = this.options.defaultRenderFunc
        
        this.cnt.empty()
        this.cnt.append(currentRow)
        
        $(items).each(function(idx, i) {
            if (idx % self.options.itemsPerRow == 0) {
                currentRow = $(self.options.rowTemplate)
                self.cnt.append(currentRow)
            }
            currentRow.append(renderFunc(i))
        })
        
        if (items.length == 0) {
            this.cnt.append($(
                '<div class="row"><div class="col-xs-6 col-md-4"><h3>' +
                this.options.emptyMsg +
                '</h3></div></div>'))
        }
    }
    
    ItemsContainer.prototype.setDefaultRenderFunc = function(renderFunc) {
        this.options.defaultRenderFunc = renderFunc
    }
    
    ItemsContainer.prototype.setSource = function(query) {
        this.source = query
        query.target = this
        $(this.source).on('loaded', function() {
            this.target.render(this.data)
        })
    }
    
    ItemsContainer.prototype.update = function(callback) {
        if (this.source) {
            this.source.fetch(callback)
        }
    }
    
    $.fn.itemsContainer = function(containerId, options) {
        return new ItemsContainer(containerId, options)
    }

}( jQuery ));